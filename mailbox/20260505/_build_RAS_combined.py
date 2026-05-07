"""Concatenate canonical_leap_native.csv + canonical_patch_2026_04_30.csv
into _inject_RAS_combined.csv (both target Regional Aspiration Scenario).

The two CSVs share core columns; native has an extra `unit_audit` column,
which is left empty for patch rows. Order: native rows first, then patch
(patch is curve-preserving Add deltas overlaid on native's Maximum Capacity
Interp baseline — must come after).
"""
from __future__ import annotations

import csv
from pathlib import Path

HERE = Path(__file__).parent
NATIVE = HERE.parent / "bioenergy" / "canonical_leap_native.csv"
PATCH = HERE.parent / "bioenergy" / "canonical_patch_2026_04_30.csv"
OUT = HERE / "_inject_RAS_combined.csv"


def main() -> int:
    with NATIVE.open(encoding="utf-8", newline="") as f:
        native_rows = list(csv.DictReader(f))
    with PATCH.open(encoding="utf-8", newline="") as f:
        patch_rows = list(csv.DictReader(f))

    fieldnames = list(native_rows[0].keys())
    extra_in_patch = [k for k in patch_rows[0] if k not in fieldnames]
    if extra_in_patch:
        raise SystemExit(f"unexpected new columns in patch: {extra_in_patch}")

    with OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in native_rows:
            w.writerow(r)
        for r in patch_rows:
            w.writerow({k: r.get(k, "") for k in fieldnames})

    print(f"native rows : {len(native_rows)}")
    print(f"patch rows  : {len(patch_rows)}")
    print(f"combined    : {len(native_rows) + len(patch_rows)} -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
