"""Render the results table. Rows come from results/results.json, which is
appended to by `pipeline measure` once a rewrite has passed verification."""
import json
from pathlib import Path
from typing import List

COLUMNS = ["benchmark", "bottleneck", "phase", "speedup", "correct", "iterations", "notes"]


def load(path: Path) -> List[dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text())


def to_markdown(rows: List[dict]) -> str:
    if not rows:
        return "_No measured results yet._\n"
    head = "| " + " | ".join(COLUMNS) + " |\n|" + "---|" * len(COLUMNS) + "\n"
    body = ""
    for r in rows:
        cells = []
        for c in COLUMNS:
            v = r.get(c, "")
            if c == "speedup" and isinstance(v, (int, float)):
                v = f"{v:.2f}x"
            if c == "correct" and isinstance(v, bool):
                v = "yes" if v else "no"
            cells.append(str(v))
        body += "| " + " | ".join(cells) + " |\n"
    return head + body
