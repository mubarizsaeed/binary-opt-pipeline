"""Rank hot spots and attach a first-guess bottleneck class from counters.

The classification here is deliberately crude: it is the prior the agent
starts from, not the diagnosis. The diagnosis step reads the decompiled code.
"""
from dataclasses import dataclass, field
from typing import Dict, List

from .perf_parse import AnnotatedInsn, Report, Symbol


@dataclass
class HotSpot:
    symbol: str
    percent: float
    dso: str
    hot_addresses: List[int] = field(default_factory=list)   # top sampled instruction addresses
    prior: str = "unknown"
    evidence: Dict[str, float] = field(default_factory=dict)


def classify(counts: Dict[str, float]) -> str:
    """Map whole-program counters to the most likely bottleneck class."""
    ev: Dict[str, float] = {}
    cyc = counts.get("cycles", 0.0)
    ins = counts.get("instructions", 0.0)
    if cyc and ins:
        ev["ipc"] = ins / cyc
    if counts.get("branches"):
        ev["branch_miss_rate"] = counts.get("branch-misses", 0.0) / counts["branches"]
    if ins:
        ev["llc_misses_per_kinst"] = 1000.0 * counts.get("LLC-load-misses", 0.0) / ins
        ev["l1d_misses_per_kinst"] = 1000.0 * counts.get("L1-dcache-load-misses", 0.0) / ins

    # Thresholds are starting points; tune after the first lab-server runs.
    if ev.get("branch_miss_rate", 0.0) > 0.05:
        return "branch"
    if ev.get("llc_misses_per_kinst", 0.0) > 5.0:
        return "memory-latency"
    if ev.get("l1d_misses_per_kinst", 0.0) > 30.0:
        return "cache-bandwidth"
    if ev.get("ipc", 9.0) < 1.0:
        return "dependency-chain"
    return "none-obvious"


def rank(report: Report, counts: Dict[str, float], annotate: List[AnnotatedInsn] = (),
         top_n: int = 5, user_only: bool = True) -> List[HotSpot]:
    prior = classify(counts)
    spots: List[HotSpot] = []
    for s in report.symbols:
        if user_only and not s.is_user:
            continue
        spots.append(HotSpot(symbol=s.symbol, percent=s.percent, dso=s.dso or "?", prior=prior))
        if len(spots) >= top_n:
            break
    # The annotate output belongs to the top symbol only (record_hot.sh).
    if spots and annotate:
        top = sorted(annotate, key=lambda a: a.percent, reverse=True)[:8]
        spots[0].hot_addresses = [a.address for a in top if a.percent > 0.0]
    return spots
