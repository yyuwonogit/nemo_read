"""Compute the three APAEC tracking metrics, ASEAN-aggregate, per scenario.

  1. RE share of installed power capacity  (power capacity result)   target 45% @2030
  2. RE share of TPES                        (Primary Supply result)  target 35% @2030
  3. Energy intensity reduction vs 2005      (TPES / Real GDP PPP)    target 40% @2030

Outputs result/20260709/apaec_metrics.json for the visualization + prints a
sanity table. RE classifications and the GDP method are surfaced for review.
"""
import csv, re, json
from pathlib import Path
from collections import defaultdict
import openpyxl

HERE = Path(__file__).resolve().parent
MB = HERE.parents[1] / "mailbox" / "20260709"
AMS10 = ["Brunei", "Cambodia", "Indonesia", "Laos", "Malaysia", "Myanmar",
         "Philippines", "Singapore", "Thailand", "Vietnam"]
SCEN = ["Baseline Simulation", "AMS Target Scenario", "Regional Aspiration Scenario"]
YEARS = [2010, 2020, 2030, 2040, 2050, 2060]

# ---------- 1. RE share of installed capacity ----------
def is_re_power(t):
    s = t.lower()
    if any(x in s for x in ("pumped hydro", "batter", "caes", "flow batter")):
        return None  # storage: exclude from numerator AND denominator
    if any(x in s for x in ("unmet load", "direct air capture", "co2 utilization")):
        return None  # not generation
    if "hydrogen" in s or "h2 " in s or s.startswith("h2"):
        return False  # H2 fuel cell = non-RE secondary carrier
    if "nuclear" in s:            # user directive 2026-07-09: count nuclear as RE
        return True
    if any(x in s for x in ("solar", "wind", "geothermal", "biomass", "biogas",
                            "bagasse", "waste", "tidal", "wave", "bioenergy")):
        return True
    if "hydro" in s:      # large/small hydro (pumped already excluded above)
        return True
    return False          # coal, gas, diesel, fuel oil, oil, nuclear

cap_re, cap_tot = defaultdict(float), defaultdict(float)
cap_techs = {}
for r in csv.DictReader(open(HERE / "aeo9_v0.71_supply_power_tidy.csv", encoding="utf-8")):
    if r["variable"] != "Capacity" or r["region"] not in AMS10:
        continue
    if r["branch_leaf"] == "Total":     # LEAP export sums row — not a technology
        continue
    cls = is_re_power(r["branch_leaf"])
    cap_techs[r["branch_leaf"]] = cls
    if cls is None:
        continue
    k = (r["scenario"], int(r["year"]))
    v = float(r["value"])
    cap_tot[k] += v
    if cls:
        cap_re[k] += v
re_cap_share = {s: {y: 100 * cap_re[(s, y)] / cap_tot[(s, y)] if cap_tot[(s, y)] else 0
                    for y in YEARS} for s in SCEN}

# ---------- 2. RE share of TPES (Primary Supply, Primary section) ----------
RE_PRIMARY = {"Bagasse", "Biomass", "Cassava", "Coconut Oil", "Geothermal",
              "Large Hydro", "Small Hydro", "Molasses", "Municipal Solid Waste",
              "Palm Oil", "Solar", "Sugarcane", "Tidal", "Wave", "Wind", "Wood",
              "Biogas", "Nuclear"}   # nuclear counted as RE (user 2026-07-09)
NONRE_PRIMARY = {"Coal Anthracite", "Coal Bituminous", "Coal Lignite",
                 "Coal Sub bituminous", "Coal Unspecified", "Crude Oil",
                 "Natural Gas"}
SHEET = {"Baseline Simulation": "Primary BAS", "AMS Target Scenario": "Primary ATS",
         "Regional Aspiration Scenario": "Primary Supply RAS"}
