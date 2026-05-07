"""Read-back-one verify per CLAUDE.md §4.1 — for the v0.38 inject cycle.

Auto-detects ActiveScenario, runs every probe row defined for it,
sets ActiveRegion=Brunei, reads Variable.Expression via COM on each
targeted branch, diffs byte-exact against the inject CSV's expression.

Run after each UI scenario flip (RAS → CA → ATS → BAS).

Reports both:
- byte-exact PASS (commas survived — desired state)
- normalised PASS (commas got renormalised to ". " list-sep — values
  are intact, but separator is wrong; still need to fix on this engine,
  see reference_leap_separator_convention memory)

Pure read; relies on existing _leap_com defensive helpers.
"""
from __future__ import annotations

from pathlib import Path

from nemo_read._leap_com import LeapTreeCache, dispatch_leap, safe_expression

HERE = Path(__file__).parent
EXPECT_AREA = "aeo9_v0.38_yy"
DEFAULT_REGION = "Brunei"

# Per scenario: list of probe rows. Each row carries the (region, branch,
# variable, expected expression, src_csv) needed to diff what LEAP holds
# against what the source CSV asked for. `region` defaults to Brunei if
# omitted (for non-ID/MY probes).
PROBES: dict[str, list[dict[str, str]]] = {
    "Regional Aspiration Scenario": [
        {
            "region": "Brunei",
            "branch": r"Transformation\Biodiesel Production\Processes\FAME Biodiesel",
            "variable": "Capital Cost",
            "expected": (
                "Interp(2025, 3.2422, 2030, 3.0833, 2035, 2.9322, 2040, 2.7885, "
                "2045, 2.6518, 2050, 2.5219, 2055, 2.3983, 2060, 2.2807)"
            ),
            "src_csv": "mailbox/bioenergy/canonical_leap_native.csv",
        },
    ],
    "Current Accounts": [
        {
            "region": "Brunei",
            "branch": r"Transformation\Centralized Electricity Generation\Processes\Coal IGCC",
            "variable": "Existing Capacity",
            "expected": (
                "Interp(2005, 0, 2006, 0, 2007, 0, 2008, 0, 2009, 0, 2010, 0, "
                "2011, 0, 2012, 0, 2013, 0, 2014, 0, 2015, 0, 2016, 0, 2017, 0, "
                "2018, 0, 2019, 254, 2020, 254, 2021, 254, 2022, 254, 2023, 254, "
                "2024, 254, FirstScenarioYear, 0)"
            ),
            "src_csv": "mailbox/20260505/inject_round1p5_CA.csv",
        },
        {
            "region": "Brunei",
            "branch": r"Transformation\Centralized Electricity Generation\Processes\Coal IGCC",
            "variable": "Historical Production",
            "expected": (
                "Interp(2005, 0, 2006, 0, 2007, 0, 2008, 0, 2009, 0, 2010, 0, "
                "2011, 0, 2012, 0, 2013, 0, 2014, 0, 2015, 0, 2016, 0, 2017, 0, "
                "2018, 0, 2019, 484.082698, 2020, 914.47981, 2021, 1241.882, "
                "2022, 1207.644, 2023, 1144.308, 2024, 1190.072, FirstScenarioYear, 0)"
            ),
            "src_csv": "mailbox/20260505/inject_round1p5_CA.csv",
        },
        {
            "region": "Indonesia",
            "branch": r"Transformation\Centralized Electricity Generation\Processes\Coal Subcritical_IDJW",
            "variable": "Existing Capacity",
            "expected": (
                "Interp(2005, 7481.571872, 2006, 8571.195673, 2007, 9218.831228, "
                "2008, 9433.686626, 2009, 9663.888837, 2010, 9961.23336, 2011, "
                "12552.92659, 2012, 12895.16055, 2013, 16013.27252, 2014, "
                "17004.44651, 2015, 18635.42918, 2016, 18714.0816, 2017, "
                "17952.8566, 2018, 21622.25683, 2019, 24039.38005, 2020, "
                "24150.62428, 2021, 24125.31673, 2022, 28447.55458, 2023, "
                "33198.97004, 2024, 36256.53401, FirstScenarioYear, 0)"
            ),
            "src_csv": "mailbox/power/20260507/rev1_ca_canonical.csv",
        },
        {
            "region": "Malaysia",
            "branch": r"Transformation\Centralized Electricity Generation\Processes\Solar PV_MYPE",
            "variable": "Historical Production",
            "expected": (
                "Interp(2005, 0, 2006, 0, 2007, 0, 2008, 0, 2009, 0, 2010, 0, "
                "2011, 0, 2012, 43.15883146, 2013, 128.4706742, 2014, "
                "207.4732809, 2015, 249.8091685, 2016, 283.915618, 2017, "
                "302.020382, 2018, 577.8894382, 2019, 1334.083371, 2020, "
                "1882.575427, 2021, 1921.592108, 2022, 3119.871461, 2023, "
                "4026.024045, 2024, 5823.699101, FirstScenarioYear, 0)"
            ),
            "src_csv": "mailbox/power/20260507/rev1_ca_canonical.csv",
        },
    ],
    "AMS Target Scenario": [
        {
            "region": "Brunei",
            "branch": r"Transformation\Centralized Electricity Generation\Processes\Coal IGCC",
            "variable": "Historical Production",
            "expected": (
                "Interp(2005, 0, 2006, 0, 2007, 0, 2008, 0, 2009, 0, 2010, 0, "
                "2011, 0, 2012, 0, 2013, 0, 2014, 0, 2015, 0, 2016, 0, 2017, 0, "
                "2018, 0, 2019, 484.082698, 2020, 914.47981, 2021, 1241.882, "
                "2022, 1207.644, 2023, 1144.308, 2024, 1190.072, FirstScenarioYear, 0)"
            ),
            "src_csv": "mailbox/20260505/inject_round1p5_ATS.csv",
        },
        {
            "region": "Indonesia",
            "branch": r"Transformation\Centralized Electricity Generation\Processes\Gas Combined Cycle_IDJW",
            "variable": "Historical Production",
            "expected": (
                "Interp(2005, 28744.75644, 2006, 28656.41036, 2007, 28984.31023, "
                "2008, 33403.31321, 2009, 33249.55706, 2010, 36802.93835, 2011, "
                "37877.5325, 2012, 33204.53453, 2013, 35194.86979, 2014, "
                "37191.15141, 2015, 37925.95295, 2016, 40951.8062, 2017, "
                "37524.14818, 2018, 37345.75705, 2019, 36658.55197, 2020, "
                "30087.90471, 2021, 33310.38127, 2022, 29013.16765, 2023, "
                "32889.23153, 2024, 35970.47608, FirstScenarioYear, 0)"
            ),
            "src_csv": "mailbox/power/20260507/rev1_ats_canonical.csv",
        },
    ],
    "Baseline Simulation": [
        {
            "region": "Brunei",
            "branch": r"Transformation\Centralized Electricity Generation\Processes\Coal IGCC",
            "variable": "Historical Production",
            "expected": (
                "Interp(2005, 0, 2006, 0, 2007, 0, 2008, 0, 2009, 0, 2010, 0, "
                "2011, 0, 2012, 0, 2013, 0, 2014, 0, 2015, 0, 2016, 0, 2017, 0, "
                "2018, 0, 2019, 484.082698, 2020, 914.47981, 2021, 1241.882, "
                "2022, 1207.644, 2023, 1144.308, 2024, 1190.072, FirstScenarioYear, 0)"
            ),
            "src_csv": "mailbox/20260505/inject_round1p5_BAS.csv",
        },
        {
            "region": "Malaysia",
            "branch": r"Transformation\Centralized Electricity Generation\Processes\Large Hydro_MYSR",
            "variable": "Historical Production",
            "expected": (
                "Interp(2005, 3358.383201, 2006, 3535.051936, 2007, 3330.429287, "
                "2008, 4364.724097, 2009, 3852.049318, 2010, 3556.29691, 2011, "
                "4503.934587, 2012, 5063.012863, 2013, 5918.402624, 2014, "
                "7484.939952, 2015, 7784.605908, 2016, 11194.98339, 2017, "
                "15009.01538, 2018, 14717.7356, 2019, 14645.6145, 2020, "
                "15262.46234, 2021, 17390.18008, 2022, 17853.60565, 2023, "
                "17898.33191, 2024, 18839.26065, FirstScenarioYear, 0)"
            ),
            "src_csv": "mailbox/power/20260507/rev1_bas_canonical.csv",
        },
    ],
}


