r"""Self-contained LEAP injector for the 2026-08-13 High-Eff drift patch.

PORTABLE: depends only on `pywin32` (Windows COM) + the standard library.
No `nemo_read` import. Copy this file + `higheff_patch_canonical.csv` to any
machine with LEAP + Python + pywin32 and it runs.

WHAT THE PATCH IS (1,320 rows, AC + Fridge, 10 ASEAN regions):
  * `Efficiency` on the Demand device leaves
    (`Demand\Residential\Projections\Air Conditioning_\<Size>\<Eff>` and
    `Refrigeration_\...`) — High_eff kWh drift, ramps to 100% at 2060
    (AC 0.5%/yr, Fridge 2.0%/yr, ultimate-frontier floored). All 4 scenarios.
  * `Activity Level` on the Key efficiency-share store
    (`Key\Residential\<Appliance>\Efficiency_Share\<Size>_<Tier>`).
  * `Variable OM Cost` + `Exogenous Devices` on the device leaves (RAS only).
  Rows are scenario-tagged: Current Accounts / Baseline Simulation /
  AMS Target Scenario 240 each + Regional Aspiration Scenario 600. Each row
  is pushed ONLY into its tagged scenario.

================================ QUICK GUIDE =================================
v0.92 UPDATE (2026-08-14): use `higheff_patch_canonical_v092.csv` (the default).
It translates the original patch to the v0.92 conventions: RAS rows retagged to
"ASEAN Coordinated Transition" (ACT), and the 30 fridge-Large VOM rows rescaled
USD/kWh -> USD/GJ (x277.778) to match the area's new per-GJ VOM storage. The
original `higheff_patch_canonical.csv` is SUPERSEDED — do not inject it.

1.  One-time setup on the LEAP machine:
        pip install pywin32
2.  In LEAP:
      - Open the aeo9_v0.92 area. CLOSE every other area (multi-area COM trap).
      - Settings -> Regional -> decimal separator MUST be '.' (period).
      - Nothing mid-flight (no calc running, no dialog open).
3.  DRY RUN first (writes nothing; checks every branch path exists):
        python inject_higheff_patch.py --expect-area "aeo9_v0.92" --dry-run
4.  REAL inject (all 4 scenarios in one COM session; ~5-10 min):
        python inject_higheff_patch.py --expect-area "aeo9_v0.92" --fail-fast --yes
5.  Read the tail of the output. Success looks like:
        [real-inject] {'pushed': N}     (zero *_not_found / set_failed)
        Readback: N EXACT, 0 NORMALISED, 0 FAIL   per scenario
    ANY 'NORMALISED' or 'FAIL' readback = STOP, do not calculate; report back.
6.  Only after a clean run: recalculate the scenarios in LEAP.

Notes
  - If the area file is named differently on your machine, pass that exact
    name to --expect-area (the script aborts rather than write elsewhere).
  - Useful scoping flags while testing: --filter-ams "Brunei"
    --filter-variable "Efficiency" --filter-branch "Air Conditioning_"
    --scenarios "Regional Aspiration Scenario"
  - The script never creates branches; a `branch_not_found` means the area
    tree does not match the patch (wrong area version) — stop and report.
===============================================================================

Load-bearing rules reproduced inline (same as the in-repo framework):
  * Interp() separator chokepoint  — comma list-sep + period decimal only.
  * Area lock                      — abort if ActiveArea drifts.
  * Scenario set + verify          — set ActiveScenario per scenario.
  * Scenario-column filter         — a tagged row goes ONLY to its scenario;
                                     an untagged row goes to every scenario.
  * Per-region ActiveRegion set    — set before each region's writes.
  * BLIND write                    — write via leap.Branches(FullName); cached
                                     writes silently no-op on Key\/Demand\.
  * Hang-safe lookup               — FullName existence index checked first, so
                                     a wrong branch name reports
                                     `branch_not_found` instead of hanging LEAP.
  * Read-back verify               — read committed Expressions back; EXACT
                                     required (NORMALISED/FAIL fail the run).

FLOW (one COM session): dispatch -> area lock -> for each scenario:
  set+verify -> scenario filter -> DRY RUN (existence check) -> confirm ->
  REAL inject (blind) -> READBACK.
"""
from __future__ import annotations

