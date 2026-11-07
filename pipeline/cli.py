"""python -m pipeline <step> ...

Steps mirror the four-step loop in docs/project_overview.md. The profile
and measure steps call perf and only work on the lab server; lift calls
Ghidra headless; diagnose and optimize bundle inputs for the agent.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

from . import hotspots, perf_parse, report


def cmd_hotspots(a):
    rep = perf_parse.parse_report(Path(a.report).read_text())
    counts = perf_parse.parse_stat_csv(Path(a.stat).read_text()) if a.stat else {}
    ann = perf_parse.parse_annotate(Path(a.annotate).read_text()) if a.annotate else []
    spots = hotspots.rank(rep, counts, ann, top_n=a.top)
    out = {"event": rep.event, "samples": rep.samples, "prior": hotspots.classify(counts),
           "hotspots": [s.__dict__ for s in spots]}
    if a.addresses:
        Path(a.addresses).write_text("\n".join(f"0x{x:x}" for s in spots for x in s.hot_addresses) + "\n")
    print(json.dumps(out, indent=2))


def cmd_lift(a):
    sh = Path(__file__).resolve().parent.parent / "ghidra_scripts" / "run_headless.sh"
    sys.exit(subprocess.call([str(sh), a.binary, a.addresses, a.out]))


def cmd_bundle(a):
    """Collect everything the agent needs for diagnose/optimize into one dir."""
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    parts = []
    for p in [a.hotspots, *a.lifted]:
        p = Path(p)
        if p.is_dir():
            for f in sorted(p.glob("*")):
                parts.append(f"### {f.name}\n```\n{f.read_text()}\n```\n")
        else:
            parts.append(f"### {p.name}\n```\n{p.read_text()}\n```\n")
    (out / "bundle.md").write_text(
        "# Diagnose/optimize input bundle\n\n"
        "Read the perf summary, then the decompiled hot function(s). Name the bottleneck "
        "with evidence, propose a rewrite, and keep the output contract identical.\n\n"
        + "\n".join(parts))
    print(f"wrote {out / 'bundle.md'}")


def cmd_results(a):
    rows = report.load(Path(a.results))
    print(report.to_markdown(rows))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="pipeline")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("hotspots", help="rank hot functions from perf report/stat/annotate text")
    p.add_argument("--report", required=True)
    p.add_argument("--stat")
    p.add_argument("--annotate")
    p.add_argument("--top", type=int, default=5)
    p.add_argument("--addresses", help="write hot instruction addresses here for the lift step")
    p.set_defaults(fn=cmd_hotspots)

    p = sub.add_parser("lift", help="decompile hot functions with Ghidra headless")
    p.add_argument("binary"); p.add_argument("addresses"); p.add_argument("out")
    p.set_defaults(fn=cmd_lift)

    p = sub.add_parser("bundle", help="gather hotspot JSON + lifted code for the agent")
    p.add_argument("--hotspots", required=True)
    p.add_argument("--lifted", nargs="+", required=True)
    p.add_argument("--out", required=True)
    p.set_defaults(fn=cmd_bundle)

    p = sub.add_parser("results", help="print the results table as markdown")
    p.add_argument("--results", default="results/results.json")
    p.set_defaults(fn=cmd_results)

    a = ap.parse_args(argv)
    a.fn(a)


if __name__ == "__main__":
    main()
