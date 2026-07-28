"""Build the bioenergy liquid-biofuel-chain canonical delta for 2026-07-22.

Scope (user ruling R1): Resources (7 feedstocks) -> 7 refinery processes ->
Blending module. The 5 lite-panel processes are excluded entirely.

Produces:
    bioenergy_delta_20260722.csv    injectable canonical delta (12 cols)
    _audit_ceiling_vs_floor.csv     per (region, fuel, year) ceiling/floor audit
    _audit_unlimited.csv            every 'Unlimited' found in scope + disposition
    _audit_group3_before_after.csv  before/after for every 2025-anchor row

Run:  python build_blend_delta_20260722.py
"""
from __future__ import annotations

import csv
import io
import os
import re
import sys
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))

TEAM = os.environ.get(
    "BIO_RAMP_DIR",
    r"C:\Users\ThinkPad\AppData\Local\Temp\claude"
    r"\c--Users-ThinkPad-Desktop-Py-YY-NEMO-read"
    r"\e5eed2c4-745e-4bab-a4ab-809cea7b2258\scratchpad\bio_ramp",
)
TEAM721 = os.environ.get(
    "BIO_721_DIR",
    r"C:\Users\ThinkPad\AppData\Local\Temp\claude"
    r"\c--Users-ThinkPad-Desktop-Py-YY-NEMO-read"
    r"\e5eed2c4-745e-4bab-a4ab-809cea7b2258\scratchpad\bio721",
)

CANON = os.path.join(REPO, "inject", "bioenergy", "structure_handover_20260703")
CANON_T = os.path.join(CANON, "current_expressions_transformation_slice_4scenarios.csv")
CANON_R = os.path.join(CANON, "current_expressions_resources_4scenarios.csv")
CANON_K = os.path.join(CANON, "current_expressions_keys_slice_4scenarios.csv")

# ---------------------------------------------------------------- constants

AMS10 = ["Brunei", "Cambodia", "Indonesia", "Laos", "Malaysia",
         "Myanmar", "Philippines", "Singapore", "Thailand", "Vietnam"]

ALIAS = {"Brunei Darussalam": "Brunei", "Lao PDR": "Laos", "Viet Nam": "Vietnam"}

RAS = "Regional Aspiration Scenario"
ATS = "AMS Target Scenario"
BAS = "Baseline Simulation"
CA = "Current Accounts"

# Moebius energy transform constants -- canon source:
# inject/fossil/structure_handover_20260703/
#   current_expressions_transformation_slice_4scenarios.csv lines 624 / 1980
# (v0.67 canon expression; VALUE may be stale vs live v0.76+).
LHV = {"Biodiesel": (38.997, 43.330), "Bioethanol": (26.744, 44.8)}

BLEND_BRANCH = {
    "Biodiesel": r"Transformation\Diesel Blending\Processes\Biodiesel",
    "Bioethanol": r"Transformation\Gasoline Blending\Processes\Ethanol",
}
KEY_BRANCH = {
    "Biodiesel": r"Key\Biofuel Blending Targets\Biodiesel",
    "Bioethanol": r"Key\Biofuel Blending Targets\Bioethanol",
}

REFINERY = {
    "Biodiesel": [
        (r"Transformation\Biodiesel Production\Processes\FAME Biodiesel", "FAME Biodiesel"),
        (r"Transformation\Biodiesel Production\Processes\CME Biodiesel", "CME Biodiesel"),
        (r"Transformation\Biodiesel Production\Processes\POME Biodiesel", "POME Biodiesel"),
    ],
    "Bioethanol": [
        (r"Transformation\Bioethanol Production\Processes\Cassava", "Cassava"),
        (r"Transformation\Bioethanol Production\Processes\Corn Ethanol", "Corn Ethanol"),
        (r"Transformation\Bioethanol Production\Processes\Molasses", "Molasses"),
        (r"Transformation\Bioethanol Production\Processes\Sugarcane", "Sugarcane"),
    ],
}
REFINERY_UNIT = {"Biodiesel": "Million Gigajoules/Year",
                 "Bioethanol": "Million Tonne Coal Equiv/Year"}
MT_TO_NATIVE = {"Biodiesel": 38.997, "Bioethanol": 0.912528}

BLEND_PSEUDO = [
    (r"Transformation\Diesel Blending\Processes\Biodiesel", "biofuel"),
    (r"Transformation\Gasoline Blending\Processes\Ethanol", "biofuel"),
    (r"Transformation\Diesel Blending\Processes\Diesel", "fossil"),
    (r"Transformation\Gasoline Blending\Processes\Gasoline", "fossil"),
]

FEEDSTOCKS = ["Palm Oil", "Palm Oil Mill Effluent", "Coconut Oil",
              "Cassava", "Corn", "Molasses", "Sugarcane"]

# Generous-but-finite replacement for an 'Unlimited' UPPER bound expressed in
# Gigajoule.  10^10 GJ = 10,000 PJ; ~1/3 of total ASEAN primary energy supply,
# so non-binding, and 100x below the 1.0e+12 export sentinel (CLAUDE.md A.11).
GJ_CAP = "10^10"
# Finite-but-large replacement for an 'Unlimited' LOWER bound (Exogenous
# Capacity -> NEMO ResidualCapacity).  NEVER 0 (the 2026-05-12 p9 burn).
EC_FLOOR = "100000"
BLEND_MAXCAP_NUM = "100000"
BLEND_MAXCAPADD_NUM = "10000"