import argparse
import copy
import csv
import re
import sys
from collections import Counter
from pathlib import Path

try:
    import pywintypes
    import win32com.client
except ImportError:  # pragma: no cover - Windows-only
    pywintypes = None
    win32com = None


_INTERP_RE = re.compile(r"Interp\(([^)]*)\)", re.IGNORECASE)
_SEMI_IN_INTERP = re.compile(r"Interp\([^)]*;[^)]*\)", re.IGNORECASE)

# v0.92 naming: "Regional Aspiration Scenario" was renamed
# "ASEAN Coordinated Transition" (ACT). Use the v092 CSV, whose rows are
# retagged to ACT and whose VOM coefficients are rescaled to USD/GJ.
DEFAULT_SCENARIOS = ("Current Accounts,Baseline Simulation,"
                     "AMS Target Scenario,ASEAN Coordinated Transition")


def normalize_interp(expr):
    if not isinstance(expr, str):
        return expr

    def _fix(m):
        return f"Interp({m.group(1).replace('; ', ', ').replace(';', ',')})"

    return _INTERP_RE.sub(_fix, expr)


def assert_interp_canonical(expr):
    if isinstance(expr, str) and _SEMI_IN_INTERP.search(expr):
        raise ValueError(f"Interp() uses ';' list-separator (forbidden): {expr!r}")


def safe_set_expression(variable, expr):
    """The ONLY place Variable.Expression is written. Normalise -> assert -> set."""
    normalised = normalize_interp(expr)
    assert_interp_canonical(normalised)
    variable.Expression = normalised
    return normalised


def safe_expression(variable):
    try:
        expr = variable.Expression
    except (pywintypes.com_error, AttributeError):
        return None
    if expr is not None and not isinstance(expr, (str, int, float, bool)):
        return None
    return expr


def compare_expressions(actual, expected):
    if actual is None or expected is None:
        return "FAIL"
    a, e = str(actual), str(expected)
    if a == e:
        return "EXACT"

    def _strip(s):
        def _fix(m):
            inner = (m.group(1).replace(". ", ", ").replace("; ", ", ").replace(";", ","))
            return f"Interp({inner})"
        return _INTERP_RE.sub(_fix, s)

    return "NORMALISED" if _strip(a) == _strip(e) else "FAIL"


def _assert_leap_unlocked():
    """Refuse to attach to LEAP while the user holds the .leap_lock interlock.

    Inlined (no nemo_read import) to keep this script portable — same contract
    as nemo_read.assert_leap_access_allowed.
    """
    import os
    env = os.environ.get("NEMO_READ_LEAP_LOCK", "").strip()
    if env:
        if env.lower() in {"1", "true", "yes", "on"}:
            raise SystemExit("LEAP COM BLOCKED — $NEMO_READ_LEAP_LOCK is set.")
        if Path(env).exists():
            raise SystemExit(f"LEAP COM BLOCKED — lock file {env}")
    here = Path(__file__).resolve()
    for d in (here.parent, *here.parents):
        lock = d / ".leap_lock"
        if lock.exists():
            raise SystemExit(
                f"LEAP COM BLOCKED — lock file {lock}\n"
                "The user is working in LEAP. Delete the lock only on their explicit say-so."
            )


def dispatch_leap():
    _assert_leap_unlocked()
    if win32com is None:
        raise RuntimeError("pywin32 not installed. `pip install pywin32` and run "
                           "on the Windows machine with LEAP open.")
    return win32com.client.Dispatch("LEAP.LEAPApplication")


def build_fullname_index(leap):
    branches = leap.Branches
    idx = {}
    for i in range(1, branches.Count + 1):
        try:
            idx[branches.Item(i).FullName] = i
        except Exception:
            continue
    return idx


