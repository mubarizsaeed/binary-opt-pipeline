# Calibration kernels

Four small C programs, one per bottleneck class the pipeline targets. They
are not the real benchmarks (those will be open-source programs with test
suites, see the open items in `docs/project_overview.md`). They exist so we
can:

1. Confirm perf on the lab server reports the hardware event we expect for
   each class before we trust it on a program we did not write.
2. Check that Ghidra recovers the hot loop in a recognisable form from a
   stripped binary (Phase B dry run).
3. Have a known-good answer for what the rewrite should look like, to
   score the agent's diagnosis against.

| Kernel | Bottleneck | Expected perf signature | Known fix |
| --- | --- | --- | --- |
| `branch_mispredict` | Data-dependent branch (filter/compaction) | branch-misses ~ N/2 | branch-free compaction or partition first |
| `pointer_chase` | Dependent loads, no prefetch | LLC misses ~ hops | software prefetch / relayout |
| `cache_aos` | 1/16 of each cache line used | high L1d misses per instr | struct-of-arrays |
| `dep_chain` | Serial dependency | IPC ~ 1 / mul latency | independent accumulators |

Every kernel prints a `checksum:` line. The rewritten binary must print the
same checksum for the same arguments; that is the correctness oracle used by
`scripts/verify.py`.

```sh
make            # build with -O2 -g -fno-omit-frame-pointer
make run        # run all four once with defaults
make strip      # stripped copies for the source-less phase
```
