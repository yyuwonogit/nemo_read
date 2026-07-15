"""Build the residential Phase-2 clean canonical for aeo9_v0.73 inject.

Converts the three WIDE author files (AC, Fridge, Lighting) to LEAP-ready
long rows and merges the three already-canon-format files. Canon-verified
against inject/residential/structure_handover_20260703/.

Structure rulings applied (see outbox/20260716/MD2):
  - AC/Fridge driver data -> Key\\Residential\\<appliance>\\{Percent Ownership,
    Size_Share, Efficiency_Share\\<Size>_<eff>, Useful_EI\\<Size>}; the demand
    leaf Activity Level is re-wired to reference Efficiency_Share (undo the
    optimizer Data() overwrite).
  - Ownership is a %-of-household saturation (LEAP divides by 100): AC 282
    = 282% = 2.82 units/HH, Fridge 87.9 = 87.9% = 0.879/HH. Inject author
    values AS-IS (no scaling) — the live model's AC 2.82 is a pre-existing
    100x error this corrects.
  - Useful EI on the SIZE node key; Efficiency on the leaf (all scen).
  - RAS-only device panel: Capital Cost(=price_usd), Unit Capacity, Exogenous
    Devices(x1000), Lifetime(15 AC/12 fridge), Interest Rate(=DiscountRate).
  - BAS/ATS: simple leaf Demand Cost (annualized capital); no FEI (LEAP derives).
  - Lighting -> tech leaf Activity Level(share) + Bulb Wattage; no FEI.
"""
import csv, os
os.chdir(os.path.dirname(os.path.abspath(__file__)) + r"\..\..\..")  # repo root
DROP = r"C:\Users\ThinkPad\AppData\Local\Temp\claude\c--Users-ThinkPad-Desktop-Py-YY-NEMO-read\e5eed2c4-745e-4bab-a4ab-809cea7b2258\scratchpad\res_inject\LEAP Input"
OUT = r"inject/residential/20260716/residential_canonical_20260716.csv"
bs = chr(92)

REGION = {"Brunei Darussalam": "Brunei", "Lao PDR": "Laos", "Viet Nam": "Vietnam"}
def reg(c): return REGION.get(c, c)
SCEN = {"BAS": "Baseline Simulation", "ATS": "AMS Target Scenario", "RAS": "Regional Aspiration Scenario"}
EFFK = {"High_eff": "High", "Mid_eff": "Mid", "Low_eff": "Low"}
COLS = ["ams","branch","variable","expression","unit","fuel","source","note","src_csv","data_confidence","scenario"]

def interp(year_val):
    pairs = sorted((int(y), v) for y, v in year_val.items())
    body = ", ".join(f"{y}, {v}" for y, v in pairs)
    return f"Interp({body})"

def rows_from(path):
    return list(csv.DictReader(open(os.path.join(DROP, path), encoding="utf-8-sig")))

out = []
def emit(ams, branch, variable, expr, unit, scenario="", src="", note=""):
    out.append({"ams": ams, "branch": branch, "variable": variable, "expression": expr,
                "unit": unit, "fuel": "", "source": src, "note": note,
                "src_csv": "residential_leap_inject_20260715", "data_confidence": "Medium",
                "scenario": scenario})