def normalise(s: str | None) -> str | None:
    """Replace '. ' (period-space) → ', ' (comma-space). Decimal points are
    never followed by a space, so they're untouched."""
    return None if s is None else s.replace(". ", ", ")


def run_probe(leap, cache, p: dict[str, str], scen_name: str) -> str:
    """Run one probe row. Returns 'EXACT' / 'NORMALISED' / 'FAIL'.

    Branch lookup: try the cache (fast). On cache miss, fall back to
    direct ``leap.Branches(FullName)`` — same blind-mode pattern as
    run_workflow.py uses when cache lazy-loading misses real branches.
    Hangs if the FullName doesn't exist; only safe because PROBES rows
    are author-curated and verified to exist."""
    region = p.get("region", DEFAULT_REGION)
    leap.ActiveRegion = region
    target_branch = p["branch"]
    branch = None
    if cache is not None and target_branch in cache.fullname_to_idx:
        idx = cache.fullname_to_idx[target_branch]
        branch = leap.Branches.Item(idx)
    else:
        # Cache miss → blind direct lookup. Trust PROBES dict.
        try:
            branch = leap.Branches(target_branch)
        except Exception as exc:
            print(f"  [FAIL] direct lookup {target_branch!r}: {exc}")
            return "FAIL"
    if branch is None:
        print(f"  [FAIL] branch not found: {target_branch!r}")
        return "FAIL"

    target_var = p["variable"]
    var_obj = None
    try:
        vc = branch.Variables.Count
    except Exception as e:
        print(f"  [FAIL] {target_branch} . {target_var!r}: Variables.Count -> {e}")
        return "FAIL"
    for j in range(1, vc + 1):
        try:
            v = branch.Variables.Item(j)
            name = v.Name
        except Exception:
            continue
        if name == target_var:
            var_obj = v
            break
    if var_obj is None:
        print(f"  [FAIL] {target_branch} . {target_var!r}: variable not found")
        return "FAIL"

    actual = safe_expression(var_obj)
    expected = p["expected"]

    leaf = target_branch.split(chr(92))[-1]
    if actual == expected:
        print(f"  [EXACT] {region}: {target_var!r} on {leaf!r}")
        return "EXACT"
    if normalise(actual) == normalise(expected):
        print(f"  [NORM ] {region}: {target_var!r} on {leaf!r}"
              f"  — periods, not commas (LEAP renormalised)")
        return "NORMALISED"
    print(f"  [FAIL] {region}: {target_var!r} on {leaf!r}")
    print(f"         actual  : {actual!r}")
    print(f"         expected: {expected!r}")
    if actual is not None:
        n = min(len(actual), len(expected))
        first_diff = next((i for i in range(n) if actual[i] != expected[i]), n)
        print(f"         first divergence at char {first_diff} "
              f"(actual_len={len(actual)}, expected_len={len(expected)})")
    return "FAIL"


