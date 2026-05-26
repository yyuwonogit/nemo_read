"""Diff new canonical (post-Lane-A fix) vs the 20260520 remainder-patched baseline."""
import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OLD = ROOT / "inject/transport/canonical_leap_inputs_remainder_patched_20260520.csv"
NEW = ROOT / "inject/transport/canonical_leap_inputs.csv"

def load(p):
    with open(p, encoding="utf-8") as f:
        return list(csv.DictReader(f))

old = load(OLD)
new = load(NEW)
SEP = "\\"

def key(r):
    return (r["ams"], r["branch"], r["variable"], r.get("scenario", ""))

old_d = {key(r): r["expression"] for r in old}
new_d = {key(r): r["expression"] for r in new}

print(f"baseline rows : {len(old)}")
print(f"new rows      : {len(new)}")
added = set(new_d) - set(old_d)
removed = set(old_d) - set(new_d)
common = set(old_d) & set(new_d)
changed = [k for k in common if old_d[k] != new_d[k]]
print(f"added (new-only)    : {len(added)}")
print(f"removed (old-only)  : {len(removed)}")
print(f"changed expression  : {len(changed)}")

print()
print("--- ADDED row families (count by family x scenario) ---")
fam = defaultdict(int)
for k in added:
    family = SEP.join(k[1].split(SEP)[:4])
    fam[(family, k[3])] += 1
for (f, s), n in sorted(fam.items()):
    print(f"  {n:4d}  {f}  [{s}]")

print()
print("--- REMOVED row families ---")
fam = defaultdict(int)
for k in removed:
    family = SEP.join(k[1].split(SEP)[:4])
    fam[(family, k[3])] += 1
for (f, s), n in sorted(fam.items()):
    print(f"  {n:4d}  {f}  [{s}]")

print()
print("--- CHANGED expressions (first 8) ---")
for k in sorted(changed)[:8]:
    print(f"  {k[0]} | {k[1]} | {k[3]}")
    print(f"    OLD: {old_d[k][:160]}")
    print(f"    NEW: {new_d[k][:160]}")

print()
print("--- Remainder(100) presence (sanity check the patches were retired) ---")
rem_old = sum(1 for r in old if "Remainder" in r["expression"])
rem_new = sum(1 for r in new if "Remainder" in r["expression"])
print(f"  baseline Remainder rows : {rem_old}")
print(f"  new      Remainder rows : {rem_new}")
