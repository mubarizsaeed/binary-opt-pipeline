#!/usr/bin/env bash
# profile.sh: measure one binary with perf stat, pinned to a core, repeated.
#
#   scripts/profile.sh <binary> [args...]
#
# Env:
#   CORE=3        core to pin to (default 3; pick an isolated one on the lab box)
#   REPS=7        repetitions; medians are taken by scripts/medians.py
#   OUT=results/raw   where the perf stat CSV lines go
#
# Produces $OUT/<name>.<timestamp>.perfstat.csv (perf -x, one event per line)
# and prints the median summary.
set -euo pipefail

CORE="${CORE:-3}"
REPS="${REPS:-7}"
OUT="${OUT:-results/raw}"
EVENTS="cycles,instructions,branches,branch-misses,cache-references,cache-misses,L1-dcache-load-misses,LLC-load-misses"

if [ $# -lt 1 ]; then echo "usage: $0 <binary> [args...]" >&2; exit 2; fi
BIN="$1"; shift
NAME="$(basename "$BIN")"
STAMP="$(date +%Y%m%d-%H%M%S)"
mkdir -p "$OUT"
CSV="$OUT/$NAME.$STAMP.perfstat.csv"

command -v perf >/dev/null || { echo "perf not found; run this on the lab server" >&2; exit 1; }

echo "# binary=$BIN args=$* core=$CORE reps=$REPS" | tee "$CSV"
for i in $(seq 1 "$REPS"); do
    echo "# rep $i" >> "$CSV"
    taskset -c "$CORE" perf stat -x, -e "$EVENTS" -o /dev/stdout -- "$BIN" "$@" 2>/dev/null \
        | grep -v '^#' | grep -v '^$' >> "$CSV"
done

python3 "$(dirname "$0")/medians.py" "$CSV"
