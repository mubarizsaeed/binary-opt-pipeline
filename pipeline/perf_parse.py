"""Parsers for perf text output. Pure functions, no perf required, so they
are testable on any machine (see tests/test_perf_parse.py)."""
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# e.g. "    61.23%  branch_mispredict  branch_mispredict  [.] sum_above"
_REPORT_LINE = re.compile(
    r"^\s*(?P<pct>\d+\.\d+)%\s+"
    r"(?:(?P<comm>\S+)\s+)?"
    r"(?:(?P<dso>\S+)\s+)?"
    r"\[(?P<kind>[.kH])\]\s+"
    r"(?P<symbol>.+?)\s*$"
)

# e.g. "  0.00 :   401156:  cmp  $0x7fffffff,%eax"  (perf annotate --stdio)
_ANNOTATE_LINE = re.compile(
    r"^\s*(?P<pct>\d+\.\d+)\s*:\s*(?P<addr>[0-9a-fA-F]+):\s*(?P<insn>.+?)\s*$"
)


@dataclass
class Symbol:
    symbol: str
    percent: float
    dso: Optional[str] = None
    kind: str = "."          # '.' user, 'k' kernel

    @property
    def is_user(self) -> bool:
        return self.kind == "."


@dataclass
class AnnotatedInsn:
    address: int
    percent: float
    insn: str


@dataclass
class Report:
    event: Optional[str] = None
    samples: Optional[int] = None
    symbols: List[Symbol] = field(default_factory=list)


def parse_report(text: str) -> Report:
    """Parse `perf report --stdio --no-children --sort symbol,dso` output."""
    rep = Report()
    for line in text.splitlines():
        if line.startswith("#"):
            m = re.search(r"Samples:\s*([\d.]+)([KM]?)\s+of event '([^']+)'", line)
            if m:
                n = float(m.group(1)) * {"": 1, "K": 1e3, "M": 1e6}[m.group(2)]
                rep.samples = int(n)
                rep.event = m.group(3)
            continue
        m = _REPORT_LINE.match(line)
        if m:
            rep.symbols.append(Symbol(
                symbol=m.group("symbol").strip(),
                percent=float(m.group("pct")),
                dso=m.group("dso"),
                kind=m.group("kind"),
            ))
    return rep


def parse_annotate(text: str) -> List[AnnotatedInsn]:
    """Parse `perf annotate --stdio` into per-instruction sample shares."""
    out = []
    for line in text.splitlines():
        m = _ANNOTATE_LINE.match(line)
        if m:
            out.append(AnnotatedInsn(
                address=int(m.group("addr"), 16),
                percent=float(m.group("pct")),
                insn=m.group("insn"),
            ))
    return out


def parse_stat_csv(text: str) -> Dict[str, float]:
    """Parse one `perf stat -x,` block into {event: count}."""
    counts: Dict[str, float] = {}
    for line in text.splitlines():
        parts = line.strip().split(",")
        if len(parts) < 3 or not parts[0] or parts[0].startswith("<") or parts[0].startswith("#"):
            continue
        try:
            counts[parts[2]] = float(parts[0])
        except ValueError:
            continue
    return counts
