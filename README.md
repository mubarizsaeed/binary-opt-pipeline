# binary-opt-pipeline

**Working backwards from the binary.** An agentic pipeline that takes a
compiled Linux binary with no source, finds why it is slow using hardware
counters, decompiles the hot code, has an AI rewrite it, recompiles, and
measures the real speedup on real hardware.

The research question is not "can an AI make it faster." It is: **for which
kinds of bottlenecks does this work, how much speedup is realistic, and how
often does the rewrite silently change behaviour?** A measured negative
result counts.

Course project for ELE 548 Computer Architecture at the University of Rhode
Island (Fall 2026), with Jake Nicynski. See
[`docs/project_overview.md`](docs/project_overview.md) for the full plan.

## Status

| Milestone | Date | State |
| --- | --- | --- |
| Proposal | Oct 22 | accepted |
| Pipeline design, calibration kernels, perf + Ghidra tooling | Nov | **in progress (this repo)** |
| Progress report with first measured results | Dec 3 | upcoming |
| Final talk / final report | Dec 17 / Dec 21 | upcoming |

No speedups are claimed yet. `results/` stays empty until a rewrite has
passed the correctness oracle and been measured on the lab server.

## The loop

```
         perf stat / perf record            Ghidra (headless or via REA MCP)
 binary ───────────────────────► hot spots ─────────────────────────────► pseudocode + asm
   ▲                                                                            │
   │ recompile, same flags                                                      │ agent reads
   │                                                                            ▼
 rewrite ◄──────────────────────── diagnosis ◄──────────────────────── perf events per line
   │
   └──► scripts/verify.py (same output?) ──► scripts/profile.sh (median of 7, pinned core) ──► results/
```

1. **Profile**: `scripts/record_hot.sh` and `scripts/profile.sh` wrap perf with
   core pinning and repeats; `python -m pipeline hotspots` parses the text
   output, ranks functions, and attaches a bottleneck prior from the counters.
2. **Lift**: `ghidra_scripts/run_headless.sh` decompiles the functions that
   contain the hot addresses and exports pseudocode, disassembly, and an
   address-to-function index.
3. **Diagnose**: `python -m pipeline bundle` packages the perf summary and
   lifted code for the agent, which names the cause with evidence.
4. **Optimize and measure**: the agent rewrites the hot spot, we recompile with
   identical flags, `verify.py` must pass, then `profile.sh` measures.

## Calibration kernels

Before trusting the pipeline on code we did not write, four small C programs
in [`benchmarks/`](benchmarks/) each isolate one bottleneck class with a
known fix. They are the unit tests for the method.

| Kernel | Bottleneck | Known fix |
| --- | --- | --- |
| `branch_mispredict` | unpredictable data-dependent branch in a filter loop | branch-free compaction |
| `pointer_chase` | dependent loads the prefetcher cannot follow | software prefetch / relayout |
| `cache_aos` | 1/16 of each cache line used | struct-of-arrays |
| `dep_chain` | serial dependency chain | independent accumulators |

```sh
make -C benchmarks          # gcc -O2 -g -fno-omit-frame-pointer
make -C benchmarks strip    # stripped copies for the source-less phase
python3 -m unittest discover -s tests
```

## Repository layout

```
benchmarks/       calibration kernels + Makefile with fixed flags
scripts/          perf wrappers (profile.sh, record_hot.sh), medians.py, verify.py
ghidra_scripts/   headless Ghidra driver and ExportHotFunctions.py
pipeline/         Python package: perf parsing, hot-spot ranking, agent bundle, results table
tests/            unit tests with real perf output as fixtures
docs/             project overview, measurement methodology, Ghidra workflow
results/          measured results (empty until Dec 3)
```

## Tools

Linux perf, Ghidra, [REA](https://github.com/rea-dev/rea) as the MCP layer that
lets a coding agent drive Ghidra, objdump as a cross-check, GCC for
recompilation. Everything runs on a Linux server; `perf` is not available
under WSL2, so profiling scripts are lab-server only.

## Roadmap

- [x] Calibration kernels with a checksum contract
- [x] perf wrappers with pinning, repeats, medians
- [x] perf text parsers + counter-based bottleneck prior, with tests
- [x] Ghidra headless export of hot functions
- [x] Correctness oracle script
- [ ] First lab-server run: confirm each kernel shows its expected event signature
- [ ] REA/MCP connection so the agent can query Ghidra interactively
- [ ] Phase A on the kernels: agent diagnosis + rewrite, scored against the known fix
- [ ] Choose two or three open-source benchmarks with test suites
- [ ] Phase B: same loop on stripped binaries
- [ ] Results table and write-up

## License

MIT.
