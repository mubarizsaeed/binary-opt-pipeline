# Project overview

Working title: *Working Backwards from the Binary*
Course: ELE 548 Computer Architecture, University of Rhode Island
Team: Mubariz Saeed (agent and pipeline side), Jake Nicynski (hardware and measurement side)
Timeline: proposal accepted Oct 22, 2026; progress report and talk Dec 3; final talk Dec 17; final report Dec 21

## The one-paragraph version

An agentic pipeline takes a compiled Linux binary, finds where it is slow,
decompiles the slow parts, has an AI rewrite them, recompiles, and measures
the speedup on real hardware. The point is not just whether the AI makes it
faster. The point is to quantify where this works and where it breaks: which
kinds of bottlenecks an AI can fix from decompiled code alone, how much
speedup is realistic, and how often the rewrite changes program behaviour.
Phase A uses open-source programs we build from source, so the AI's output
can be checked against the truth. Phase B moves to binaries with no source
and measures how much of that still holds.

## Why this is a computer architecture project

Every slow spot is a hardware event: a branch the predictor keeps getting
wrong, a load that keeps missing in cache, a pointer chain the prefetcher
cannot follow. The project diagnoses those events from the outside, with no
source code, and fixes them at the software level. It ties to the course
material on branch prediction, caches, and prefetching, but measured on a
real CPU instead of in a simulator.

## The four-step loop

1. **Profile.** Linux perf on the lab server: cycles, instructions,
   branch-misses, cache-misses, LLC misses; `perf record`/`report` for the
   exact addresses. Output: ranked hot functions with the events behind each.
2. **Lift.** Ghidra (headless, or driven by the agent through REA's MCP
   server) decompiles the hot functions; objdump as a cross-check. Output:
   pseudocode per hot spot, annotated with which lines the misses land on.
3. **Diagnose.** The agent reads pseudocode plus perf data and names the
   cause: data-dependent branch, pointer chase, struct layout wasting cache
   lines, long dependency chain. Output: one diagnosis per hot spot, with
   evidence.
4. **Optimize and measure.** The agent rewrites the hot spot to match the
   diagnosis (branch-free code or lookup table, software prefetch,
   AoS to SoA, loop restructuring). Recompile with the same flags. Verify
   output matches on the test set. Measure again. Record the speedup or
   the failure. Back to step 1.

## Two phases

- **Phase A, with source.** Calibrates the method: is the diagnosis right,
  is the rewrite equivalent, how faithful is Ghidra's output to the real code.
- **Phase B, source-less.** Stripped binaries. Everything the agent knows
  comes from perf and Ghidra. Compare speedup and correctness to Phase A.

## What "good" looks like

A table by bottleneck type (branch, cache, prefetch, dependency chain)
showing speedup, correctness, agent iterations, and with/without source.
Plus a written account of where the pipeline broke and why. A negative
result is a valid result, as long as it is measured.

## Open items (as of Nov 7, 2026)

- **Benchmark selection.** SPEC is off the table. Need open-source programs
  with clear hot spots and a test suite for correctness checks.
- **Agent cost.** Confirm how much agent time the department covers.
- **Measurement discipline.** Pinned core, repeated runs, medians, same
  flags every time. See `methodology.md`.
- **Correctness oracle.** Per benchmark, decide what "same output" means
  before optimizing anything.
