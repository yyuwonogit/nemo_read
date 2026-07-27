"""Run every sealed pre-flight gate against the 20260722 bioenergy delta."""
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from nemo_read import (find_region_lock_violations,
                       find_zero_existing_capacity_conflicts,
                       validate_canonical_csv_expressions)

CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "bioenergy_delta_20260722.csv")

print("gate 1  find_region_lock_violations (A.21 node lock + A.23 base-branch lock)")
v = find_region_lock_violations(CSV)
print("        violations:", len(v))
for x in v[:20]:
    print("        ", x)

print("gate 2  validate_canonical_csv_expressions (A.15 Interp separator)")
try:
    validate_canonical_csv_expressions(CSV)
    print("        PASS - no forbidden Interp() form")
except Exception as e:
    print("        FAIL -", type(e).__name__, e)

print("gate 3  find_zero_existing_capacity_conflicts (S11.2b EC-zero vs HP-non-zero)")
c = find_zero_existing_capacity_conflicts(CSV)
print("        conflicts:", len(c))
for x in c[:20]:
    print("        ", x)