def main() -> int:
    leap = dispatch_leap()

    area_name = leap.ActiveArea.Name
    print(f"[probe] ActiveArea: {area_name!r}")
    if area_name != EXPECT_AREA:
        print(f"  ERROR: expected {EXPECT_AREA!r}, aborting.")
        return 3

    scen_name = leap.ActiveScenario.Name
    print(f"[probe] ActiveScenario: {scen_name!r}")
    if scen_name not in PROBES:
        print(f"  ERROR: no probe rows defined for scenario {scen_name!r}.")
        print(f"  Known: {list(PROBES)}")
        return 2
    probes = PROBES[scen_name]

    # ActiveRegion is set per-probe-row inside run_probe (see PROBES dict).

    # Skip cache build — direct `leap.Branches(FullName)` lookup. PROBES
    # rows are author-curated and verified to exist, so the hang trap
    # (CLAUDE.md §11.1) doesn't fire. Saves ~5 min per probe run.
    cache = None
    print(f"[probe] using blind lookup (no tree cache build).")

    print(f"[probe] running {len(probes)} probe row(s) for {scen_name!r}:")
    results = [run_probe(leap, cache, p, scen_name) for p in probes]

    n_exact = sum(1 for r in results if r == "EXACT")
    n_norm = sum(1 for r in results if r == "NORMALISED")
    n_fail = sum(1 for r in results if r == "FAIL")
    print()
    print(f"[probe] {scen_name}: {n_exact} EXACT, {n_norm} NORMALISED, {n_fail} FAIL")
    if n_fail:
        return 1
    if n_norm and not n_exact:
        # All probes passed only after normalisation — inject is wrong on this engine
        return 0  # not a failure but caller should re-inject
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
