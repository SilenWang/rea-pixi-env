#!/usr/bin/env python3
"""Minimal MCP stdio smoke test: spawn `rea mcp`, list tools, call one.

Proves the MCP server is actually reachable/callable without restarting an
agent client. Prints a JSON summary. Exits non-zero on protocol failure.
"""
import json
import os
import subprocess
import sys
import threading

TOOL = os.environ.get("SMOKE_TOOL", "")
CALL_ARGS = json.loads(os.environ.get("SMOKE_ARGS", "{}"))


def send(p, msg):
    p.stdin.write((json.dumps(msg) + "\n").encode())
    p.stdin.flush()


def read_one(p, timeout=600):
    """Read one newline-delimited JSON-RPC message from stdout."""
    box = {}

    def _worker():
        try:
            while True:
                line = p.stdout.readline()
                if not line:
                    box["err"] = "server closed stdout"
                    return
                line = line.strip()
                if not line:
                    continue
                box["msg"] = json.loads(line)
                return
        except Exception as exc:  # noqa: BLE001
            box["err"] = repr(exc)

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    t.join(timeout)
    if "msg" not in box:
        raise TimeoutError(box.get("err", f"no message within {timeout}s"))
    return box["msg"]


def rpc(p, msg, timeout=600):
    send(p, msg)
    while True:
        resp = read_one(p, timeout)
        if resp.get("id") == msg.get("id"):
            return resp


def main():
    proc = subprocess.Popen(
        ["rea", "mcp"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    out = {"initialize": None, "tool_count": 0, "tools": [], "tool_call": None}
    try:
        init = rpc(
            proc,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "rea-mcp-smoke", "version": "0.1.0"},
                },
            },
        )
        out["initialize"] = init.get("result", {}).get("serverInfo", init)
        send(proc, {"jsonrpc": "2.0", "method": "notifications/initialized"})
        listing = rpc(proc, {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        tools = listing.get("result", {}).get("tools", [])
        out["tool_count"] = len(tools)
        out["tools"] = sorted(t["name"] for t in tools)
        if TOOL:
            call = rpc(
                proc,
                {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {"name": TOOL, "arguments": CALL_ARGS},
                },
            )
            result = call.get("result", call.get("error"))
            text = json.dumps(result)[:4000]
            out["tool_call"] = {"tool": TOOL, "ok": "error" not in call, "preview": text}
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()
        out["stderr_tail"] = proc.stderr.read().decode(errors="replace")[-800:]

    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0 if out["initialize"] and out["tool_count"] else 1


if __name__ == "__main__":
    sys.exit(main())
