"""binary-opt-pipeline: profile -> lift -> diagnose -> optimize -> measure.

Modules:
    perf_parse   parse `perf report --stdio` and `perf stat -x,` output
    hotspots     rank hot functions and attach the hardware events behind them
    report       render the results table in docs/ and results/
    cli          `python -m pipeline <step>` entry point
"""
__version__ = "0.1.0"