OUT = os.path.join(HERE, "bioenergy_delta_20260722.csv")
COLS = ["ams", "branch", "variable", "expression", "unit", "fuel", "source",
        "note", "src_csv", "domain", "data_confidence", "scenario"]

rows: list[dict] = []
blocked: list[tuple[str, str]] = []
counts: dict[str, int] = defaultdict(int)


def add(group, **kw):
    r = {c: "" for c in COLS}
    r.update(kw)
    rows.append(r)
    counts[group] += 1


def block(group, reason):
    blocked.append((group, reason))


# ---------------------------------------------------------------- helpers

def fmt(x, nd=4):
    s = f"{x:.{nd}f}".rstrip("0").rstrip(".")
    return s if s not in ("", "-0") else "0"


def energy_pct(vol_pct, fuel):
    """Moebius volume-% -> energy-%.  E(v)=v*Eb/(v*Eb+(1-v)*Ef)*100."""
    eb, ef = LHV[fuel]
    v = vol_pct / 100.0
    den = v * eb + (1.0 - v) * ef
    return 0.0 if den == 0 else v * eb / den * 100.0


def read(path):
    return list(csv.DictReader(open(path, encoding="utf-8-sig")))


def clean_expr(e):
    return e.split(" ? ")[0].split(" ?")[0].strip()


NUMPAIR = re.compile(r"(-?\d+(?:\.\d+)?)")


def parse_anchors(expr):
    """(kind, [(year, value), ...]) for scalar / Interp / InterpFSY."""
    e = expr.strip().replace("%", "")
    m = re.match(r"(?i)^(InterpFSY|Interp)\s*\((.*)\)\s*$", e)
    if not m:
        try:
            return "scalar", [(None, float(e))]
        except ValueError:
            return "other", []
    kind = "InterpFSY" if m.group(1).lower() == "interpfsy" else "Interp"
    nums = [float(x) for x in NUMPAIR.findall(m.group(2))]
    return kind, [(int(nums[i]), nums[i + 1]) for i in range(0, len(nums) - 1, 2)]


def eval_series(kind, pts, year):
    """Evaluate under the R2 RAMP reading of InterpFSY."""
    if kind == "scalar":
        return pts[0][1]
    if not pts:
        return None
    p = list(pts)
    if kind == "InterpFSY" and p[0][0] > 2024:
        p = [(2024, 0.0)] + p          # R2: linear ramp from (2024, 0)
    p.sort()
    if year <= p[0][0]:
        return p[0][1]
    if year >= p[-1][0]:
        return p[-1][1]                # R2: HOLD FLAT after the last anchor
    for i in range(len(p) - 1):
        (y0, v0), (y1, v1) = p[i], p[i + 1]
        if y0 <= year <= y1:
            return v0 + (v1 - v0) * (year - y0) / (y1 - y0)
    return p[-1][1]


def render(kind, pts):
    body = ", ".join(f"{y}, {fmt(v)}" for y, v in pts)
    return f"{kind}({body})" if kind != "scalar" else fmt(pts[0][1])


def set_2025(kind, pts, value):
    """Insert/replace the 2025 anchor, preserving every other anchor."""
    if kind == "scalar":
        return ("InterpFSY", [(2025, value)]) if value else ("scalar", [(None, 0.0)])
    p = [(y, v) for y, v in pts if y != 2025] + [(2025, value)]
    p.sort()
    return kind, p


# ================================================================= LOAD

canon_t = read(CANON_T)
canon_r = read(CANON_R)
canon_k = read(CANON_K)

# canon Key\Biofuel Blending Targets : Activity Level, per (fuel, scenario, region)
key_expr: dict[tuple[str, str, str], str] = {}
for x in canon_k:
    if not x["branch_path"].startswith(r"Key\Biofuel Blending Targets"):
        continue
    if x["variable"] != "Activity Level":
        continue
    fuel = x["branch_path"].rsplit("\\", 1)[-1]
    reg = x["region"]
    e = clean_expr(x["expression"])
    if reg.startswith("ALL "):
        for a in AMS10:
            key_expr.setdefault((fuel, x["scenario"], a), e)
    else:
        key_expr[(fuel, x["scenario"], reg)] = e


def canon_key(fuel, scen, ams):
    return key_expr.get((fuel, scen, ams), "0")


# ================================================================= GROUP 1
# Blending ceiling: Maximum_Share_of_Production, RAS only.

ceil_raw = read(os.path.join(TEAM, "blend_ceiling_ramp.csv"))
ceil: dict[tuple[str, str], dict[int, float]] = defaultdict(dict)
for x in ceil_raw:
    a = ALIAS.get(x["ams"], x["ams"])
    ceil[(a, x["fuel"])][int(x["year"])] = float(x["max_blend_share_volume_pct"])
YEARS = sorted({int(x["year"]) for x in ceil_raw})

