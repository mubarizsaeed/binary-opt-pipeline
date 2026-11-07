#!/usr/bin/env python3
"""Reduce repeated `perf stat -x,` output to per-event medians.

    python3 scripts/medians.py results/raw/foo.perfstat.csv [--json]

Reports medians, not means: a single interrupted run should not move the
number. Also derives IPC and miss rates where the inputs are present.
"""
import json
import statistics
import sys


def parse(path):
    reps, cur = [], {}
    for line in open(path):
        line = line.strip()
        if line.startswith("# rep"):
            if cur:
                reps.append(cur)
            cur = {}
            continue
        if not line or line.startswith("#"):
            continue
        parts = line.split(",")
        if len(parts) < 3 or parts[0] in ("<not supported>", "<not counted>"):
            continue
        try:
            cur[parts[2]] = float(parts[0])
        except ValueError:
            pass
    if cur:
        reps.append(cur)
    return reps


def medians(reps):
    events = sorted({k for r in reps for k in r})
    med = {e: statistics.median([r[e] for r in reps if e in r]) for e in events}
    if "cycles" in med and "instructions" in med and med["cycles"]:
        med["ipc"] = med["instructions"] / med["cycles"]
    if "branches" in med and "branch-misses" in med and med["branches"]:
        med["branch_miss_rate"] = med["branch-misses"] / med["branches"]
    if "cache-references" in med and "cache-misses" in med and med["cache-references"]:
        med["cache_miss_rate"] = med["cache-misses"] / med["cache-references"]
    if "instructions" in med and "LLC-load-misses" in med and med["instructions"]:
        med["llc_misses_per_kinst"] = 1000.0 * med["LLC-load-misses"] / med["instructions"]
    return med


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    reps = parse(sys.argv[1])
    med = medians(reps)
    if "--json" in sys.argv:
        print(json.dumps({"reps": len(reps), "median": med}, indent=2))
        return
    print(f"{len(reps)} reps, medians:")
    for k, v in med.items():
        print(f"  {k:24s} {v:,.4f}" if v < 1000 else f"  {k:24s} {v:,.0f}")


if __name__ == "__main__":
    main()
