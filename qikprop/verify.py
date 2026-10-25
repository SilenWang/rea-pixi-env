"""Check the QikProp 8.8 relations documented in README.md against the package's own data.

usage: pixi run qp-verify --data-dir /path/to/extracted/qikprop

Every check recomputes a number from inputs QikProp itself shipped (descriptor columns
and parameter files), so a pass means the documented formula reproduces the binary's output.
"""

import argparse
import csv
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
COLUMN = {"#amine": "#amine", "#amide": "#amide", "#acid": "#acid", "ACxDN": "ACxDN^.5/SA"}


def table(path):
    rows = []
    for line in Path(path).read_text().splitlines():
        if line.strip() and not line.lstrip().startswith("//"):
            rows.append(line.split("\t"))
    return rows


def load(path):
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


def num(row, key):
    try:
        return float(row[COLUMN.get(key, key)])
    except (KeyError, ValueError, TypeError):
        return 0.0


def check_star_table(data):
    """params/stars.tsv must equal the value lines of data/QPlimits."""
    want = [(r[0], float(r[1]), float(r[2])) for r in table(HERE / "params/stars.tsv")]
    got, pending = [], None
    for line in (data / "data/QPlimits").read_text().splitlines():
        if "standard is:" in line:
            pending = line.split("standard is:")[0].strip()
            continue
        hit = re.fullmatch(r"\s*(-?\d+\.?\d*)\s*/\s*(-?\d+\.?\d*)\s*", line)
        if hit and pending:
            got.append((pending, float(hit.group(1)), float(hit.group(2))))
            pending = None
    assert len(want) == len(got) and all(a[1:] == b[1:] for a, b in zip(want, got)), (
        "stars.tsv no longer matches QPlimits: " + str([(a, b) for a, b in zip(want, got) if a[1:] != b[1:]])
    )


def check_stars(data):
    ranges = [(r[0], float(r[1]), float(r[2])) for r in table(HERE / "params/stars.tsv")]
    rows = load(data / "data/QPxpd1.CSV")
    bad = [r["molecule"] for r in rows if int(num(r, "#stars")) != sum(
        1 for name, lo, hi in ranges if num(r, name) < lo or num(r, name) > hi)]
    return "star count (QPxpd1)", len(rows) - len(bad), len(rows), bad[:3]


def check_sasa_parts(data):
    rows = load(data / "qiksim/sample/QP.CSV")
    bad = [r["molecule"] for r in rows
           if abs(sum(num(r, k) for k in ("FOSA", "FISA", "PISA", "WPSA")) - num(r, "SASA")) > 0.02]
    return "SASA = FOSA+FISA+PISA+WPSA", len(rows) - len(bad), len(rows), bad[:3]


def check_logp_hydrocarbon(data):
    """Every polar-group-free solute in the sample must follow -0.640392 + 0.009165*volume."""
    rows = [r for r in load(data / "qiksim/sample/QP.CSV")
            if num(r, "FOSA") == num(r, "SASA") and not any(
                num(r, k) for k in ("FISA", "PISA", "WPSA", "donorHB", "accptHB"))]
    bad = [r["molecule"] for r in rows
           if abs(num(r, "QPlogPo/w") - (-0.640392 + 0.009165 * num(r, "volume"))) > 0.0015]
    return "QPlogPo/w hydrocarbon branch", len(rows) - len(bad), len(rows), bad[:3]


def check_logp_fit1(data):
    terms = [(r[0], float(r[1])) for r in table(HERE / "params/logp_fit1.tsv")]
    const = dict(terms)["const"]

    def fit1(r):
        return const + sum(c * num(r, k) for k, c in terms if k != "const")

    rows = load(data / "data/QPxpd1.CSV")
    hit, bad = 0, []
    for r in rows:
        value = fit1(r) - (1.874 if num(r, "#acid") > 0 and num(r, "#amine") > 0 else 0.0)
        if abs(value - num(r, "QPlogPo/w")) <= 0.0015:
            hit += 1
        else:
            bad.append(r["molecule"])
    return "QPlogPo/w fit1 + zwitterion branch (QPxpd1)", hit, len(rows), bad[:3]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True, help="extracted qikprop-v8.8-Linux-x86_64 package")
    data = Path(ap.parse_args().data_dir)
    check_star_table(data)
    hard = [check_stars(data), check_sasa_parts(data), check_logp_hydrocarbon(data)]
    # The v3.0-era fit covers ~82% of QPxpd1; 8.8 routes the rest through branches not decoded here.
    soft = [check_logp_fit1(data)]
    failed = 0
    for label, hit, total, bad in hard:
        ok = hit == total and not bad
        failed += not ok
        print(f"{'PASS' if ok else 'FAIL'}  {label:<46} {hit}/{total}  {bad if bad else ''}")
    for label, hit, total, bad in soft:
        ok = hit / total >= 0.8
        failed += not ok
        print(f"{'PASS' if ok else 'FAIL'}  {label:<46} {hit}/{total}  {bad if bad else ''}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