audit_cf = []
for fuel in ("Biodiesel", "Bioethanol"):
    for a in AMS10:
        vol = ceil[(a, fuel)]
        if len(vol) != len(YEARS):
            block("G1", f"{a}/{fuel}: only {len(vol)}/{len(YEARS)} ceiling years")
            continue
        pts = [(y, energy_pct(vol[y], fuel)) for y in YEARS]
        inner = "Interp(" + ", ".join(f"{y}, {fmt(v)}" for y, v in pts) + ")"
        expr = f"Max(Minimum Share of Production, {inner})"
        add("G1", ams=a, branch=BLEND_BRANCH[fuel],
            variable="Maximum_Share_of_Production", expression=expr, unit="%",
            fuel=fuel,
            source="blend_ceiling_ramp.csv (bioenergy team 20260722); "
                   "vol%->energy% via canon Moebius transform "
                   "(E_bio/E_fossil from canon Minimum Share of Production, "
                   "v0.67 slice lines 624/1980 - canon VALUE may be stale)",
            note="R6/R7 wrapper: reference FIRST, numeric LAST (S11.2e). "
                 "Max() guarantees ceiling >= canon floor at every year. "
                 "RAS only: ATS/BAS carry Optimize=No so the bound is inert; "
                 "canon has NO Current Accounts row for this variable.",
            src_csv="blend_ceiling_ramp.csv", domain="blend_ceiling",
            data_confidence="Low", scenario=RAS)

G3_ANCHOR: dict[tuple[str, str], float] = {}
for fuel in ("Biodiesel", "Bioethanol"):
    for a in AMS10:
        G3_ANCHOR[(a, fuel)] = ceil[(a, fuel)].get(2025, 0.0)

AUDIT_YEARS = list(range(2025, 2061))
# post-delta RAS floor expression per (region, fuel); seeded with canon, then
# overwritten by whatever GROUP 2 / GROUP 3 author.
new_floor_ras: dict[tuple[str, str], str] = {
    (a, f): canon_key(f, RAS, a) for f in ("Biodiesel", "Bioethanol") for a in AMS10
}

# ================================================================= GROUP 2
# Indonesia bioethanol floor lowered to the team's E20 physical wall (R4).
ID_BE_OLD = canon_key("Bioethanol", RAS, "Indonesia")
ID_BE_NEW = "InterpFSY(2025, 0, 2050, 20)"
for scen in (ATS, RAS):
    add("G2", ams="Indonesia", branch=KEY_BRANCH["Bioethanol"],
        variable="Activity Level", expression=ID_BE_NEW, unit="Volume %",
        fuel="Bioethanol",
        source="USER RULING R4 (2026-07-22) accepting the bioenergy team's E20 "
               "physical wall; 2025 anchor = observed achieved 0.0% "
               "(blend_observed_panel.csv, USDA GAIN ID2025-0029 T7, 2015-2025)",
        note=f"SCENARIO-NARRATIVE CHANGE. Was: {ID_BE_OLD} (E50 by 2050). "
             "Volume % pass-through - NO energy conversion on this variable. "
             "ONE reversible row per scenario; revert by restoring the old "
             "expression. Endpoint 20 EQUALS the wall from 2050 on, so the "
             "Max() ceiling wrapper pins lb=ub in 2050/2055/2060.",
        src_csv="USER_RULING_R4", domain="blend_mandate",
        data_confidence="High", scenario=scen)
new_floor_ras[("Indonesia", "Bioethanol")] = ID_BE_NEW

# ================================================================= GROUP 3
# Uniform 2025 blend anchor across BAS / ATS / RAS (R5).
obs = read(os.path.join(TEAM, "blend_observed_panel.csv"))
obs_latest: dict[tuple[str, str], tuple[int, str, str]] = {}
for x in obs:
    a = ALIAS.get(x["ams"], x["ams"])
    if not x["achieved_vol_pct"].strip():
        continue
    y = int(x["year"])
    k = (a, x["fuel"])
    if k not in obs_latest or y > obs_latest[k][0]:
        obs_latest[k] = (y, x["achieved_vol_pct"], x["confidence"])

audit_g3 = []
for fuel in ("Biodiesel", "Bioethanol"):
    for a in AMS10:
        anchor = G3_ANCHOR[(a, fuel)]
        o = obs_latest.get((a, fuel))
        prov = (f"observed achieved {o[1]}% ({o[0]}, {o[2]} confidence)"
                if o else "NO observation in blend_observed_panel.csv -> 0.0")
        for scen in (BAS, ATS, RAS):
            if fuel == "Bioethanol" and a == "Indonesia" and scen in (ATS, RAS):
                audit_g3.append(dict(ams=a, fuel=fuel, scenario=scen,
                                     anchor_2025=fmt(anchor), provenance=prov,
                                     before=canon_key(fuel, scen, a),
                                     after="(owned by GROUP 2)", action="DEFERRED-TO-G2"))
                continue
            old = canon_key(fuel, scen, a)
            k, p = parse_anchors(old)
            if k == "other":
                block("G3", f"{a}/{fuel}/{scen}: unparseable canon expression {old!r}")
                continue
            nk, np_ = set_2025(k, p, anchor)
            new = render(nk, np_)
            same = all(abs((eval_series(k, p, y) or 0) - (eval_series(nk, np_, y) or 0)) < 1e-9
                       for y in AUDIT_YEARS)
            audit_g3.append(dict(ams=a, fuel=fuel, scenario=scen,
                                 anchor_2025=fmt(anchor), provenance=prov,
                                 before=old, after=new,
                                 action="NO-OP (skipped)" if same else "AUTHORED"))
            if same:
                continue
            add("G3", ams=a, branch=KEY_BRANCH[fuel], variable="Activity Level",
                expression=new, unit="Volume %", fuel=fuel,
                source="USER RULING R5 (2026-07-22) uniform 2025 start; anchor from "
                       "blend_ceiling_ramp.csv 2025 row (binding_reason="
                       "observed_achieved_floor) == blend_observed_panel.csv",
                note=f"2025 anchor := {fmt(anchor)} vol% ({prov}). Post-2025 "
                     f"trajectory PRESERVED verbatim. Was: {old}",
                src_csv="blend_observed_panel.csv", domain="blend_mandate",
                data_confidence="Medium", scenario=scen)
            if scen == RAS:
                new_floor_ras[(a, fuel)] = new

