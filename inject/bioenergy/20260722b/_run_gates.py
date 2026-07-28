"""Run every sealed pre-flight gate against the 20260722b bioenergy delta.

Gate names are discovered from `nemo_read.__all__` so a newly-shipped
validator is picked up without editing this file.
"""
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import nemo_read

CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "bioenergy_delta_20260722b.csv")

CANDIDATES = [n for n in nemo_read.__all__
              if n.startswith(("find_", "validate_", "assert_"))
              and ("csv" in n or "violation" in n or "conflict" in n
                   or "expression" in n or "interp" in n.lower())]

print("gates discovered in nemo_read.__all__:")
for n in sorted(CANDIDATES):
    print("   ", n)
print()

import csv as _csv
import inspect

ROWS = list(_csv.DictReader(open(CSV, encoding="utf-8-sig")))

fails = 0
for name in sorted(CANDIDATES):
    fn = getattr(nemo_read, name)
    params = list(inspect.signature(fn).parameters)
    # per-EXPRESSION gates take `expr`, not a csv path -- calling them with a
    # path is a silent false PASS. Route them over every row instead.
    if params and params[0] == "expr":
        bad = []
        for r in ROWS:
            try:
                fn(r["expression"])
            except Exception as e:
                bad.append((r["ams"], r["variable"], type(e).__name__, str(e)[:80]))
        print(f"[{'PASS' if not bad else 'FAIL'}] {name}: checked "
              f"{len(ROWS)} expressions, {len(bad)} rejected")
        for x in bad[:20]:
            print("        ", x)
        fails += bool(bad)
        continue
    try:
        res = fn(CSV)
    except Exception as e:
        print(f"[FAIL] {name}: {type(e).__name__}: {e}")
        fails += 1
        continue
    if res is None:
        print(f"[PASS] {name}: no violations raised")
    else:
        n = len(res)
        print(f"[{'PASS' if n == 0 else 'FAIL'}] {name}: {n} finding(s)")
        for x in list(res)[:20]:
            print("        ", x)
        fails += (n != 0)

print()
print("GATES:", "ALL PASS" if fails == 0 else f"{fails} FAILING")
sys.exit(1 if fails else 0)
