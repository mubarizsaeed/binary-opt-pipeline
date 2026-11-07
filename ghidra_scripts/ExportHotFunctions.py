# ExportHotFunctions.py - Ghidra headless script (Jython 2.7)
#
# Given a file of hot addresses (one hex address per line, as perf reports
# them after `pipeline lift` rebases them to the image base), decompile the
# function containing each address and write:
#   <out>/<func>.c      decompiled pseudocode
#   <out>/<func>.asm    disassembly of the same function
#   <out>/index.json    address -> function name, entry, size, line hit by the sample
#
# Run via ghidra_scripts/run_headless.sh. Script args: <addresses.txt> <out_dir>
#
# @category Analysis
from ghidra.app.decompiler import DecompInterface
from ghidra.util.task import ConsoleTaskMonitor
import json
import os

args = getScriptArgs()
if len(args) < 2:
    raise SystemExit("usage: ExportHotFunctions.py <addresses.txt> <out_dir>")
addr_file, out_dir = args[0], args[1]
if not os.path.isdir(out_dir):
    os.makedirs(out_dir)

program = currentProgram
listing = program.getListing()
fm = program.getFunctionManager()
af = program.getAddressFactory()
base = program.getImageBase()

decomp = DecompInterface()
decomp.openProgram(program)
monitor = ConsoleTaskMonitor()

index = {}
seen = set()
for raw in open(addr_file):
    raw = raw.strip()
    if not raw or raw.startswith("#"):
        continue
    addr = af.getAddress(raw)
    func = fm.getFunctionContaining(addr)
    if func is None:
        index[raw] = {"error": "no function contains this address"}
        continue
    name = func.getName()
    entry = func.getEntryPoint()
    res = decomp.decompileFunction(func, 60, monitor)
    if res.decompileCompleted():
        c_code = res.getDecompiledFunction().getC()
    else:
        c_code = "/* decompile failed: %s */\n" % res.getErrorMessage()

    if name not in seen:
        seen.add(name)
        with open(os.path.join(out_dir, name + ".c"), "w") as f:
            f.write(c_code)
        with open(os.path.join(out_dir, name + ".asm"), "w") as f:
            body = func.getBody()
            for cu in listing.getCodeUnits(body, True):
                f.write("%s  %s\n" % (cu.getAddress(), cu.toString()))
    index[raw] = {
        "function": name,
        "entry": str(entry),
        "size": func.getBody().getNumAddresses(),
        "offset_in_function": addr.subtract(entry),
        "signature": func.getPrototypeString(True, False),
    }

with open(os.path.join(out_dir, "index.json"), "w") as f:
    json.dump({"image_base": str(base), "functions": index}, f, indent=2)
print("ExportHotFunctions: wrote %d functions to %s" % (len(seen), out_dir))