# ---- per-year ceiling-vs-floor audit (RAW ceiling, i.e. BEFORE the Max()
# wrapper) against BOTH the pre-delta canon floor and the post-delta floor.
inversions, inversions_post = [], []
for fuel in ("Biodiesel", "Bioethanol"):
    for a in AMS10:
        vol = ceil[(a, fuel)]
        if len(vol) != len(YEARS):
            continue
        ck, cp = "Interp", [(y, vol[y]) for y in YEARS]
        f_pre = parse_anchors(canon_key(fuel, RAS, a))
        f_post = parse_anchors(new_floor_ras[(a, fuel)])
        for y in AUDIT_YEARS:
            cv = eval_series(ck, cp, y)
            pre = eval_series(*f_pre, year=y) if f_pre[1] else 0.0
            post = eval_series(*f_post, year=y) if f_post[1] else 0.0
            ce = energy_pct(cv, fuel)
            fe_pre, fe_post = energy_pct(pre or 0.0, fuel), energy_pct(post or 0.0, fuel)
            i_pre, i_post = fe_pre - ce, fe_post - ce
            audit_cf.append(dict(
                ams=a, fuel=fuel, year=y,
                ceiling_vol_pct=fmt(cv),
                ceiling_energy_pct=fmt(ce),
                canon_floor_vol_pct=fmt(pre or 0),
                canon_floor_energy_pct=fmt(fe_pre),
                inversion_vs_canon_floor_energy_pp=fmt(i_pre),
                inverted_vs_canon="YES" if i_pre > 1e-9 else "",
                postdelta_floor_vol_pct=fmt(post or 0),
                postdelta_floor_energy_pct=fmt(fe_post),
                inversion_vs_postdelta_floor_energy_pp=fmt(i_post),
                inverted_vs_postdelta="YES" if i_post > 1e-9 else "",
                wrapped_ceiling_energy_pct=fmt(max(ce, fe_post))))
            if i_pre > 1e-9:
                inversions.append((a, fuel, y, round(i_pre, 3)))
            if i_post > 1e-9:
                inversions_post.append((a, fuel, y, round(i_post, 3)))

# ================================================================= GROUP 4
# Refinery Maximum Capacity, re-authored under the R7 Max() wrapper.
cap_rows = read(os.path.join(TEAM721, "biomass_supply_cap_rows.csv"))
LITE = {"All Biomass", "Anaerobic Digestion", "CO2 Utilization for Iron and Steel",
        "Production from Hydrogen", "Hydrogen"}
for x in cap_rows:
    leaf = x["branch"].rsplit("\\", 1)[-1]
    if x["variable"] != "Maximum Capacity":
        continue
    if leaf == "Cellulosic Rice Straw":
        continue
    if leaf in LITE:
        continue
    a = ALIAS.get(x["ams"], x["ams"])
    if a not in AMS10:
        block("G4", f"row for non-LEAP region {x['ams']!r} dropped")
        continue
    inner = clean_expr(x["expression"])
    add("G4", ams=a, branch=x["branch"], variable="Maximum Capacity",
        expression=f"Max(Exogenous Capacity, {inner})", unit=x["unit"],
        fuel=x["fuel"], source=x["source"],
        note="R7 wrapper: reference FIRST, numeric/Interp LAST (S11.2e). Prevents "
             "LEAP's 'Maximum capacity constraint is less than exogenous capacity' "
             "halt. Values are the team's, native unit, pass-through (no "
             "conversion). Original note: " + x["note"][:220],
        src_csv="biomass_supply_cap_rows.csv (20260721 handover)",
        domain="refining_capacity", data_confidence=x["data_confidence"],
        scenario=RAS)
block("G4", "Cellulosic Rice Straw x10 EXCLUDED - branch does not exist yet "
            "(row_disposition_20260721.csv: HOLD - pending structural create)")
block("G4", "5 lite-panel processes EXCLUDED by user ruling R1 (out of scope)")

# ================================================================= GROUP 5
# Refinery + blending Maximum Capacity Addition (build-rate limit).
br = read(os.path.join(TEAM, "build_rate_limit.csv"))
brate = {}
for x in br:
    brate[(ALIAS.get(x["ams"], x["ams"]), x["fuel"])] = x

