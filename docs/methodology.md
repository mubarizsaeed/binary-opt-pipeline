# Measurement methodology

Prof. Sendag's rule for this project: no simulators, no ChampSim, no SPEC.
Real binaries, real hardware, real numbers. That only means something if the
numbers are repeatable, so these are the rules every measurement follows.

## Machine

All numbers come from the URI lab server. Record `lscpu`, kernel version,
and `perf version` in `results/machine.txt` the first time and re-check it
before every session. Turbo/frequency scaling state is part of the machine
description; if it changes, old numbers are not comparable.

## Builds

- Same compiler, same version, same flags for the original and the rewrite.
  Default: `gcc -O2 -g -fno-omit-frame-pointer` (see `benchmarks/Makefile`).
- `-g` and frame pointers do not change the generated hot-loop code at -O2
  in the cases we care about, but check `objdump -d` for the hot function
  with and without once, and note it.
- For Phase B, the stripped binary is measured, not the one with symbols.
  perf reports addresses; the pipeline maps them to Ghidra function names.

## Runs

- Pin to one core with `taskset -c $CORE`. Pick a core with nothing else
  scheduled on it; avoid core 0.
- 7 repetitions minimum. Report the **median**. Also keep min and max in
  the raw CSV so an outlier is visible.
- Run the original and the rewrite back to back in the same session.
- Inputs are fixed per benchmark and written down in
  `tests/fixtures/<benchmark>_inputs.txt`. Speedup is reported per input.

## Events

`perf stat -e cycles,instructions,branches,branch-misses,cache-references,cache-misses,L1-dcache-load-misses,LLC-load-misses`

Derived: IPC, branch miss rate, LLC misses per thousand instructions. These
are what `scripts/medians.py` and `pipeline/hotspots.py` compute. For
localisation, `perf record -e <event> -g` with the event that stood out,
then `perf annotate` on the top symbol.

## Correctness before speed

A speedup is not recorded until `scripts/verify.py` passes on the full
input set. For the calibration kernels the contract is the `checksum:` line.
For real benchmarks the oracle is decided per benchmark before any rewrite
is attempted (test suite, output diff, or hash of output files) and written
in that benchmark's README.

## What gets reported

Per (benchmark, bottleneck class, phase): median speedup, whether the
rewrite was correct, how many agent iterations it took, and a short note on
what the agent changed. A failed or negative result is recorded the same
way as a positive one.
