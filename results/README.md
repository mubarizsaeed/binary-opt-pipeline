# Results

**No measured results yet.** First measured numbers are due with the
progress report on Dec 3, 2026. Nothing goes in this table until the rewrite
has passed `scripts/verify.py` against the original binary on the agreed
input set.

`results.json` is appended by the measure step; `python -m pipeline results`
renders it. Raw perf output lives in `results/raw/` (gitignored, kept on the
lab server).

| benchmark | bottleneck | phase | speedup | correct | iterations | notes |
|---|---|---|---|---|---|---|
| _pending_ | | | | | | |

Measurement rules (see `docs/methodology.md`): pinned core, 7 repetitions,
medians, same compiler and flags for original and rewrite.
