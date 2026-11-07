# Ghidra workflow

Ghidra is the decompiler. REA is the layer that lets a coding agent drive
Ghidra through an MCP server instead of a human clicking through the GUI.
This page covers the headless path, which is what the pipeline scripts use;
the MCP path is for the agent's interactive diagnose/optimize loop.

## Headless

```sh
export GHIDRA_HOME=~/ghidra_11.x
# addresses.txt comes from `pipeline hotspots --addresses`
ghidra_scripts/run_headless.sh benchmarks/branch_mispredict/bin/branch_mispredict.stripped addresses.txt lifted/branch_mispredict
```

`run_headless.sh` imports the binary into `ghidra_projects/` (first run) or
reuses the analysed project (later runs), then runs
`ExportHotFunctions.py`, which writes for each hot address:

- `<func>.c`: decompiled pseudocode
- `<func>.asm`: the function's disassembly, for cross-checking against
  `objdump -d` and `perf annotate`
- `index.json`: address to function mapping with entry, size, offset of
  the sample inside the function, and the recovered signature

## Address mapping

perf reports virtual addresses. For a non-PIE binary they match Ghidra's
image base directly. For PIE binaries perf's `--sort symbol` still gives
`symbol+offset`, and `perf annotate` prints file-relative addresses, so the
pipeline uses those and Ghidra's default image base. If the two disagree,
check `readelf -h` for the entry point and compare with Ghidra's.

## Recovering structure

Raw decompiler output has generic names (`uVar3`, `param_1`), lost types,
missing structs, and inlined code in odd places. The lift step is not done
when the file exists; it is done when a person could read it. The agent:

1. Renames variables from how they are used (loop counter, pointer walk).
2. Defines a struct where the code indexes a fixed stride into memory
   (`*(long *)(param_1 + 8)` is a field at offset 8).
3. Fixes the function signature and calling convention.
4. Re-decompiles and diffs against the previous output.

In Phase A we score this against the real source. That score decides how
much to trust the same process in Phase B.

## What to expect

Decompiler output does not compile as-is. Vectorised loops look like soup.
Compiler-inlined helpers show up inside the caller. Getting from pseudocode
to code that recompiles and behaves identically is the hardest step in the
pipeline and one of the things the project is measuring.
