"""On-demand: list variable names on a single LEAP branch via COM.

Pure use of existing ``nemo_read._leap_com`` primitives:

  - ``dispatch_leap``          — connects to the running LEAP instance
  - ``LeapTreeCache``          — id/FullName index over all branches
  - ``iterate_variables_safe`` — yields (idx, name, expr) per variable,
    using the documented safe pattern (``fetch_expression=False`` skips
    ``.Expression`` access, which is what fires the
    "Expressions are not used for result variables" LEAP modal). This
    module also avoids ``.DataUnitText`` on result variables, so no
    modal popups can fire from the probe at all.

Use this when you want to discover what variables a specific branch
type exposes — e.g. the leaner Cultivation Process subtype (~30 vars)
versus a regular Biofuel Production process (44 vars). Faster and less
disruptive than a full-tree walk via ``nemo_read.leap_units --all``.

CLI:

    nemo_read-list-branch-vars "Transformation\\Palm Oil Cultivation\\Processes\\Palm Oil Cultivation"

Or fall back to suggestions if the FullName isn't found:

    nemo_read-list-branch-vars "non-matching-path"
    # → prints up to 30 'Cultivation'-containing branches as fallback hints
"""
from __future__ import annotations

import sys

from ._leap_com import (
    LeapTreeCache, dispatch_leap, iterate_variables_safe,
)


def list_branch_variables(branch_fullname: str) -> int:
    """Connect to LEAP, look up ``branch_fullname``, print its variable
    list. Returns 0 on success, 1 if the branch isn't found, 2 on COM
    failure. Designed as the CLI entry-point body; safe to call from
    interactive contexts too.
    """
    leap = dispatch_leap()
    print(f"[probe] ActiveArea: {leap.ActiveArea.Name!r}")
    print(f"[probe] building branch index ...")
    cache = LeapTreeCache(leap=leap)
    n = len(cache.fullname_to_idx)
    print(f"[probe] indexed {n} branches")

    idx = cache.fullname_to_idx.get(branch_fullname)
    if idx is None:
        print(f"\nERROR: branch not in tree: {branch_fullname!r}")
        # Show similar branches as a fallback hint, scoped to a keyword
        # taken from the requested path's last segment.
        leaf = branch_fullname.rsplit("\\", 1)[-1] if "\\" in branch_fullname else branch_fullname
        keyword = leaf.split()[0] if leaf else ""
        if keyword:
            similar = sorted([
                fn for fn in cache.fullname_to_idx
                if keyword.lower() in fn.lower()
            ])
            if similar:
                print(f"\n{len(similar)} branches contain {keyword!r}:")
                for fn in similar[:30]:
                    print(f"  {fn}")
                if len(similar) > 30:
                    print(f"  ... and {len(similar) - 30} more")
        return 1

    branch = cache.branches.Item(idx)
    print(f"\n[probe] branch:     {branch.FullName}")
    try:
        bt = branch.BranchType
        print(f"[probe] BranchType: {bt}")
    except Exception:
        pass
    try:
        vc = branch.Variables.Count
    except Exception as e:
        print(f"[probe] failed to read Variables.Count: {e}")
        return 2
    print(f"[probe] Variables:  {vc}\n")

    print(f"{'#':>3}  variable_name")
    print("-" * 60)
    for j, name, _ in iterate_variables_safe(
        branch, fetch_expression=False, deadline_seconds=30.0,
    ):
        print(f"{j:>3}  {name}")
    return 0


def cli_main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print(__doc__)
        return 2
    return list_branch_variables(args[0])


if __name__ == "__main__":
    sys.exit(cli_main())