# --- canon allocation shares (canon's OWN rule, not invented): the
# '* Interp(<per-feedstock>) / Interp(<total>)' idiom on Exogenous Capacity,
# canon comment "production capacity distributed between fuels according to
# shares of historical production".  Evaluated at 2023 (last canon anchor).
INTERPS = re.compile(r"Interp\s*\(([^)]*)\)")


def interp_at(body, year):
    nums = [float(z) for z in NUMPAIR.findall(body)]
    pts = [(int(nums[i]), nums[i + 1]) for i in range(0, len(nums) - 1, 2)]
    return eval_series("Interp", pts, year)


share: dict[tuple[str, str], float] = {}
for x in canon_t:
    if x["variable"] != "Exogenous Capacity" or x["scenario"] != RAS:
        continue
    bp = x["branch_path"]
    leaf = bp.rsplit("\\", 1)[-1]
    fam = ("Biodiesel" if r"Biodiesel Production" in bp
           else "Bioethanol" if r"Bioethanol Production" in bp else None)
    if fam is None or x["region"] not in AMS10:
        continue
    e = clean_expr(x["expression"])
    if e in ("0", "0.0", ""):
        share[(x["region"], leaf)] = 0.0
        continue
    ii = INTERPS.findall(e)
    if len(ii) >= 3 and "/" in e:
        num, den = interp_at(ii[-2], 2023), interp_at(ii[-1], 2023)
        share[(x["region"], leaf)] = (num / den) if den else 0.0
    else:
        share[(x["region"], leaf)] = 1.0

alloc_note = []
for fuel in ("Biodiesel", "Bioethanol"):
    for a in AMS10:
        tot = sum(share.get((a, leaf), 0.0) for _, leaf in REFINERY[fuel])
        alloc_note.append((a, fuel, tot,
                           {leaf: round(share.get((a, leaf), 0.0), 5)
                            for _, leaf in REFINERY[fuel]}))

# Group-4 accepted Maximum Capacity trajectory per (ams, process), in the
# process's NATIVE unit -> used to clamp the build-rate unroll so the level cap
# and the rate cap agree instead of over-determining each other.
g4_cap: dict[tuple[str, str], tuple] = {}
for x in cap_rows:
    leaf = x["branch"].rsplit("\\", 1)[-1]
    if x["variable"] == "Maximum Capacity" and leaf not in LITE:
        a = ALIAS.get(x["ams"], x["ams"])
        g4_cap[(a, leaf)] = parse_anchors(clean_expr(x["expression"]))

# Cross-check: the team allocated Maximum Capacity per process by FEEDSTOCK
# availability; canon allocates installed capacity by HISTORICAL PRODUCTION.
# Where they disagree the level cap sits below the existing fleet.
audit_alloc = []
for fuel in ("Biodiesel", "Bioethanol"):
    for a in AMS10:
        rec = brate.get((a, fuel))
        I0n = float(rec["installed_2023_mt_per_yr"]) if rec else 0.0
        for _, leaf in REFINERY[fuel]:
            capk = g4_cap.get((a, leaf))
            cap25 = eval_series(*capk, year=2025) if capk else None
            inst = I0n * share.get((a, leaf), 0.0) * MT_TO_NATIVE[fuel]
            if cap25 is None:
                continue
            audit_alloc.append(dict(
                ams=a, fuel=fuel, process=leaf, unit=REFINERY_UNIT[fuel],
                team_max_capacity_2025=fmt(cap25, 5),
                canon_share_2023=fmt(share.get((a, leaf), 0.0), 5),
                canon_implied_installed_2023=fmt(inst, 5),
                conflict="CAP BELOW EXISTING FLEET" if inst - cap25 > 1e-6 else ""))

