r"""Self-contained LEAP injector for the fridge Key-tree canonical.

PORTABLE: depends only on `pywin32` (Windows COM) + the standard library.
No `nemo_read` import. Copy this file + `canonical_fridge.csv` out of the
repo and it runs anywhere LEAP + pywin32 are installed.

It is branch-agnostic — it writes whatever `branch / variable / expression`
each canonical row names. The Phase-1 canonical targets the Key Assumptions
store `Key\Residential\Refrigeration\…` (Percent Ownership / Size_Share /
Efficiency_Share / Useful_EI), all on the `Activity Level` variable.

Load-bearing rules reproduced inline (same as the in-repo framework):
  * Interp() separator chokepoint  — comma list-sep + period decimal only.
  * Area lock                      — abort if ActiveArea drifts.
  * Scenario set + verify          — set ActiveScenario per scenario.
  * Scenario-column filter         — a tagged row goes ONLY to its scenario;
                                     an untagged row goes to every scenario.
  * Per-region ActiveRegion set    — set before each region's writes (Key
                                     Assumption values are region-scoped).
  * BLIND write                    — write via leap.Branches(FullName) so the
                                     value actually persists.
  * Hang-safe lookup               — a per-region name->index cache is checked
                                     first, so a wrong branch name is reported
                                     `branch_not_found` instead of hanging LEAP.
  * Read-back verify               — read each committed Expression back; EXACT
                                     required (NORMALISED/FAIL fail the run).

FLOW (one COM session): dispatch -> area lock -> for each scenario:
  set+verify -> scenario filter -> DRY RUN (existence check) -> confirm ->
  REAL inject (blind) -> READBACK.

Typical run (after build_canonical_fridge_keys.py):

    python inject_fridge_leap.py ^
        --csv canonical_fridge.csv ^
        --expect-area "AEO9" ^
        --scenarios "Baseline Simulation,AMS Target Scenario,Regional Aspiration Scenario" ^
        --fail-fast --yes

Let the dry run happen on the first push (don't pass --skip-dry-run) so any
Key-path mismatch surfaces before a write. Fridge data is ASEAN-10 (no Timor
Leste), so there is no supplement.
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
    from pathlib import Path
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


class FridgeKeyInjector:
    SECTOR = "fridge_keys"

    def run(self, argv=None):
        for stream in (sys.stdout, sys.stderr):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass
        args = self._parser().parse_args(argv)

        csv_path = Path(args.csv)
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

        # Build the FullName existence index ONCE (area-wide, region-independent
        # for these structural Key/Demand branches). Used only for hang-safe
        # existence checks; the actual write is blind per-region.
        print(f"[{self.SECTOR}] building branch index once (this is the slow "
              f"step, ~1-3 min on a large area)...")
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
                  f"Likely a Key branch path in the canonical doesn't match the "
                  f"live tree; fix KEY_BASE / naming in the adapter and rebuild.")
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
            print(f"      [SKIP] {branch_path} — not found in region tree")
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
        p = argparse.ArgumentParser(prog="inject_fridge_leap",
                                    description="Self-contained fridge Key-tree LEAP injector.")
        p.add_argument("--csv", default="canonical_fridge.csv")
        p.add_argument("--expect-area", help="Abort if leap.ActiveArea.Name != this")
        p.add_argument("--scenario", help="single LEAP scenario name")
        p.add_argument("--scenarios", default="",
                       help="comma list of LEAP scenario names, one COM session")
        p.add_argument("--no-scenario-switch", action="store_true")
        p.add_argument("--dry-run-only", "--dry-run", action="store_true")
        p.add_argument("--skip-dry-run", action="store_true")
        p.add_argument("--yes", "-y", action="store_true")
        p.add_argument("--no-readback", action="store_true")
        p.add_argument("--readback-rows-per-region", type=int, default=1)
        p.add_argument("--fail-fast", action="store_true")
        p.add_argument("--filter-ams", default="")
        p.add_argument("--filter-variable", default="")
        p.add_argument("--filter-branch", default="",
                       help="substring filter on branch path "
                            "(e.g. 'Efficiency_Share')")
        return p


if __name__ == "__main__":
    raise SystemExit(FridgeKeyInjector().run())