wb = openpyxl.load_workbook(MB / "v_0.71 Resources Result.xlsx", read_only=True, data_only=True)
tpes_re, tpes_tot = defaultdict(float), defaultdict(float)
prim_fuel_seen = set()
for scen, sheet in SHEET.items():
    rows = list(wb[sheet].iter_rows(values_only=True))
    hdr = rows[5]
    colmap = {}
    for j, c in enumerate(hdr):
        m = re.match(r"^(.+?)\s+(\d{4})$", str(c or "").strip())
        if m and m.group(1).strip() in AMS10 and int(m.group(2)) in YEARS:
            colmap[j] = (m.group(1).strip(), int(m.group(2)))
    in_primary = False
    for r in rows[6:]:
        b = r[0]
        if b is None or str(b).strip() == "":
            continue
        s = str(b); depth = (len(s) - len(s.lstrip())) // 3; name = s.strip()
        if depth == 0:
            in_primary = (name == "Primary")
            continue
        if not in_primary or depth != 1:
            continue
        prim_fuel_seen.add(name)
        re_fuel = name in RE_PRIMARY
        for j, (region, year) in colmap.items():
            v = r[j]
            if v in (None, "") or (isinstance(v, str) and not v.strip()):
                continue
            try: val = float(v)
            except (TypeError, ValueError): continue
            k = (scen, year)
            tpes_tot[k] += val
            if re_fuel:
                tpes_re[k] += val
re_tpes_share = {s: {y: 100 * tpes_re[(s, y)] / tpes_tot[(s, y)] if tpes_tot[(s, y)] else 0
                     for y in YEARS} for s in SCEN}
# TPES total (EJ) per scenario/year, + back-interp 2005 for the EI baseline
tpes_ej = {s: {y: tpes_tot[(s, y)] for y in YEARS} for s in SCEN}
for s in SCEN:  # linear extrapolation 2010->2020 back to 2005
    a, b = tpes_ej[s][2010], tpes_ej[s][2020]
    tpes_ej[s][2005] = a - (b - a) * (2010 - 2005) / (2020 - 2010)

# ---------- 3. Energy intensity vs 2005 ----------
# GDP structures (per country): (a) most = If(Year<=2050, Interp(2005..2050
# absolute), PrevYearValue*(V2050/V2049)); (b) Indonesia = CA Interp(2005..2024)
# + scenario Growth(rate%) compounding. Handle both; sci-notation aware.
NUM = r"-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?"
def first_interp_pairs(expr):
    i = expr.find("Interp(")
    d, j = 0, i + 6
    while j < len(expr):
        if expr[j] == "(": d += 1
        elif expr[j] == ")":
            d -= 1
            if d == 0: break
        j += 1
    nums = [float(x) for x in re.findall(NUM, expr[i + 7:j])]
    return list(zip([int(y) for y in nums[0::2]], nums[1::2]))
def interp(pairs, y):
    if y <= pairs[0][0]: return pairs[0][1]
    if y >= pairs[-1][0]: return pairs[-1][1]
    for (y1, v1), (y2, v2) in zip(pairs, pairs[1:]):
        if y1 <= y <= y2:
            return v1 + (v2 - v1) * (y - y1) / (y2 - y1)
gdp_expr = defaultdict(dict)
kf = HERE.parents[1] / "inject/keys/structure_handover_20260703/current_expressions_keys_4scenarios.csv"
rdr = csv.DictReader(open(kf, encoding="utf-8-sig"))
fn = {k.lower().replace(" ", "_"): k for k in rdr.fieldnames}
for r in rdr:
    if r[fn["branch_path"]].split(chr(92))[-1] == "Real GDP PPP" and r[fn["region"]] in AMS10:
        gdp_expr[r[fn["region"]]][r[fn["scenario"]]] = r[fn["expression"]].split("?")[0]