BUILD_YEARS = list(range(2025, 2061))
for fuel in ("Biodiesel", "Bioethanol"):
    for a in AMS10:
        rec = brate.get((a, fuel))
        if rec is None:
            block("G5", f"no build_rate_limit row for {a}/{fuel}")
            continue
        I0n = float(rec["installed_2023_mt_per_yr"])
        alpha = float(rec["alpha_per_yr"])
        floor = float(rec["one_train_floor_mt_per_yr"])
        fy_nat = int(rec["first_feasible_year"])
        for branch, leaf in REFINERY[fuel]:
            s = share.get((a, leaf), 0.0)
            I0 = I0n * s
            # basis rule (the team's own): a process with zero installed base in
            # this region is greenfield -> 2028 lead time, not the national
            # brownfield 2026.
            fy = fy_nat if I0 > 0 else max(fy_nat, 2028)
            capk = g4_cap.get((a, leaf))
            inst, pts, clamped = I0, [], 0
            for y in BUILD_YEARS:
                addn = 0.0 if y < fy else max(floor, alpha * inst)
                if capk:
                    lvl = eval_series(*capk, year=y)
                    if lvl is not None:
                        head = max(0.0, lvl / MT_TO_NATIVE[fuel] - inst)
                        if addn > head:
                            addn, clamped = head, clamped + 1
                inst += addn
                pts.append((y, addn * MT_TO_NATIVE[fuel]))
            expr = "Interp(" + ", ".join(f"{y}, {fmt(v, 5)}" for y, v in pts) + ")"
            add("G5", ams=a, branch=branch, variable="Maximum Capacity Addition",
                expression=expr, unit=REFINERY_UNIT[fuel], fuel=fuel,
                source="build_rate_limit.csv (bioenergy team 20260722), recursion "
                       "PRE-SOLVED OFFLINE; allocation across processes uses CANON's "
                       "own share-of-historical-production idiom (Exogenous Capacity "
                       "'* Interp(<feedstock>) / Interp(<total>)', evaluated at 2023)",
                note=f"installed_2023(national)={I0n} Mt/yr; canon share({leaf})="
                     f"{s:.5f} -> installed_2023(process)={I0:.5f} Mt/yr; "
                     f"alpha={alpha}; one_train_floor={floor} Mt/yr; "
                     f"first_feasible_year={fy} "
                     f"({'national brownfield' if I0 > 0 else 'greenfield (zero installed base)'}). "
                     f"Mt/yr -> {REFINERY_UNIT[fuel]} x{MT_TO_NATIVE[fuel]}. "
                     "Pure numerics in Interp() - no Max(), so S11.2e "
                     "numeric-first-parsed-as-year CANNOT fire. "
                     f"Unroll CLAMPED against the GROUP 4 accepted Maximum "
                     f"Capacity trajectory in {clamped}/{len(BUILD_YEARS)} years "
                     "so the level cap and the rate cap agree instead of "
                     "over-determining each other.",
                src_csv="build_rate_limit.csv", domain="refining_buildrate",
                data_confidence="Low", scenario=RAS)

# blending build rate (R6: replace 'Unlimited')
for fuel in ("Biodiesel", "Bioethanol"):
    for a in AMS10:
        add("G5", ams=a, branch=BLEND_BRANCH[fuel],
            variable="Maximum Capacity Addition", expression=BLEND_MAXCAPADD_NUM,
            unit="Megawatt", fuel=fuel,
            source="USER RULING R6 (nothing stays Unlimited in scope)",
            note=f"Was 'Unlimited' (canon ALL (12 regions), RAS). UPPER bound -> "
                 f"finite. {BLEND_MAXCAPADD_NUM} MW/yr = 10% of the "
                 f"{BLEND_MAXCAP_NUM} MW level cap per year, i.e. the whole "
                 "blending terminal fleet can be rebuilt in 10 years. "
                 "Blending is a pass-through pseudo-tech (Process Efficiency=100); "
                 "the cap exists to stop a free unbounded build, not to bind.",
            src_csv="USER_RULING_R6", domain="blend_capacity",
            data_confidence="Low", scenario=RAS)
block("G5", "Diesel Blending\\Processes\\Diesel and Gasoline Blending\\Processes\\"
            "Gasoline Maximum Capacity Addition NOT authored - task scoped this "
            "row group to the 2 biofuel blending processes. OPEN SYMMETRY ITEM: "
            "leaving the fossil siblings at 'Unlimited' while rate-limiting the "
            "biofuel siblings biases the blend split. Needs a ruling.")

# ================================================================= GROUP 6
# Kill every remaining 'Unlimited' in scope.
audit_unl = []


def note_unl(branch, variable, unit, scen, region, direction, disposition):
    audit_unl.append(dict(branch=branch, variable=variable, unit=unit,
                          scenario=scen, region=region,
                          bound_direction=direction, disposition=disposition))


IN_SCOPE_T = {b for f in REFINERY for b, _ in REFINERY[f]} | {b for b, _ in BLEND_PSEUDO}
for x in canon_t:
    if x["branch_path"] not in IN_SCOPE_T or "Unlimited" not in x["expression"]:
        continue
    u = (x["scale"] + " " + x["units"]).strip()
    v, bp, sc, rg = x["variable"], x["branch_path"], x["scenario"], x["region"]
    if v == "Exogenous Capacity":
        note_unl(bp, v, u, sc, rg, "LOWER (-> NEMO ResidualCapacity)",
                 f"-> {EC_FLOOR} (finite-but-large; NEVER 0 - p9 burn 2026-05-12)")
    elif v == "Maximum Capacity Addition":
        note_unl(bp, v, u, sc, rg, "UPPER", "-> GROUP 5 build-rate Interp / finite MW")
    elif v == "Maximum Production":
        note_unl(bp, v, u, sc, rg, "UPPER", f"-> {GJ_CAP} GJ")
    elif v == "Maximum Capacity":
        note_unl(bp, v, u, sc, rg, "UPPER",
                 "-> GROUP 4 Max(Exogenous Capacity, Interp(...))"
                 if bp not in {b for b, _ in BLEND_PSEUDO}
                 else f"-> Max(Exogenous Capacity[MW], {BLEND_MAXCAP_NUM})")
    else:
        note_unl(bp, v, u, sc, rg, "?", "UNCLASSIFIED - review")

