"""Power-domain LEAP injector — thin subclass of CanonicalInjector.

All LEAP-side rules (Interp() separator enforcement, area/scenario
lock, safe_set_expression chokepoint, placeholder gate) come from
nemo_read.inject_base. This file owns only power-specific concerns:

  - 3-cache region grouping (Indonesia / Malaysia / Other). In
    `aeo9_v0.38_yy`, `leap.Branches.Count` enumeration is region-
    filtered: Indonesia + Malaysia each have unique subnational trees,
    the other 9 AMS share the country-level-only shape. So we build
    one cache per group (under a member of that group) and reuse it
    for every row in the group, but flip `ActiveRegion` per-row so
    the COM `branch.Variable(...)` reads see the right region's data.
  - --blind escape hatch — bypasses the tree cache (§11.1).
  - --expect-area required (cannot run unless caller names the area).

Usage:
    python inject/power/run_workflow.py \\
        --csv inject/power/20260507/ats_combined_canonical.csv \\
        --expect-area aeo9_v0.38_yy \\
        --expect-scenario "AMS Target Scenario"
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

from nemo_read._leap_com import LeapTreeCache
from nemo_read.inject_base import CanonicalInjector


GROUPS: dict[str, list[str]] = {
    "Indonesia": ["Indonesia"],
    "Malaysia": ["Malaysia"],
    "Other": [
        "Brunei", "Cambodia", "Laos", "Myanmar", "Philippines",
        "Singapore", "Thailand", "Timor Leste", "Vietnam",
    ],
}


def _group_for_region(region: str) -> str | None:
    for group_name, members in GROUPS.items():
        if region in members:
            return group_name
    return None


class PowerInjector(CanonicalInjector):
    SECTOR_NAME = "power"
    REQUIRE_EXPECT_AREA = True  # §A.9 — area must be confirmed

    # --blind is now inherited from the base CanonicalInjector
    # (promoted to the framework 2026-05-20). Power keeps only its
    # group-cache override below.

    def group_by_region(self, rows: list[dict]) -> dict[str, list[dict]]:
        """Group by GROUPS dict (Indonesia / Malaysia / Other), not by AMS.

        Rows within each group are sorted region-major (stable): branch-major
        CSVs interleave regions row-by-row, and the per-row ActiveRegion flip
        in `before_push_row` costs ~4s per REAL region switch in LEAP.
        Measured 2026-07-07 on the v0.69 sendback: 766 switches across the
        1,379-row CA 'Other' group = 4.75 s/row = 12h ETA; sorted, the group
        switches region only 8 times.
        """
        grouped: dict[str, list[dict]] = defaultdict(list)
        unknown: list[dict] = []
        for r in rows:
            g = _group_for_region(r.get("ams", ""))
            if g is None:
                unknown.append(r)
            else:
                grouped[g].append(r)
        if unknown:
            sample = [(r.get("ams"), r.get("branch")) for r in unknown[:3]]
            print(f"[power] {len(unknown)} row(s) with unknown region; "
                  f"first 3: {sample}")
        return {g: sorted(members, key=lambda r: r.get("ams", ""))
                for g, members in grouped.items()}

    def cache_for_region(self, leap, region: str) -> LeapTreeCache | None:
        """For power, `region` is a group name ('Indonesia'/'Malaysia'/
        'Other'). Build the cache under the first member of that group
        — it's valid for every member. Returns None in --blind mode."""
        if self._args.blind:
            print(f"  [power] --blind mode — no tree cache for group {region!r}")
            return None
        members = GROUPS.get(region, [])
        cache_region = members[0] if members else region
        print(f"  [power] cache built under {cache_region!r} for group "
              f"{region!r}")
        leap.ActiveRegion = leap.Regions(cache_region)
        return LeapTreeCache(leap=leap)

    def before_push_row(self, leap, row: dict, args: argparse.Namespace) -> None:
        """Set ActiveRegion to the row's ams before COM lookups.

        The cache built under one group member is valid for all members
        of the same group, but `branch.Variable(...)` reads data scoped
        to whatever ActiveRegion is at read time — so we flip it per row.
        """
        ams = row.get("ams")
        if ams:
            # The SET is the expensive call (~4s real region switch); the
            # READ is cheap. Skip when LEAP is already on the row's region
            # — and if the read comes back blank/garbage (§11.1), fall
            # through to the set, which is always safe.
            try:
                if leap.ActiveRegion.Name == ams:
                    return
            except Exception:
                pass
            try:
                leap.ActiveRegion = leap.Regions(ams)
            except Exception as exc:
                # A silent failure here means the write lands under a
                # STALE ActiveRegion — the §A.19 wrong-region-write
                # corruption. Abort loudly instead.
                raise RuntimeError(
                    f"[power] could not set ActiveRegion={ams!r} for "
                    f"{row.get('branch','?')} . {row.get('variable','?')}"
                    f": {exc}"
                ) from exc


if __name__ == "__main__":
    raise SystemExit(PowerInjector().run())
