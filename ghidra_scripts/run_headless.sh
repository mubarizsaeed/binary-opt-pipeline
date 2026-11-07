#!/usr/bin/env bash
# run_headless.sh: import a binary into a scratch Ghidra project, auto-analyse,
# and run ExportHotFunctions.py on it.
#
#   ghidra_scripts/run_headless.sh <binary> <addresses.txt> <out_dir>
#
# Env: GHIDRA_HOME (dir containing support/analyzeHeadless). Projects go in
# ./ghidra_projects (gitignored). Re-running on the same binary reuses the
# analysed project via -process instead of -import.
set -euo pipefail
GHIDRA_HOME="${GHIDRA_HOME:-$HOME/ghidra}"
HEADLESS="$GHIDRA_HOME/support/analyzeHeadless"
[ -x "$HEADLESS" ] || { echo "analyzeHeadless not found at $HEADLESS; set GHIDRA_HOME" >&2; exit 1; }
[ $# -eq 3 ] || { echo "usage: $0 <binary> <addresses.txt> <out_dir>" >&2; exit 2; }

BIN="$(readlink -f "$1")"; ADDRS="$(readlink -f "$2")"; OUT="$(readlink -f "$3")"
NAME="$(basename "$BIN")"
PROJ_DIR="$(pwd)/ghidra_projects"
mkdir -p "$PROJ_DIR" "$OUT"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ -f "$PROJ_DIR/$NAME.gpr" ]; then
    MODE=(-process "$NAME")
else
    MODE=(-import "$BIN")
fi
"$HEADLESS" "$PROJ_DIR" "$NAME" "${MODE[@]}" \
    -scriptPath "$SCRIPT_DIR" \
    -postScript ExportHotFunctions.py "$ADDRS" "$OUT" \
    -analysisTimeoutPerFile 600
echo "lifted output in $OUT"
