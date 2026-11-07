#!/usr/bin/env python3
"""Correctness oracle: run the original and the rewritten binary on the same
inputs and compare their output.

    python3 scripts/verify.py ORIGINAL CANDIDATE [--inputs inputs.txt] [--mode checksum|stdout]

inputs.txt holds one argument list per line (empty file = run with no args).
Mode `checksum` compares only lines starting with `checksum:` (the calibration
kernels' contract); `stdout` compares the full output. Exit status is 0 when
every input matches, 1 otherwise. No speedup is reported until this passes.
"""
import argparse
import shlex
import subprocess
import sys


def run(binary, args):
    p = subprocess.run([binary, *args], capture_output=True, text=True, timeout=600)
    return p.returncode, p.stdout


def extract(stdout, mode):
    if mode == "checksum":
        return [l.strip() for l in stdout.splitlines() if l.startswith("checksum:")]
    return stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("original")
    ap.add_argument("candidate")
    ap.add_argument("--inputs", help="file with one argument list per line")
    ap.add_argument("--mode", choices=["checksum", "stdout"], default="checksum")
    a = ap.parse_args()

    inputs = [[]]
    if a.inputs:
        inputs = [shlex.split(l) for l in open(a.inputs) if l.strip() and not l.startswith("#")]

    failures = 0
    for args in inputs:
        rc_o, out_o = run(a.original, args)
        rc_c, out_c = run(a.candidate, args)
        same = rc_o == rc_c and extract(out_o, a.mode) == extract(out_c, a.mode)
        status = "ok  " if same else "FAIL"
        print(f"[{status}] args={' '.join(args) or '(none)'}")
        if not same:
            failures += 1
            print(f"       original rc={rc_o}: {extract(out_o, a.mode)}")
            print(f"       candidate rc={rc_c}: {extract(out_c, a.mode)}")
    print(f"{len(inputs) - failures}/{len(inputs)} inputs match")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