# 6a. Exogenous Capacity on the 4 blending pseudo-techs, all 4 scenarios.
for branch, kind in BLEND_PSEUDO:
    fl = "Biodiesel" if "Biodiesel" in branch else ("Bioethanol" if "Ethanol" in branch else "")
    for scen in (CA, BAS, ATS, RAS):
        for a in AMS10:
            add("G6", ams=a, branch=branch, variable="Exogenous Capacity",
                expression=EC_FLOOR, unit="Megawatt", fuel=fl,
                source="USER RULING R6 (Unlimited on a LOWER bound is the 1.0e+12 "
                       "forced-floor trap, CLAUDE.md S A.11)",
                note="Was 'Unlimited' -> exports as ResidualCapacity 1.0e+12, a "
                     "FORCED FLOOR. Replaced with finite-but-large "
                     f"{EC_FLOOR} MW. NEVER 0: on 2026-05-12 EC=0 on these same 4 "
                     "pseudo-techs took primal infeasibility 24k -> 4.6M (190x "
                     f"worse, the p9 burn). All 4 pseudo-techs are moved together "
                     f"(this one is the {kind} leg) - an asymmetric change would "
                     "distort the PercentShare blend split.",
                src_csv="USER_RULING_R6", domain="blend_capacity",
                data_confidence="Low", scenario=scen)

# 6b. Maximum Capacity on the 2 biofuel blending pseudo-techs (RAS).
for fuel in ("Biodiesel", "Bioethanol"):
    for a in AMS10:
        add("G6", ams=a, branch=BLEND_BRANCH[fuel], variable="Maximum Capacity",
            expression=f"Max(Exogenous Capacity[MW], {BLEND_MAXCAP_NUM})",
            unit="Megawatt", fuel=fuel,
            source="USER RULING R6 + R7 house idiom",
            note="Was 'Unlimited' (canon ALL (12 regions), RAS). UPPER bound. "
                 "R7 pattern, reference FIRST / numeric LAST (S11.2e). The Max() "
                 "guarantees the cap can never fall below the Exogenous Capacity "
                 f"floor authored in 6a ({EC_FLOOR} MW), so LEAP's 'Maximum "
                 "capacity constraint is less than exogenous capacity' halt "
                 "cannot fire. [MW] unit tag is the calc-proven canon form "
                 "(S11.2e Max(Exogenous Capacity[MW], 1874.0)).",
            src_csv="USER_RULING_R6", domain="blend_capacity",
            data_confidence="Low", scenario=RAS)

# 6c. Maximum Production on the 7 refineries + 2 biofuel blending (RAS).
for fuel in ("Biodiesel", "Bioethanol"):
    for branch, leaf in REFINERY[fuel] + [(BLEND_BRANCH[fuel], "blending")]:
        for a in AMS10:
            add("G6", ams=a, branch=branch, variable="Maximum Production",
                expression=GJ_CAP, unit="Gigajoule", fuel=fuel,
                source="USER RULING R6",
                note="Was 'Unlimited' (canon ALL (12 regions), RAS). UPPER bound "
                     f"-> {GJ_CAP} GJ = 10,000 PJ: generous (roughly a third of "
                     "total ASEAN primary energy supply, so non-binding against "
                     "any plausible national biofuel output) yet 100x below the "
                     "1.0e+12 export sentinel that pollutes CPLEX conditioning "
                     "(CLAUDE.md S A.11 / S11.2d). Capacity is the real bind "
                     "(Maximum Capacity, groups 4/6b).",
                src_csv="USER_RULING_R6", domain="refining_capacity",
                data_confidence="Low", scenario=RAS)

# 6d. Resources: Maximum Imports = Unlimited on Corn / Molasses / POME (RAS).
res_unl = defaultdict(list)
for x in canon_r:
    leaf = x["branch_path"].rsplit("\\", 1)[-1]
    if leaf in FEEDSTOCKS and "Unlimited" in x["expression"]:
        u = (x["scale"] + " " + x["units"]).strip()
        res_unl[(leaf, x["variable"], u, x["scenario"])].append(x["region"])

for (leaf, var, u, scen), regs in sorted(res_unl.items()):
    scoped = [r for r in regs if r in AMS10] or \
             (AMS10 if any(r.startswith("ALL ") for r in regs) else [])
    outer = sorted(set(regs) - set(AMS10))
    if var == "Maximum Imports" and scoped:
        note_unl(r"Resources\Primary\\" + leaf, var, u, scen, ", ".join(regs),
                 "UPPER", f"-> {GJ_CAP} GJ (10 AMS)")
        for a in scoped:
            add("G6", ams=a, branch=r"Resources\Primary" + "\\" + leaf,
                variable="Maximum Imports", expression=GJ_CAP, unit="Gigajoule",
                fuel=leaf, source="USER RULING R6",
                note="Was 'Unlimited' (canon ALL (12 regions), RAS). UPPER bound. "
                     "Unlimited on an import cap is the S11.2d silent-parse-failure "
                     "class: some AMS export it as missing/zero, un-capping the "
                     f"chain from the other direction. {GJ_CAP} GJ is generous and "
                     "finite.",
                src_csv="USER_RULING_R6", domain="feedstock_supply",
                data_confidence="Low", scenario=RAS)
    elif var == "Maximum Production":
        if scen == RAS:
            note_unl(r"Resources\Primary\\" + leaf, var, u, scen, ", ".join(regs),
                     "UPPER", "OUT OF SCOPE - only Base Template (not a real "
                              "region, S11.1) and Timor Leste (disabled in calc, "
                              "--exclude-timor-leste). NOT authored.")
        else:
            note_unl(r"Resources\Primary\\" + leaf, var, u, scen, ", ".join(regs),
                     "UPPER", "-> copy the region's own RAS expression (canon-sourced)")

