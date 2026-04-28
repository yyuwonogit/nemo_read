"""Fixed workflow for going from mailbox source CSVs to a LEAP-ready
canonical-native CSV, with unit audit + conversions baked in.

Sequence (each step writes a file the next step reads):

    1. build_canonical             ─ aggregates the 9 source CSVs
       └─ writes:  mailbox/canonical_leap_inputs.csv

    2. probe LEAP units            ─ requires LEAP open with target area
       └─ writes:  <export_dir>/branch_variable_units.csv

    3. audit canonical vs LEAP     ─ produces per-pair status + proposal
       └─ writes:  mailbox/unit_audit.csv

    4. apply conversions           ─ rewrites values in LEAP-native units
       └─ writes:  mailbox/canonical_leap_native.csv

After step 4 the LEAP-native CSV is what ``inject_to_leap.py`` should
consume. The injector refuses to push the source-units CSV (canonical_
leap_inputs.csv) when unresolved mismatches exist; it accepts only
canonical_leap_native.csv (or any CSV the user tags --already-converted).

Run the full pipeline:
    python mailbox/run_workflow.py

Skip step 2 when LEAP isn't available (uses cached units file if present):
    python mailbox/run_workflow.py --skip-probe

Apply user overrides to specific (branch, variable[, ams]) keys: edit the
``OVERRIDES`` dict at the top of this script.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd

from nemo_read import (
    LeapAreaContext, apply_audit_conversions, audit_canonical_units,
)


REPO_ROOT = Path(__file__).resolve().parent.parent
MAILBOX = REPO_ROOT / "mailbox"

# Per-row conversion overrides. Use this to pin a specific factor when the
# package's default proposal doesn't fit your data (e.g. Sumatran lignite
# LHV ≈ 11.5 GJ/tonne instead of IPCC default 11.9). Keys can be either:
#   (branch, variable)         — applies to every row in that branch+var
#   (branch, variable, ams)    — applies only to that AMS row
OVERRIDES: dict = {
    # Example (commented):
    # ("Resources\\Primary\\Coal Lignite", "Production Cost", "Indonesia"): {
    #     "factor": 11.5,
    #     "source": "PT Bukit Asam Sumatran lignite contracts (avg LHV)",
    #     "confidence_stars": 4,
    # },
}


def step1_build_canonical(log) -> Path:
    log("[step 1] build canonical from mailbox source CSVs")
    res = subprocess.run(
        [sys.executable, str(MAILBOX / "build_canonical.py")],
        capture_output=True, text=True,
    )
    if res.returncode != 0:
        log(res.stdout); log(res.stderr)
        raise RuntimeError("build_canonical.py failed")
    out = MAILBOX / "canonical_leap_inputs.csv"
    if not out.exists():
        raise RuntimeError(f"step 1 didn't produce {out}")
    log(f"   wrote {out.relative_to(REPO_ROOT)}")
    return out


def step2_probe_units(canonical_csv: Path, log, skip: bool = False) -> Path:
    """Run nemo_read-leap-units --canonical against live LEAP.

    Returns the units CSV path. Skipped (uses cached units file) when
    ``skip=True`` or LEAP is unavailable on this machine.
    """
    if skip:
        log("[step 2] SKIPPED — looking for cached branch_variable_units.csv")
    else:
        log("[step 2] probing LEAP for units (requires LEAP COM)")
    try:
        from nemo_read._leap_com import dispatch_leap
    except ImportError:
        log("   pywin32 not installed; skipping probe")
        skip = True
    if not skip:
        try:
            leap = dispatch_leap()
            area_name = leap.ActiveArea.Name
            if not area_name:
                raise RuntimeError(
                    "LEAP has no ActiveArea loaded — open the target area "
                    "(File → Open Area) before running the workflow"
                )
            log(f"   ActiveArea = {area_name!r}")
        except Exception as exc:
            log(f"   could not connect to LEAP ({exc}); skipping probe")
            skip = True

    if skip:
        candidates = list(Path.home().glob(
            "Documents/LEAP Areas/*/NEMO_25.leap_export/branch_variable_units.csv"
        ))
        if not candidates:
            raise RuntimeError(
                "no cached branch_variable_units.csv found and probe skipped — "
                "run nemo_read-leap-units --canonical first"
            )
        units_csv = max(candidates, key=lambda p: p.stat().st_mtime)
        log(f"   using cached units file: {units_csv}")
        return units_csv

    res = subprocess.run(
        [sys.executable, "-m", "nemo_read.leap_units",
         "--canonical", str(canonical_csv)],
        capture_output=True, text=True,
    )
    log(res.stdout.strip())
    if res.returncode != 0:
        log(res.stderr)
        raise RuntimeError("nemo_read-leap-units failed")
    # Parse the actual output path from stdout — more reliable than
    # re-computing it (the parent's dispatch state may differ from the
    # subprocess's at the moment of writing).
    units_csv = None
    for line in res.stdout.splitlines():
        line = line.strip()
        if "wrote" in line and "branch_variable_units.csv" in line:
            # Pattern: "[leap-units] wrote <path>  (N unit rows)"
            after = line.split("wrote", 1)[1].strip()
            path_str = after.rsplit("(", 1)[0].strip()
            units_csv = Path(path_str)
            break
    if units_csv is None or not units_csv.exists():
        raise RuntimeError(
            "could not locate branch_variable_units.csv from subprocess output"
        )
    log(f"   wrote {units_csv}")
    return units_csv


def step3_audit(canonical_csv: Path, units_csv: Path, log) -> tuple[Path, pd.DataFrame]:
    log("[step 3] audit canonical vs LEAP units")
    canonical = pd.read_csv(canonical_csv)
    ctx = LeapAreaContext.from_export(units_csv.parent)
    audit = audit_canonical_units(canonical, ctx)
    out = MAILBOX / "unit_audit.csv"
    audit.to_csv(out, index=False)
    counts = audit["status"].value_counts().to_dict()
    log(f"   wrote {out.relative_to(REPO_ROOT)}  ({len(audit)} rows; {counts})")
    n_unresolved = ((audit["status"] == "mismatch")
                    & (audit["proposed_factor"].isna())).sum()
    if n_unresolved > 0:
        log(f"   WARNING: {n_unresolved} mismatches have NO proposed factor "
            f"and need a manual override in OVERRIDES")
    return out, audit


def step4_apply(canonical_csv: Path, audit_df: pd.DataFrame, log) -> Path:
    log("[step 4] apply conversions -> canonical_leap_native.csv")
    canonical = pd.read_csv(canonical_csv)
    converted = apply_audit_conversions(canonical, audit_df, overrides=OVERRIDES)
    out = MAILBOX / "canonical_leap_native.csv"
    converted.to_csv(out, index=False)
    n_converted = (converted["unit_audit"].str.startswith("factor=", na=False)).sum()
    n_unresolved = (converted["unit_audit"]
                    .str.startswith("MISMATCH unresolved", na=False)).sum()
    log(f"   wrote {out.relative_to(REPO_ROOT)}  ({len(converted)} rows; "
        f"{n_converted} converted, {n_unresolved} unresolved)")
    if n_unresolved > 0:
        log(f"   {n_unresolved} rows still need user attention — "
            f"see 'unit_audit' column starting with MISMATCH unresolved")
    return out


def main(argv=None) -> int:
    import argparse
    p = argparse.ArgumentParser(prog="run_workflow")
    p.add_argument("--skip-probe", action="store_true",
                   help="Skip step 2 (units probe) — use the latest cached "
                        "branch_variable_units.csv from a prior run")
    args = p.parse_args(argv)

    def log(msg: str) -> None:
        print(msg)

    canonical_csv = step1_build_canonical(log)
    units_csv = step2_probe_units(canonical_csv, log, skip=args.skip_probe)
    _, audit = step3_audit(canonical_csv, units_csv, log)
    native_csv = step4_apply(canonical_csv, audit, log)

    # Snapshot ActiveArea so we can recommend the safe inject command.
    try:
        from nemo_read._leap_com import dispatch_leap
        leap_now = dispatch_leap()
        active_area = leap_now.ActiveArea.Name or ""
    except Exception:
        active_area = ""

    print()
    print(f"WORKFLOW DONE")
    print(f"  source-unit CSV:   {canonical_csv.relative_to(REPO_ROOT)}")
    print(f"  audit:             {(MAILBOX/'unit_audit.csv').relative_to(REPO_ROOT)}")
    print(f"  LEAP-native CSV:   {native_csv.relative_to(REPO_ROOT)}")
    print()
    print(f"Recommended inject command (set scenario manually in LEAP UI first):")
    cmd = (f"  python mailbox/inject_to_leap.py "
           f"--csv {native_csv.relative_to(REPO_ROOT)} "
           f"--no-scenario-switch")
    if active_area:
        cmd += f" --expect-area \"{active_area}\""
    cmd += " --dry-run"
    print(cmd)
    print()
    print(f"Drop --dry-run when you're satisfied with the dry-run output.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
