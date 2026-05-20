"""Check CA-2024 vs forward-scenario-2025 continuity in transport canonical.

For each (ams, branch, variable) triple with both a Current Accounts row
and at least one forward-scenario (BAS/ATS/RAS) row, parse the Interp()
expressions and compare CA's 2024 value to the forward's 2025 value.

Reports mismatches > 1% relative difference. Should be near-zero for a
clean canonical — large discontinuities (e.g. CA_2024=70 vs BAS_2025=100)
indicate a build_canonical.py bug or raw-author data inconsistency.

Read-only — does not touch LEAP COM.
"""
from __future__ import annotations

import csv
import re
from collections import defaultdict
from pathlib import Path

INTERP_RE = re.compile(r"Interp\((.*)\)")


def parse_interp(expr: str | None) -> dict[int, float]:
    """Return {year: value} dict from an Interp(year, value, ...) expression."""
    if not expr:
        return {}
    m = INTERP_RE.search(expr)
    if not m:
        return {}
    tokens = [t.strip() for t in m.group(1).split(",")]
    out: dict[int, float] = {}
    for i in range(0, len(tokens) - 1, 2):
        try:
            yr = int(tokens[i])
            val = float(tokens[i + 1])
            out[yr] = val
        except (ValueError, IndexError):
            continue
    return out


def short_branch(branch: str) -> str:
    parts = branch.split("\\")
    if len(parts) >= 2:
        return parts[-2] + "\\" + parts[-1]
    return branch


def main() -> int:
    csv_path = Path(__file__).parent / "canonical_leap_inputs.csv"
    with csv_path.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    # Group by (ams, branch, variable)
    groups: dict[tuple[str, str, str], dict[str, str]] = defaultdict(dict)
    for r in rows:
        key = (r["ams"], r["branch"], r["variable"])
        groups[key][r["scenario"]] = r["expression"]

    mismatches = []
    for (ams, branch, var), by_scen in groups.items():
        ca_expr = by_scen.get("Current Accounts")
        if not ca_expr:
            continue
        ca = parse_interp(ca_expr)
        ca_2024 = ca.get(2024)
        if ca_2024 is None:
            continue
        for scen in ("Baseline Simulation", "AMS Target Scenario",
                     "Regional Aspiration Scenario"):
            fwd_expr = by_scen.get(scen)
            if not fwd_expr:
                continue
            fwd = parse_interp(fwd_expr)
            fwd_2025 = fwd.get(2025)
            if fwd_2025 is None:
                continue
            diff = abs(ca_2024 - fwd_2025)
            if diff < 0.01:
                continue
            rel = diff / max(abs(ca_2024), abs(fwd_2025), 1e-9)
            if rel < 0.01:
                continue
            mismatches.append({
                "ams": ams, "branch": branch, "var": var, "scen": scen,
                "ca_2024": ca_2024, "fwd_2025": fwd_2025,
                "diff": diff, "rel": rel,
            })

    print(f"Total (ams, branch, variable) groups examined: {len(groups)}")
    print(f"Mismatches (|CA_2024 - fwd_2025| / max > 1%): {len(mismatches)}")
    print()
    if not mismatches:
        print("CLEAN: no discontinuities found.")
        return 0

    scen_abbrev = {
        "Baseline Simulation": "BAS",
        "AMS Target Scenario": "ATS",
        "Regional Aspiration Scenario": "RAS",
    }
    print(f"{'AMS':<13} {'VAR':<16} {'SCEN':<5}  CA_2024     fwd_2025    diff       rel%   BRANCH")
    print("-" * 130)
    # Sort by descending relative diff
    for m in sorted(mismatches, key=lambda x: -x["rel"]):
        print(f"{m['ams']:<13} {m['var']:<16} "
              f"{scen_abbrev[m['scen']]:<5}  "
              f"{m['ca_2024']:10.4f}  {m['fwd_2025']:10.4f}  "
              f"{m['diff']:9.4f}  {m['rel']*100:6.1f}  "
              f"{short_branch(m['branch'])}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