# 6e. Corn Maximum Production = Unlimited in ATS/BAS/CA -> copy canon's RAS value.
corn_ras = {}
for x in canon_r:
    if (x["branch_path"].rsplit("\\", 1)[-1] == "Corn"
            and x["variable"] == "Maximum Production" and x["scenario"] == RAS
            and x["region"] in AMS10):
        corn_ras[x["region"]] = clean_expr(x["expression"])
for scen in (ATS, BAS, CA):
    for a in AMS10:
        e = corn_ras.get(a)
        if not e or "Unlimited" in e:
            block("G6", f"Corn Maximum Production {a}/{scen}: canon RAS value "
                        f"missing or itself Unlimited ({e!r}) - not authored")
            continue
        add("G6", ams=a, branch=r"Resources\Primary\Corn",
            variable="Maximum Production", expression=e, unit="Metric Tonne",
            fuel="Corn", source="canon RAS per-region expression "
                                "(current_expressions_resources_4scenarios.csv, "
                                "v0.67 - VALUE may be stale vs live v0.76+)",
            note="Was 'Unlimited' (canon ALL (12 regions)) in this scenario while "
                 "RAS already carries a finite per-region cap. UPPER bound. The "
                 "physical crop-supply potential is scenario-invariant, so the "
                 "minimal canon-derived fix is to mirror RAS. No new number "
                 "invented.",
            src_csv="USER_RULING_R6", domain="feedstock_supply",
            data_confidence="Medium", scenario=scen)

# ================================================================= GROUP 7
# Feedstock resources: confirm Maximum Production has a companion cost row.
g7_report = []
for leaf in FEEDSTOCKS:
    have = defaultdict(set)
    for x in canon_r:
        if x["branch_path"].rsplit("\\", 1)[-1] == leaf:
            have[x["variable"]].add(x["region"])
    mp = have.get("Maximum Production", set())
    pc = have.get("Production Cost", set())
    mi = have.get("Maximum Imports", set())
    ic = have.get("Import Cost", set())

    def cov(s):
        return "ALL (12 regions)" if any(r.startswith("ALL ") for r in s) else \
               f"{len(s & set(AMS10))}/10 AMS"
    gap = []
    if mp and not pc:
        gap.append("Maximum Production WITHOUT Production Cost")
    if mi and not ic:
        gap.append("Maximum Imports WITHOUT Import Cost")
    g7_report.append((leaf, cov(mp), cov(pc), cov(mi), cov(ic),
                      "; ".join(gap) or "OK - every cap has its companion cost row"))

# ================================================================= WRITE

os.makedirs(HERE, exist_ok=True)
with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=COLS)
    w.writeheader()
    w.writerows(rows)


def dump(name, recs):
    if not recs:
        return
    p = os.path.join(HERE, name)
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(recs[0].keys()))
        w.writeheader()
        w.writerows(recs)


dump("_audit_ceiling_vs_floor.csv", audit_cf)
dump("_audit_unlimited.csv", audit_unl)
dump("_audit_group3_before_after.csv", audit_g3)
dump("_audit_maxcap_vs_installed.csv", audit_alloc)

print("rows per group:", dict(sorted(counts.items())))
print("total rows:", len(rows))
print("blocked:")
for g, r in blocked:
    print("  ", g, "-", r)
print("\nworked example (Group 1): Malaysia Biodiesel 2050 volume 50.0% ->",
      f"{energy_pct(50.0, 'Biodiesel'):.4f} energy%")
print("reference: B7", fmt(energy_pct(7, "Biodiesel")), "B20",
      fmt(energy_pct(20, "Biodiesel")), "B50", fmt(energy_pct(50, "Biodiesel")),
      "E10", fmt(energy_pct(10, "Bioethanol")), "E20", fmt(energy_pct(20, "Bioethanol")))
for label, inv in (("PRE-delta (canon floor)", inversions),
                   ("POST-delta (G2+G3 floor)", inversions_post)):
    print(f"\nceiling<floor cells, {label}, ramp reading: {len(inv)}")
    seen = set()
    for a, fu, y, d in inv:
        if (a, fu) not in seen:
            seen.add((a, fu))
            yrs = [i for i in inv if (i[0], i[1]) == (a, fu)]
            print(f"   {a}/{fu}: {len(yrs)} yr(s) {yrs[0][2]}-{yrs[-1][2]}, "
                  f"max {max(i[3] for i in yrs)} energy-pp")
print("\nallocation shares (canon rule, 2023):")
for a, fu, tot, d in alloc_note:
    if tot > 0:
        print(f"   {a}/{fu}: sum={tot:.5f} {d}")
print("\nteam Maximum Capacity BELOW the canon-implied existing fleet:")
for x in audit_alloc:
    if x["conflict"]:
        print(f"   {x['ams']}/{x['process']}: cap2025={x['team_max_capacity_2025']} "
              f"< installed2023={x['canon_implied_installed_2023']} {x['unit']}")

print("\nGROUP 7 feedstock cap/cost pairing:")
for r in g7_report:
    print("   ", " | ".join(r))