def gdp_value(region, scen, year):
    expr = gdp_expr[region][scen]
    if "Growth(" in expr:                       # compound from CA history base
        grow = first_interp_pairs(expr)         # annual growth %
        ca = first_interp_pairs(gdp_expr[region]["Current Accounts"])
        base_yr, val = ca[-1]
        if year <= base_yr:
            return interp(ca, year)
        for y in range(base_yr + 1, year + 1):
            val *= (1 + interp(grow, y) / 100)
        return val
    pairs = first_interp_pairs(expr)            # absolute Interp 2005..2050
    last = pairs[-1][0]
    if year <= last:
        return interp(pairs, year)
    ratio = interp(pairs, last) / interp(pairs, last - 1)   # 2049->2050 tail growth
    return interp(pairs, last) * ratio ** (year - last)

gdp_asean = {s: {y: sum(gdp_value(r, s, y) for r in AMS10) for y in [2005] + YEARS}
             for s in SCEN}
# EI = TPES / GDP ; reduction from 2005 (2005 EI shared history, use each scen's path)
ei = {s: {y: tpes_ej[s][y] / gdp_asean[s][y] for y in [2005] + YEARS} for s in SCEN}
ei_reduction = {s: {y: 100 * (1 - ei[s][y] / ei[s][2005]) for y in [2005] + YEARS}
                for s in SCEN}

# ---------- output ----------
SHORT = {"Baseline Simulation": "BAS", "AMS Target Scenario": "ATS",
         "Regional Aspiration Scenario": "RAS"}
out = {
    "re_capacity_share": {SHORT[s]: re_cap_share[s] for s in SCEN},
    "re_tpes_share": {SHORT[s]: re_tpes_share[s] for s in SCEN},
    "ei_reduction_2005": {SHORT[s]: ei_reduction[s] for s in SCEN},
    "targets": {"re_capacity": {"year": 2030, "value": 45},
                "re_tpes": {"year": 2030, "value": 35},
                "ei_reduction": {"year": 2030, "value": 40}},
    "years": YEARS, "years_ei": [2005] + YEARS,
}
json.dump(out, open(HERE / "apaec_metrics.json", "w"), indent=2)

print("=== power capacity classification ===")
for t, c in sorted(cap_techs.items()):
    tag = "RE" if c else ("storage/excl" if c is None else "non-RE")
    if c or c is None: print(f"  {tag:<12} {t}")
print("  non-RE:", sorted(t for t, c in cap_techs.items() if c is False))
print("\n=== primary fuels seen (classify) ===")
print("  RE   :", sorted(f for f in prim_fuel_seen if f in RE_PRIMARY))
print("  nonRE:", sorted(f for f in prim_fuel_seen if f in NONRE_PRIMARY))
print("  UNCLASSIFIED:", sorted(f for f in prim_fuel_seen if f not in RE_PRIMARY and f not in NONRE_PRIMARY) or "none")
print("\n=== METRICS (ASEAN aggregate) ===")
for title, d, tgt in [("RE capacity %", re_cap_share, "45@2030"),
                      ("RE TPES %", re_tpes_share, "35@2030"),
                      ("EI reduction vs2005 %", ei_reduction, "40@2030")]:
    print(f"\n{title}  (target {tgt})")
    print("  scen  " + "".join(f"{y:>8}" for y in YEARS))
    for s in SCEN:
        print(f"  {SHORT[s]:<5} " + "".join(f"{d[s][y]:>8.1f}" for y in YEARS))
print(f"\nGDP ASEAN 2005={gdp_asean['Regional Aspiration Scenario'][2005]:,.0f}  "
      f"2030(RAS)={gdp_asean['Regional Aspiration Scenario'][2030]:,.0f}  "
      f"2060(RAS)={gdp_asean['Regional Aspiration Scenario'][2060]:,.0f} (Million 2021 USD PPP)")
print(f"TPES ASEAN 2005(RAS back-interp)={tpes_ej['Regional Aspiration Scenario'][2005]:.2f} EJ  "
      f"2030={tpes_ej['Regional Aspiration Scenario'][2030]:.2f}  2060={tpes_ej['Regional Aspiration Scenario'][2060]:.2f}")