class HighEffPatchInjector:
    SECTOR = "higheff_patch"

    def run(self, argv=None):
        for stream in (sys.stdout, sys.stderr):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass
        args = self._parser().parse_args(argv)

        csv_path = Path(args.csv)
        if not csv_path.is_absolute() and not csv_path.exists():
            beside = Path(__file__).resolve().parent / csv_path
            if beside.exists():
                csv_path = beside
        if not csv_path.exists():
            print(f"[{self.SECTOR}] CSV not found: {csv_path}", file=sys.stderr)
            return 1
        rows = self._load(csv_path)
        rows = self._apply_filters(rows, args)
        if not rows:
            print(f"[{self.SECTOR}] no rows after filters; nothing to do.")
            return 0
        bad = [r["expression"] for r in rows
               if isinstance(r.get("expression"), str)
               and _SEMI_IN_INTERP.search(r["expression"])]
        if bad:
            print(f"[{self.SECTOR}] REFUSED: {len(bad)} row(s) have a forbidden "
                  f"';' Interp separator. First: {bad[0]}", file=sys.stderr)
            return 2

        scenarios = ([s.strip() for s in args.scenarios.split(",") if s.strip()]
                     if args.scenarios else [args.scenario] if args.scenario else [None])

        leap = dispatch_leap()
        area = leap.ActiveArea.Name
        if args.expect_area and area != args.expect_area:
            print(f"[{self.SECTOR}] ActiveArea is {area!r}, expected "
                  f"{args.expect_area!r}. Aborting (area-drift). Confirm the "
                  f"right area is open and rerun.", file=sys.stderr)
            return 3
        print(f"[{self.SECTOR}] ActiveArea (locked): {area!r}")
        print(f"[{self.SECTOR}] {len(rows)} rows; scenarios: {scenarios or '<current>'}")

        # Build the FullName existence index ONCE (area-wide). Used only for
        # hang-safe existence checks; the actual write is blind per-region.
        print(f"[{self.SECTOR}] building branch index once (the slow step, "
              f"~1-3 min on a large area)...")
        self._index = build_fullname_index(leap)
        print(f"[{self.SECTOR}] indexed {len(self._index)} branches")

        any_failed = False
        for scen in scenarios:
            if self._scenario_cycle(leap, scen, rows, args) != 0:
                any_failed = True
                if args.fail_fast:
                    print(f"[{self.SECTOR}] --fail-fast: stopping.")
                    break
        print(f"\n[{self.SECTOR}] === DONE === "
              f"({'with failures' if any_failed else 'clean'})")
        return 1 if any_failed else 0

    def _scenario_cycle(self, leap, scenario, rows, args):
        label = scenario or "<current scenario>"
        print(f"\n[{self.SECTOR}] === SCENARIO: {label!r} ===")
        if scenario and not args.no_scenario_switch:
            try:
                leap.ActiveScenario = leap.Scenarios(scenario)
            except Exception as exc:
                print(f"  ERROR: cannot switch to {scenario!r}: {exc}", file=sys.stderr)
                return 4
            if args.expect_area and leap.ActiveArea.Name != args.expect_area:
                print(f"  ERROR: area drifted to {leap.ActiveArea.Name!r}. Aborting.",
                      file=sys.stderr)
                return 3
        active = leap.ActiveScenario.Name
        print(f"  ActiveScenario: {active!r}")

        sub = [r for r in rows
               if not (r.get("scenario") or "").strip()
               or (r.get("scenario") or "").strip() == active]
        print(f"  rows for this scenario: {len(sub)} (untagged + scenario={active!r})")
        if not sub:
            print("  nothing tagged for this scenario; skipping.")
            return 0

        groups = {}
        for r in sub:
            groups.setdefault(r["ams"], []).append(r)
        print(f"  {len(sub)} rows across {len(groups)} region(s)")

        if args.skip_dry_run:
            print("  -- Phase 1: DRY RUN skipped --")
            dcounts, dfail = Counter(), []
        else:
            print("  -- Phase 1: DRY RUN --")
            dcounts, dfail, _ = self._phase(leap, groups, args, dry_run=True)
            print(f"  [dry-run] {dict(dcounts)}")
        if dfail or dcounts.get("branch_not_found") or dcounts.get("var_not_found") \
                or dcounts.get("row_invalid"):
            print(f"  DRY-RUN HAS FAILURES — refusing real inject for {label!r}. "
                  f"A branch path in the patch doesn't match the live tree; "
                  f"the open area is probably not the intended version.")
            return 5
        if args.dry_run_only:
            print("  --dry-run-only: stopping.")
            return 0

        if not args.yes and not self._confirm(
                f"  Dry-run clean for {label!r}. Proceed with REAL inject? [y/N] "):
            print(f"  declined; skipping real inject for {label!r}.")
            return 6

        print("  -- Phase 3: REAL INJECT --")
        counts, failures, committed = self._phase(leap, groups, args, dry_run=False)
        print(f"  [real-inject] {dict(counts)}")
        for r, msg in failures[:5]:
            print(f"    - {r.get('ams')} | {r.get('branch')}: {msg}")

        if not args.no_readback and committed:
            print("  -- Phase 4: READBACK VERIFY --")
            if not self._readback(leap, committed, args.readback_rows_per_region):
                print(f"  READBACK FAILED for {label!r}.")
                return 7
        return 1 if failures else 0

    def _phase(self, leap, groups, args, dry_run):
        counts, failures, committed = Counter(), [], []
        pa = copy.copy(args)
        pa.dry_run = dry_run
        for region, group_rows in groups.items():
            print(f"    --- region {region!r} ({len(group_rows)} rows) ---")
            try:
                leap.ActiveRegion = leap.Regions(region)
            except Exception as exc:
                print(f"      WARN: cannot set ActiveRegion={region!r}: {exc}")
            for r in group_rows:
                self._push_one(leap, self._index, r, pa, counts, failures, committed)
        return counts, failures, committed

    def _push_one(self, leap, cache, row, args, counts, failures, committed):
        branch_path = row.get("branch", "")
        var_name = row.get("variable", "")
        expr = row.get("expression", "")

        def ff(reason):
            if args.fail_fast:
                raise SystemExit(f"[{self.SECTOR}] FAIL-FAST: {reason}")

        if not branch_path or not var_name or expr == "":
            failures.append((row, "missing branch/variable/expression"))
            counts["row_invalid"] += 1
            ff("row_invalid")
            return
        if branch_path not in cache:
            counts["branch_not_found"] += 1
            print(f"      [SKIP] {branch_path} — not found in area tree")
            ff(f"branch_not_found: {branch_path}")
            return
        try:
            branch = leap.Branches(branch_path)
            var = branch.Variable(var_name)
        except Exception as exc:
            failures.append((row, f"lookup error: {exc}"))
            counts["lookup_error"] += 1
            ff(f"lookup_error: {exc}")
            return
        if var is None:
            counts["var_not_found"] += 1
            print(f"      [SKIP] {branch_path} . {var_name!r} = None")
            ff(f"var_not_found: {var_name}")
            return
        if args.dry_run:
            preview = expr if len(expr) <= 70 else expr[:67] + "..."
            print(f"      [DRY] {branch_path} . {var_name!r} = {preview}")
            counts["dry_run"] += 1
            return
        try:
            committed_expr = safe_set_expression(var, expr)
            counts["pushed"] += 1
            committed.append(row)
            preview = committed_expr if len(committed_expr) <= 60 else committed_expr[:57] + "..."
            print(f"      [OK]  {branch_path} . {var_name!r} = {preview}")
        except Exception as exc:
            failures.append((row, f"set failed: {exc}"))
            counts["set_failed"] += 1
            print(f"      [ERR] {branch_path}: {exc}")
            ff(f"set_failed: {exc}")

    def _readback(self, leap, committed, rows_per_region):
        by_region = {}
        for row in committed:
            by_region.setdefault(row.get("ams", "?"), []).append(row)
        samples = []
        for rs in by_region.values():
            samples.extend(rs[:rows_per_region])
        print(f"    verifying {len(samples)} row(s) "
              f"({rows_per_region}/region x {len(by_region)} region(s))")
        n_exact = n_norm = n_fail = 0
        for row in samples:
            ams, bp, vn, exp = (row.get("ams"), row.get("branch", ""),
                                row.get("variable", ""), row.get("expression", ""))
            try:
                if ams:
                    leap.ActiveRegion = leap.Regions(ams)
                branch = leap.Branches(bp)
                var = branch.Variable(vn) if branch else None
                actual = safe_expression(var) if var else None
            except Exception as exc:
                print(f"    [FAIL] {ams}|{bp}.{vn}: {exc}")
                n_fail += 1
                continue
            verdict = compare_expressions(actual, exp)
            if verdict == "EXACT":
                n_exact += 1
                print(f"    [EXACT] {ams}|{vn} on {bp}")
            elif verdict == "NORMALISED":
                n_norm += 1
                print(f"    [NORM-FAIL] {ams}|{vn} on {bp} — separator renormalised. "
                      f"actual={actual!r}")
            else:
                n_fail += 1
                print(f"    [FAIL] {ams}|{vn} on {bp}")
                print(f"           actual:   {actual!r}")
                print(f"           expected: {exp!r}")
        print(f"    Readback: {n_exact} EXACT, {n_norm} NORMALISED, {n_fail} FAIL")
        return n_norm == 0 and n_fail == 0

    @staticmethod
    def _load(path):
        with path.open(encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))

    @staticmethod
    def _apply_filters(rows, args):
        ams = {a.strip() for a in args.filter_ams.split(",") if a.strip()}
        var = args.filter_variable.strip()
        branch_sub = args.filter_branch.strip()
        out = []
        for r in rows:
            if ams and r.get("ams") not in ams:
                continue
            if var and r.get("variable") != var:
                continue
            if branch_sub and branch_sub not in r.get("branch", ""):
                continue
            out.append(r)
        return out

    @staticmethod
    def _confirm(message):
        if not sys.stdin.isatty():
            print(f"{message}[non-interactive -> NO; pass --yes to proceed]")
            return False
        try:
            return input(message).strip().lower() in ("y", "yes")
        except EOFError:
            return False

    def _parser(self):
        p = argparse.ArgumentParser(
            prog="inject_higheff_patch",
            description="Self-contained injector for the 2026-08-13 High-Eff "
                        "drift patch (AC + Fridge) — target area aeo9_v0.90.")
        p.add_argument("--csv", default="higheff_patch_canonical_v092.csv",
                       help="patch CSV (default: beside this script; the v092 "
                            "file carries the ACT retag + USD/GJ VOM rescale)")
        p.add_argument("--expect-area", help="Abort if leap.ActiveArea.Name != this "
                                             "(use: aeo9_v0.92)")
        p.add_argument("--scenario", help="single LEAP scenario name")
        p.add_argument("--scenarios", default=DEFAULT_SCENARIOS,
                       help=f"comma list, one COM session (default: all four "
                            f"tagged in the patch)")
        p.add_argument("--no-scenario-switch", action="store_true",
                       help="don't touch ActiveScenario (user drives the UI dropdown)")
        p.add_argument("--dry-run-only", "--dry-run", action="store_true")
        p.add_argument("--skip-dry-run", action="store_true")
        p.add_argument("--yes", "-y", action="store_true")
        p.add_argument("--no-readback", action="store_true")
        p.add_argument("--readback-rows-per-region", type=int, default=2)
        p.add_argument("--fail-fast", action="store_true")
        p.add_argument("--filter-ams", default="")
        p.add_argument("--filter-variable", default="")
        p.add_argument("--filter-branch", default="",
                       help="substring filter on branch path "
                            "(e.g. 'Air Conditioning_' or 'Efficiency_Share')")
        return p


if __name__ == "__main__":
    raise SystemExit(HighEffPatchInjector().run())
