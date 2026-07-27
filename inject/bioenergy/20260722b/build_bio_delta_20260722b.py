"""Build the corrected bioenergy delta for cycle 20260722b.

Supersedes inject/bioenergy/20260722/ (known-bad: it rewrote refinery
`Maximum Capacity` from canon's `Add()` cumulative-additions form into a
`Max(Exogenous Capacity, Interp(...))` level, which would have instructed
the model to scrap ~90% of the Indonesian biodiesel fleet).

Rulings implemented (settled 2026-07-22, see BUILD_NOTES_20260722b.md):
  B1  refinery `Maximum Capacity` keeps `Add()` semantics -> NOT touched
  B2  invariant: no negative `Add()` argument (asserted against canon)
  B3  floor on all 200 cells; ceiling ONLY where ceiling > floor (162)
  B4  Philippines FAME `Exogenous Capacity` multiplier restored
  B5  `Max()` stays on `Maximum Imports` only -> not touched here
  B6  p4_pending branch-creates stay out
  B7  join on the team's `region` column, never `ams`
  B8  volume% -> energy% via the NON-LINEAR Mobius transform

Inputs  : the bioenergy team's 2026-07-22 RETURN package (read-only)
Outputs : bioenergy_delta_20260722b.csv  + _audit_*.csv
No LEAP COM. Nothing is injected by this script.
"""
from __future__ import annotations

import csv
import io
import os
import re
import sys
from collections import OrderedDict, defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = (r"C:\Users\ThinkPad\AppData\Local\Temp\claude"
       r"\c--Users-ThinkPad-Desktop-Py-YY-NEMO-read"
       r"\e5eed2c4-745e-4bab-a4ab-809cea7b2258\scratchpad\bio3")
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
CANON_XLSX = os.path.join(REPO, "LEAP structure", "LEAP Input Transformation.xlsx")

OUT_CSV = os.path.join(HERE, "bioenergy_delta_20260722b.csv")

# canonical column set, read off inject/bioenergy/canonical_leap_inputs.csv,
# plus the `scenario` column the CanonicalInjector filters on (A.20 #2).
COLUMNS = ["ams", "branch", "variable", "expression", "unit", "fuel", "source",
           "note", "src_csv", "domain", "data_confidence", "scenario"]

RAS = "Regional Aspiration Scenario"
ATS = "AMS Target Scenario"
BAS = "Baseline Simulation"

B = "\\"
DIESEL_BLEND = B.join(["Transformation", "Diesel Blending", "Processes", "Biodiesel"])
GASOLINE_BLEND = B.join(["Transformation", "Gasoline Blending", "Processes", "Ethanol"])
BIO_PROC = B.join(["Transformation", "Biodiesel Production", "Processes"]) + B
ETH_PROC = B.join(["Transformation", "Bioethanol Production", "Processes"]) + B

BIODIESEL_PROCS = ["FAME Biodiesel", "CME Biodiesel", "POME Biodiesel"]
ETHANOL_PROCS = ["Cassava", "Corn Ethanol", "Molasses", "Sugarcane"]

REFINERY_BRANCH = {p: BIO_PROC + p for p in BIODIESEL_PROCS}
REFINERY_BRANCH.update({p: ETH_PROC + p for p in ETHANOL_PROCS})

# B8 -- Mobius (non-linear) volume% -> energy% constants. Verbatim from the
# canon `Minimum Share of Production` expressions on the two blending
# processes (LEAP Input Transformation.xlsx, RAS, Base Template).
MOBIUS = {
    "Biodiesel": (38.997, 43.330),   # E_bio, E_fossil
    "Bioethanol": (26.744, 44.8),
}

# team fuel label -> (blending branch, canon units for the two share vars)
BLEND_TARGET = {
    "Biodiesel": DIESEL_BLEND,
    "Bioethanol": GASOLINE_BLEND,
}
UNIT_MIN_SHARE = "Percent"   # canon units on `Minimum Share of Production`
UNIT_MAX_SHARE = "%"         # canon units on `Maximum_Share_of_Production`

ANCHORS = [2025, 2026, 2027, 2030, 2035, 2040, 2045, 2050, 2055, 2060]

