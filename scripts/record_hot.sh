#!/usr/bin/env bash
# record_hot.sh: find where the time goes in one binary.
#
#   scripts/record_hot.sh <binary> [args...]
#
# Writes $OUT/<name>.perf.data, <name>.report.txt (perf report --stdio, by
# symbol) and <name>.annotate.txt (per-instruction samples for the top
# symbol). The report file is what pipeline/perf_parse.py reads.
set -euo pipefail

CORE="${CORE:-3}"
OUT="${OUT:-results/raw}"
EVENT="${EVENT:-cycles}"      # try branch-misses or LLC-load-misses to localise a specific event
FREQ="${FREQ:-5000}"

if [ $# -lt 1 ]; then echo "usage: $0 <binary> [args...]" >&2; exit 2; fi
BIN="$1"; shift
NAME="$(basename "$BIN")"
mkdir -p "$OUT"
DATA="$OUT/$NAME.$EVENT.perf.data"

command -v perf >/dev/null || { echo "perf not found; run this on the lab server" >&2; exit 1; }

taskset -c "$CORE" perf record -e "$EVENT" -F "$FREQ" -g -o "$DATA" -- "$BIN" "$@"
perf report -i "$DATA" --stdio --no-children --sort symbol,dso --percent-limit 0.5 > "$OUT/$NAME.$EVENT.report.txt"
TOP="$(perf report -i "$DATA" --stdio --no-children --sort symbol 2>/dev/null \
      | grep -E '^\s+[0-9.]+%' | head -1 | awk '{print $NF}')"
if [ -n "$TOP" ]; then
    perf annotate -i "$DATA" --stdio -s "$TOP" > "$OUT/$NAME.$EVENT.annotate.txt" 2>/dev/null || true
fi
echo "report: $OUT/$NAME.$EVENT.report.txt"
echo "top symbol: ${TOP:-?}"