def build_device(appliance, keyname, inject_csv, exo_csv, own_col, own_div, dcost_col, lifetime):
    """appliance: 'Air Conditioning_'/'Refrigeration_'; keyname: 'Air Conditioning'/'Refrigeration'."""
    KP = f"Key{bs}Residential{bs}{keyname}"
    LEAF = f"Demand{bs}Residential{bs}Projections{bs}{appliance}"
    rows = rows_from(inject_csv)
    # collectors keyed appropriately
    own = {}                       # country -> {year: val}
    size = {}                      # (country,size) -> {year: val}
    ueis = {}                      # (country,size) -> {year: val}
    effs = {}                      # (country,size,eff,scen) -> {year: val}
    eff_pct = {}                   # (country,size,eff) -> {year: val}   (Efficiency, invariant)
    cap = {}                       # (country,size,eff) -> {year: val}   RAS price
    ucap = {}                      # (country,size,eff) -> {year: val}   RAS unit capacity
    dcost = {}                     # (country,size,eff,scen) -> {year: val}  BAS/ATS
    for r in rows:
        c = reg(r["Country"]); y = r["Year"]; s = SCEN[r["Scenario"]]
        S = r["Size_group"]; E = r["Efficiency_level"]; EA = EFFK[E]
        own.setdefault(c, {})[y] = round(float(r[own_col]) / own_div, 6)
        size.setdefault((c, S), {})[y] = float(r["size_share_pct"])
        ueis.setdefault((c, S), {})[y] = float(r["useful_energy_intensity_toe"])
        effs.setdefault((c, S, EA, s), {})[y] = float(r["eff_share_pct"])
        eff_pct.setdefault((c, S, E), {})[y] = float(r["efficiency_pct"])
        if r["Scenario"] == "RAS":
            cap.setdefault((c, S, E), {})[y] = float(r["price_usd"])
            ucap.setdefault((c, S, E), {})[y] = float(r["unit_capacity_kw"])
        else:  # BAS/ATS -> simple Demand Cost = annualized capital
            dcost.setdefault((c, S, E, s), {})[y] = float(r[dcost_col])
    # --- Keys ---
    for c, yv in own.items():
        emit(c, f"{KP}{bs}Percent Ownership", "Activity Level", interp(yv), "%")
    for (c, S), yv in size.items():
        emit(c, f"{KP}{bs}Size_Share{bs}{S}", "Activity Level", interp(yv), "%")
    for (c, S), yv in ueis.items():
        emit(c, f"{KP}{bs}Useful_EI{bs}{S}", "Activity Level", interp(yv), "Tonnes of Oil Equivalent")
    for (c, S, EA, s), yv in effs.items():
        emit(c, f"{KP}{bs}Efficiency_Share{bs}{S}_{EA}", "Activity Level", interp(yv), "%", scenario=s)
    # --- Demand leaves ---
    for (c, S, E), yv in eff_pct.items():
        EA = EFFK[E]
        leaf = f"{LEAF}{bs}{S}{bs}{E}"
        emit(c, leaf, "Efficiency", interp(yv), "Efficiency")
        # re-wire leaf Activity Level to the Efficiency_Share key (undo optimizer Data())
        emit(c, leaf, "Activity Level", f"{KP}{bs}Efficiency_Share{bs}{S}_{EA}[%]", "%")
    for (c, S, E), yv in cap.items():
        leaf = f"{LEAF}{bs}{S}{bs}{E}"
        emit(c, leaf, "Capital Cost", interp(yv), "U.S. Dollar", scenario="Regional Aspiration Scenario")
        emit(c, leaf, "Lifetime", str(lifetime), "Years", scenario="Regional Aspiration Scenario")
        emit(c, leaf, "Interest Rate", "DiscountRate", "Percent", scenario="Regional Aspiration Scenario")
    for (c, S, E), yv in ucap.items():
        emit(c, f"{LEAF}{bs}{S}{bs}{E}", "Unit Capacity", interp(yv), "Kilowatt", scenario="Regional Aspiration Scenario")
    for (c, S, E, s), yv in dcost.items():
        emit(c, f"{LEAF}{bs}{S}{bs}{E}", "Demand Cost", interp(yv), "2020 USD", scenario=s)
    # Exogenous Devices (RAS) from exo file, x1000
    exo = {}
    for r in rows_from(exo_csv):
        c = reg(r["Country"]); exo.setdefault((c, r["Size_group"], r["Efficiency_level"]), {})[r["Year"]] = round(float(r["device_thousand"]) * 1000, 3)
    for (c, S, E), yv in exo.items():
        emit(c, f"{LEAF}{bs}{S}{bs}{E}", "Exogenous Devices", interp(yv), "Device", scenario="Regional Aspiration Scenario")

build_device("Air Conditioning_", "Air Conditioning", "ac_leap_inject.csv", "ac_exo_device.csv",
             own_col="units_per_hh_parent", own_div=1.0, dcost_col="annualized_capital_usd", lifetime=15)
build_device("Refrigeration_", "Refrigeration", "fridge_leap_inject.csv", "fridge_exo_device.csv",
             own_col="ownership_parent_pct", own_div=1.0, dcost_col="annualized_capital_usd", lifetime=12)

# --- Lighting ---
LIT = f"Demand{bs}Residential{bs}Projections{bs}Lighting{bs}Electricity"
litshare = {}
for r in rows_from("lighting_tech_shares.csv"):
    litshare.setdefault((reg(r["Country"]), r["Tech"], SCEN[r["Scenario"]]), {})[r["Year"]] = float(r["share_percent"])
for (c, T, s), yv in litshare.items():
    emit(c, f"{LIT}{bs}{T}", "Activity Level", interp(yv), "Share", scenario=s)
for r in rows_from("lighting_bulb_wattage.csv"):
    emit(reg(r["Country"]), f"{LIT}{bs}{r['Tech']}", "Bulb Wattage", str(float(r["watts"])), "Watts")

n_converted = len(out)

# --- Merge the 3 already-clean canon-format files verbatim ---
n_clean = 0
for f in ["appliance_efficiency_paste.csv", "cooking_canonical_input.csv", "cooking_stove_characteristics.csv"]:
    for r in rows_from(f):
        out.append({k: r.get(k, "") for k in COLS}); n_clean += 1

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=COLS); w.writeheader(); w.writerows(out)
print(f"converted (AC+Fridge+Lighting): {n_converted} rows | clean merged: {n_clean} | total: {len(out)}")
print("OUT:", OUT)