TEN_AMS = ["Brunei", "Cambodia", "Indonesia", "Laos", "Malaysia", "Myanmar",
           "Philippines", "Singapore", "Thailand", "Vietnam"]


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def read_csv(name):
    with open(os.path.join(PKG, name), encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def mobius(vol_pct, fuel):
    """B8. E(v) = v*E_bio / (v*E_bio + (1-v)*E_fossil) * 100, v = vol%/100.

    NON-LINEAR. A linear x38.997 over-permits ~1.48x and is wrong.
    """
    e_bio, e_fos = MOBIUS[fuel]
    v = vol_pct / 100.0
    denom = v * e_bio + (1.0 - v) * e_fos
    if denom <= 0:
        raise ValueError("non-positive Mobius denominator")
    return v * e_bio / denom * 100.0


def num(x, dp=6):
    """Format a number with PERIOD decimal, no exponent, trailing zeros cut."""
    s = f"{x:.{dp}f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s or "0"


def interp(pairs, dp=6):
    """A.15 -- COMMA list separator, PERIOD decimal. No semicolons ever."""
    body = ", ".join(f"{y}, {num(v, dp)}" for y, v in pairs)
    return f"Interp({body})"


def row(ams, branch, variable, expression, unit, fuel, source, note,
        src_csv, domain, confidence, scenario):
    return OrderedDict(zip(COLUMNS, [ams, branch, variable, expression, unit,
                                     fuel, source, note, src_csv, domain,
                                     confidence, scenario]))


# --------------------------------------------------------------------------
# canon reader (structure + the Add() baseline we must NOT disturb)
# --------------------------------------------------------------------------
def load_canon_transformation():
    import openpyxl
    wb = openpyxl.load_workbook(CANON_XLSX, read_only=True, data_only=True)
    ws = wb["Export"]
    out = []
    for r in ws.iter_rows(min_row=4, values_only=True):
        out.append(dict(branch=r[4], variable=r[5], scenario=r[6], region=r[7],
                        scale=r[8], units=r[9], per=r[10], expr=r[11]))
    return out


ADD_RE = re.compile(r"^\s*Add\s*\((.*)\)\s*$", re.S)


def add_arguments(expr):
    """Return the numeric value arguments of an Add(y1, v1, y2, v2, ...)."""
    m = ADD_RE.match(expr)
    if not m:
        return None
    parts = [p.strip() for p in m.group(1).split(",")]
    if len(parts) % 2:
        raise ValueError(f"odd Add() arity: {expr!r}")
    return [float(parts[i]) for i in range(1, len(parts), 2)]


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------
def main():
    report = []

    def say(msg=""):
        print(msg)
        report.append(msg)

    say("=" * 78)
    say("bioenergy delta 20260722b -- build")
    say("=" * 78)

    canon = load_canon_transformation()

    # ---------------- B2 proof: no negative Add() argument in canon ---------
    add_rows, neg = 0, []
    for c in canon:
        if (c["branch"] in REFINERY_BRANCH.values()
                and c["variable"] == "Maximum Capacity"
                and isinstance(c["expr"], str)):
            args = add_arguments(c["expr"])
            if args is None:
                continue
            add_rows += 1
            for a in args:
                if a < 0:
                    neg.append((c["branch"], c["region"], c["scenario"], a))
    say("")
    say(f"[B2] canon refinery `Maximum Capacity` rows in Add() form : {add_rows}")
    say(f"[B2] negative Add() arguments found                       : {len(neg)}")
    if neg:
        raise SystemExit(f"ABORT (B2): negative Add() argument(s): {neg[:5]}")
    say("[B2] PASS -- cap-below-fleet is structurally unreachable; no "
        "Max(Exogenous Capacity, N) guard is needed or authored.")

    rows = []
    audit_floor, audit_ceiling, audit_skipped, audit_buildrate = [], [], [], []

    # =================== GROUP 1 -- blend FLOOR (all 200 cells) =============
    floor = read_csv("blend_floor_mandated.csv")
    fkey = {}
    for r in floor:
        fkey[(r["region"], r["fuel"], int(r["year"]))] = float(r["min_blend_share_volume_pct"])
    assert len(fkey) == 200, f"expected 200 floor cells, got {len(fkey)}"

    g1 = 0
    for fuel in ("Biodiesel", "Bioethanol"):
        for region in TEN_AMS:
            pairs = []
            for y in ANCHORS:
                v = fkey[(region, fuel, y)]
                pairs.append((y, mobius(v, fuel)))
                audit_floor.append(dict(region=region, fuel=fuel, year=y,
                                        volume_pct=v,
                                        energy_pct=round(mobius(v, fuel), 6)))
            rows.append(row(
                region, BLEND_TARGET[fuel], "Minimum Share of Production",
                interp(pairs), UNIT_MIN_SHARE, fuel,
                "bioenergy team RETURN 2026-07-22 / blend_floor_mandated.csv",
                "B3 FLOOR: forced minimum = max(in-force mandate, canon RAS "
                "target). Volume%->energy% via the canon Mobius transform "
                "(B8); canon carries the identical Mobius on this variable as "
                "a live reference to Key\\Biofuel Blending Targets -- this "
                "delta pins it to the team's explicit anchors.",
                "blend_floor_mandated.csv", "blend_floor", "Team-owned content",
                RAS))
            g1 += 1
    say("")
    say(f"[G1] blend FLOOR  `Minimum Share of Production`  rows: {g1}  "
        f"(200 cells -> {g1} Interp series)")

    # =================== GROUP 2 -- blend CEILING (162 cells) ===============
    ceil = read_csv("blend_ceiling_ramp.csv")
    ckey = {}
    for r in ceil:
        ckey[(r["region"], r["fuel"], int(r["year"]))] = float(r["max_blend_share_volume_pct"])
    assert len(ckey) == 200, f"expected 200 ceiling cells, got {len(ckey)}"
    assert set(ckey) == set(fkey), "ceiling/floor key sets diverge"

    n_gt = sum(1 for k in ckey if ckey[k] > fkey[k])
    n_eq = sum(1 for k in ckey if ckey[k] == fkey[k])
    n_lt = sum(1 for k in ckey if ckey[k] < fkey[k])
    say("")
    say(f"[G2] ceiling vs floor across 200 cells: >{'':1}{n_gt}  =={n_eq}  <{n_lt}")
    if n_lt:
        raise SystemExit("ABORT (B3): ceiling < floor somewhere -- blocking "
                         "inversion, send back to the team.")
    assert (n_gt, n_eq) == (162, 38), f"expected 162/38, got {n_gt}/{n_eq}"

    g2, g2_series_skipped = 0, []
    for fuel in ("Biodiesel", "Bioethanol"):
        for region in TEN_AMS:
            pairs, skipped_years = [], []
            for y in ANCHORS:
                c, f = ckey[(region, fuel, y)], fkey[(region, fuel, y)]
                if c > f:
                    pairs.append((y, mobius(c, fuel)))
                    audit_ceiling.append(dict(region=region, fuel=fuel, year=y,
                                              ceiling_vol_pct=c, floor_vol_pct=f,
                                              ceiling_energy_pct=round(mobius(c, fuel), 6),
                                              authored="yes"))
                else:
                    skipped_years.append(y)
                    audit_skipped.append(dict(region=region, fuel=fuel, year=y,
                                              ceiling_vol_pct=c, floor_vol_pct=f,
                                              reason="ceiling<=floor -> canon "
                                                     "default 100 left standing "
                                                     "(B3: do not create the pin)"))
            if not pairs:
                g2_series_skipped.append((region, fuel, len(skipped_years)))
                continue
            note = ("B3 CEILING: physical blend-wall ramp, authored ONLY on "
                    "anchors where ceiling > floor. Guard keeps the mandate "
                    "dominant and is reference-first per S11.2e.")
            if skipped_years:
                note += (" Pinned anchors omitted from the Interp: "
                         + ", ".join(str(y) for y in skipped_years)
                         + " -- the Max() guard lifts those years back to the "
                           "floor, so no pin is created.")
            rows.append(row(
                region, BLEND_TARGET[fuel], "Maximum_Share_of_Production",
                f"Max(Minimum Share of Production, {interp(pairs)})",
                UNIT_MAX_SHARE, fuel,
                "bioenergy team RETURN 2026-07-22 / blend_ceiling_ramp.csv",
                note, "blend_ceiling_ramp.csv", "blend_ceiling",
                "Team-owned content", RAS))
            g2 += 1

    say(f"[G2] blend CEILING `Maximum_Share_of_Production` rows: {g2}  "
        f"({n_gt} authored cells; {n_eq} pinned cells NOT authored)")
    for region, fuel, n in g2_series_skipped:
        say(f"[G2]   series fully pinned, nothing authored: {region} / {fuel} "
            f"({n}/10 anchors pinned)")

    # =================== GROUP 3 -- refinery Maximum Capacity ===============
    say("")
    say("[G3] refinery `Maximum Capacity` rows: 0")
    say("[G3] The team shipped 80 `Maximum Capacity` rows in "
        "`bioenergy_leap_input.csv`, ALL in `Interp(2025, X, ...)` LEVEL "
        "form (zero `Add(`).")
    say("[G3] REFUSED under B1. Canon authors this variable as `Add()` = "
        "cumulative additions layered on top of `Exogenous Capacity`. "
        "Injecting a level would scrap the standing fleet.")
    say("[G3] Add()-preservation proof -- canon Indonesia FAME (RAS), "
        "untouched by this delta:")
    for c in canon:
        if (c["branch"] == BIO_PROC + "FAME Biodiesel"
                and c["variable"] == "Maximum Capacity"
                and c["scenario"] == RAS and c["region"] == "Indonesia"):
            say(f"[G3]   canon : {c['expr']}")
            say(f"[G3]   sum of Add() args = "
                f"{num(sum(add_arguments(c['expr'])), 3)} Million GJ/Yr of "
                f"ADDITIONS, on top of ~636.5 already standing.")
    for r in read_csv("bioenergy_leap_input.csv"):
        if (r["branch"] == BIO_PROC + "FAME Biodiesel"
                and r["variable"] == "Maximum Capacity"
                and r["ams"] == "Indonesia"):
            say(f"[G3]   team  : {r['expression'][:110]}...  <- LEVEL, refused")

    # =================== GROUP 4 -- refinery build rate =====================
    br = read_csv("build_rate_limit.csv")
    assert len(br) == 70, f"expected 70 build-rate rows, got {len(br)}"

    # canon units, per process, for `Maximum Capacity Addition`
    canon_mca_units = {}
    for c in canon:
        if (c["branch"] in REFINERY_BRANCH.values()
                and c["variable"] == "Maximum Capacity Addition"):
            canon_mca_units[c["branch"].split(B)[-1]] = f"{c['scale']} {c['units']}"

    # GJ per liter of biodiesel, DERIVED (not hardcoded) from the team's own
    # reconciliation: Indonesia FAME installed_2023 / canon's 2023 liter
    # figure. Used only to re-base the Philippines row for B4.
    id_installed = next(float(x["installed_2023"]) for x in br
                        if x["region"] == "Indonesia" and x["process"] == "FAME Biodiesel")
    GJ_PER_LITER_BIODIESEL = id_installed / 18548.0
    for sib_region, sib_liters in (("Malaysia", 1580.0), ("Thailand", 2910.0)):
        sib = next(float(x["installed_2023"]) for x in br
                   if x["region"] == sib_region and x["process"] == "FAME Biodiesel")
        rel = abs(sib / sib_liters - GJ_PER_LITER_BIODIESEL) / GJ_PER_LITER_BIODIESEL
        assert rel < 1e-5, (f"{sib_region} implies a different GJ/liter "
                            f"({rel:.2e} relative) -- re-verify")

    g4 = 0
    for r in br:
        region, proc = r["region"], r["process"]
        branch = REFINERY_BRANCH[proc]
        unit_team = r["unit"]
        unit_canon = canon_mca_units[proc]
        if unit_team != unit_canon:
            raise SystemExit(f"ABORT: unit mismatch {proc}: team {unit_team!r} "
                             f"vs canon {unit_canon!r}")
        installed = float(r["installed_2023"])
        alpha = float(r["alpha_per_yr"])
        floor_t = float(r["one_train_floor"])
        ffy = int(r["first_feasible_year"])

        # B4 knock-on: the team read Philippines FAME `installed_2023`
        # straight off the DEFECTIVE canon expression (bare Interp, no
        # multiplier). Re-base it onto the corrected expression, else the
        # Philippines gets a ~29x inflated build allowance.
        rebased = ""
        if region == "Philippines" and proc == "FAME Biodiesel":
            corrected = installed * GJ_PER_LITER_BIODIESEL
            rebased = (f"RE-BASED for B4: team shipped installed_2023="
                       f"{num(installed, 4)} read off the defective canon "
                       f"expression; corrected to {num(corrected, 4)} "
                       f"(x{num(GJ_PER_LITER_BIODIESEL, 7)} GJ/liter, the "
                       f"factor implied by the three sibling regions). ")
            installed = corrected

        # Offline resolution of the team's self-referential rule
        #   MaxCapAdd(y) = 0                       if y < ffy
        #                = MAX(one_train_floor, alpha * installed(y-1))
        # `installed(y-1)` is endogenous, so the rule is not offline-
        # resolvable as written. STRUCTURAL RESOLUTION (ours, flagged back
        # to the team): hold installed(y) = canon `Exogenous Capacity`,
        # which is constant post-2023. The rule then collapses to a
        # constant annual allowance from first_feasible_year onward.
        allowance = max(floor_t, alpha * installed)
        binder = "one_train_floor" if floor_t >= alpha * installed else "alpha x installed"
        pairs = [(2025, 0.0)] if ffy > 2025 else []
        if ffy > 2026:
            pairs.append((ffy - 1, 0.0))
        pairs.append((ffy, allowance))
        pairs.append((2060, allowance))
        if any(v < 0 for _, v in pairs):
            raise SystemExit(f"ABORT: negative build-rate for {region}/{proc}")

        rows.append(row(
            region, branch, "Maximum Capacity Addition", interp(pairs, dp=4),
            unit_canon, "Biodiesel" if proc in BIODIESEL_PROCS else "Ethanol",
            "bioenergy team RETURN 2026-07-22 / build_rate_limit.csv",
            f"G4 build-rate limit, resolved OFFLINE from the team's rule "
            f"(first_feasible_year={ffy}, alpha={num(alpha)}/yr, "
            f"one_train_floor={num(floor_t)}, installed_2023={num(installed, 4)}"
            f"). {rebased}Recursion closed by holding installed(y) = canon "
            f"`Exogenous Capacity` (constant post-2023) -> constant allowance "
            f"{num(allowance, 4)} from {ffy}, binder = {binder}. Pure numerics "
            f"-- no Max()/Min(), so S11.2e cannot fire. Replaces canon's "
            f"`Unlimited` (S A.11).",
            "build_rate_limit.csv", "build_rate", "Team-owned content", RAS))
        audit_buildrate.append(dict(
            region=region, process=proc, unit=unit_canon,
            installed_2023_team=r["installed_2023"],
            installed_2023_used=num(installed, 6),
            rebased_for_B4="yes" if rebased else "no",
            alpha=alpha, one_train_floor=floor_t, first_feasible_year=ffy,
            alpha_x_installed=num(alpha * installed, 6),
            allowance_per_yr=num(allowance, 6), binder=binder,
            series=interp(pairs, dp=4)))
        g4 += 1
    say("")
    say(f"[G4] build rate `Maximum Capacity Addition` rows: {g4}")
    say(f"[G4] canon units confirmed byte-exact per process: "
        f"{sorted(set(canon_mca_units.values()))}")

    # =================== GROUP 5 -- Philippines FAME Exogenous Capacity =====
    sibling = None
    ph_canon = {}
    for c in canon:
        if (c["branch"] == BIO_PROC + "FAME Biodiesel"
                and c["variable"] == "Exogenous Capacity"):
            if c["region"] == "Thailand" and c["scenario"] == RAS:
                sibling = c
            if c["region"] == "Philippines":
                ph_canon[c["scenario"]] = c
    assert sibling is not None, "Thailand FAME sibling not found in canon"
    ph_ras = ph_canon[RAS]
    ph_unit = f"{ph_ras['scale']} {ph_ras['units']}"

    MULT = " * 10^6 * ConvFuelUnits(liter, gj, biodiesel)"
    ph_series = ph_ras["expr"].split("?")[0].strip()
    assert ph_series.startswith("Interp(") and "ConvFuelUnits" not in ph_series, \
        "Philippines FAME no longer matches the B4 defect signature -- re-verify"
    ph_fixed = (ph_series + MULT +
                " ? (ACE) Biofuel Production, Feedstock, and Land Use Data in "
                "ASEAN.xlsx")

    g5 = 0
    for scen in (RAS, ATS, BAS):
        rows.append(row(
            "Philippines", BIO_PROC + "FAME Biodiesel", "Exogenous Capacity",
            ph_fixed, ph_unit, "Biodiesel",
            "B4 structural fix -- canon defect; multiplier mirrored from the "
            "Thailand/Indonesia/Malaysia siblings",
            "B4: canon Philippines carried the bare Interp series with NO "
            "multiplier while all three non-zero siblings carry "
            "'* 10^6 * ConvFuelUnits(liter, gj, biodiesel)'. Exogenous "
            "Capacity is a LOWER bound (exports as ResidualCapacity), so the "
            "bare form forced ~29x the plant the Philippines has. Sibling "
            "quoted verbatim in BUILD_NOTES.",
            "LEAP Input Transformation.xlsx (canon v0.67)", "exogenous_capacity_fix",
            "Structure-owned (ours)", scen))
        g5 += 1
    say("")
    say(f"[G5] Philippines FAME `Exogenous Capacity` rows: {g5} "
        f"(one per in-scope scenario: RAS / ATS / BAS)")
    say(f"[G5] canon carries the defective bare form in ALL "
        f"{len(ph_canon)} scenarios (incl. Current Accounts) -- CA is OUTSIDE "
        f"this cycle's declared scenario set and is NOT touched. Flagged.")
    say(f"[G5] sibling quoted (Thailand, RAS): {sibling['expr'][:96]}...")

    # =================== GROUP 6 -- nothing else authored ===================
    say("")
    say("[G6] additional canon-backed in-scope rows authored: 0  (see "
        "BUILD_NOTES S6 for the full inventory of what was deliberately "
        "left out and why)")

    # =================== assertions + write =================================
    say("")
    say("-" * 78)
    for r in rows:
        e = r["expression"]
        assert "Unlimited" not in e, f"Unlimited authored: {r}"
        assert ";" not in e, f"semicolon in expression (A.15): {r}"
        assert not re.search(r"\d,\d", e), f"comma decimal (A.15): {r}"
        assert not re.search(r"(Max|Min)\(\s*[-+.\d]", e), \
            f"numeric-first Max/Min (S11.2e): {r}"
        assert r["scenario"] in (RAS, ATS, BAS), f"out-of-scope scenario: {r}"
        assert "Cellulosic" not in r["branch"] and "Rice Straw" not in r["branch"]
        assert "Used Cooking Oil" not in r["branch"]
        assert r["ams"] in TEN_AMS, f"non-roster region: {r['ams']}"
    assert not any(r["variable"] == "Maximum Capacity" for r in rows), \
        "B1 violation: a refinery Maximum Capacity row leaked in"
    say("[gate-local] no Unlimited / no semicolon / no comma-decimal / "
        "no numeric-first Max|Min / no CNZ / no non-canon branch / "
        "no Maximum Capacity  -- PASS")

    with open(OUT_CSV, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)

    def dump(name, data):
        if not data:
            return
        p = os.path.join(HERE, name)
        with open(p, "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(data[0].keys()))
            w.writeheader()
            w.writerows(data)

    dump("_audit_floor_mobius.csv", audit_floor)
    dump("_audit_ceiling_authored.csv", audit_ceiling)
    dump("_audit_ceiling_skipped_pins.csv", audit_skipped)
    dump("_audit_buildrate_unroll.csv", audit_buildrate)

    say("")
    say("=" * 78)
    say(f"TOTAL ROWS: {len(rows)}   ->  {OUT_CSV}")
    say(f"  G1 floor            {g1:>4}")
    say(f"  G2 ceiling          {g2:>4}")
    say(f"  G3 refinery MaxCap  {0:>4}   (refused, B1)")
    say(f"  G4 build rate       {g4:>4}")
    say(f"  G5 PH FAME ExoCap   {g5:>4}")
    say(f"  G6 other            {0:>4}")
    say("=" * 78)

    with open(os.path.join(HERE, "_build_log_20260722b.txt"), "w",
              encoding="utf-8") as fh:
        fh.write("\n".join(report) + "\n")


if __name__ == "__main__":
    main()
