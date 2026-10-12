# rea-pixi-env

A pinned, reproducible [pixi](https://pixi.prefix.dev) environment for
[REA](https://github.com/morluto/rea) (`rea-agents`) with the **Ghidra**
native-analysis provider, for static reverse engineering of Mach-O binaries on
Linux x64. No Hopper, no IDA, no global installs.

## From zero

```bash
git clone https://github.com/SilenWang/rea-pixi-env.git && cd rea-pixi-env && pixi run repro
```

That verifies and extracts Ghidra, installs REA into the env, and prints
`rea --version` (expect `6.4.0`). Then:

```bash
pixi run doctor      # rea doctor --provider ghidra
pixi run mcp-smoke   # spawn `rea mcp`, list tools, make one real tool call
```

## What is pinned

| Component | Version | Source |
|---|---|---|
| `rea-agents` | 6.4.0 (npm) | `npm install --global` inside the pixi env |
| Ghidra | 12.1.4 (`ghidra_12.1.4_PUBLIC_20260921.zip`) | GitHub release, SHA-256 verified before extraction |
| OpenJDK | 21.x (conda-forge) | Ghidra's full JDK |
| Node.js | 22.x (conda-forge) | REA 6.4.0 requires 22.19+/24.x |
| pwntools / pyelftools / unicorn | 4.15.0 / 0.33 / 2.1.2 (PyPI) | REA's ELF/DOS providers only |

Everything else is pinned by `pixi.lock`. Ghidra is not on conda-forge, so
`scripts/fetch-ghidra.sh` downloads the official zip and verifies the digest
before extracting to `.tools/`. Downloads stay out of git: `.pixi/`, `.tools/`,
`samples/` and `out/` are ignored.

## Tasks

```bash
pixi run repro                       # fetch Ghidra + install REA + print version
pixi run doctor                      # rea doctor --provider ghidra
pixi run providers                   # provider + capability matrix (JSON)
pixi run capabilities                # full MCP tool catalog (JSON)
pixi run mcp                         # run the MCP server on stdio
pixi run mcp-smoke                   # scripted MCP handshake + one real tool call
pixi run rea -- analyze <target> --provider ghidra --json
pixi run rea -- function <target> <name-or-address> --provider ghidra --json
pixi run rea -- decompile <target> <name-or-address> --provider ghidra --json
pixi run rea -- search <target> <pattern> --kind procedures --provider ghidra --json
```

`bin/with-rea-env.sh` is the single place that sets `GHIDRA_INSTALL_DIR`,
`REA_ANALYSIS_PROVIDER`, `GHIDRA_HEADLESS_MAXMEM`, the Ghidra first-query
timeout and `REA_PWNTOOLS_PYTHON`. Tune those through environment variables
rather than editing each caller.

Register the MCP server with your agent, then restart the client:

```bash
pixi run rea -- setup --client codex --dry-run   # review the plan first
pixi run rea -- setup --client codex --yes
```

## Verified on Linux x64

- `rea doctor --provider ghidra` — every check ok (Ghidra 12.1.4, 64-bit JDK 21, headless, native decompiler).
- `rea mcp doctor` — healthy: 170/170 tools, 6/6 prompts, catalog digest match.
- Mach-O arm64 end to end: `analyze`, `function`, `decompile`, `xrefs`, `search`, `trace`, `address-to-file-offset`.
- Host-independent Apple tools: `inspect-artifact`, `trace-dylib-resolution`, `project-apple-application-graph`.

The exact command lines and result JSON for each of these are in `evidence/`
(the multi-MB function dossier is gzipped). The sample binaries were public
releases — `jq` 1.7.1 macOS arm64 and `@esbuild/darwin-arm64` — and are not
committed.

## Known boundaries

**macOS-only capabilities** (they report `unsupported_host` on Linux because
they shell out to Xcode/macOS tooling): `inspect_macho`, `list_architectures`,
`inspect_signature`, `inspect_plist`, `inspect_native_dispatch_metadata`,
`demangle_swift`, `inspect_asset_catalog`, `observe_native_calls`,
`observe_native_ui`, `capture_native_ui_scenario`. To use them, run this same
environment on macOS: add `osx-arm64` to `[workspace] platforms` and re-lock.

**Target-specific providers**: `inspect-binary-layout` is ELF-only
(`pwntools-elf`) and rejects Mach-O by design; Mach-O layout inspection needs
the macOS-only `inspect_macho`.

**No Python workflow**: REA covers native binaries, JS/Electron, .NET, Android,
web, firmware and EVM bytecode. Python or script layers inside a target are
outside its scope and must be read directly.

**Scale**: a 9.8 MB Go Mach-O takes about 2 minutes for the first import and
analysis. Analyze one executable at a time instead of a whole installation
tree, and raise `GHIDRA_HEADLESS_MAXMEM` / `REA_GHIDRA_STARTUP_TIMEOUT_MS` for
large targets.

## Scope

This repository is tooling. It analyzes a supplied artifact; whether analyzing
a given artifact is permitted is the operator's call, not the environment's.
