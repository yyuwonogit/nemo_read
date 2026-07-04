"""Phase 0: mechanical connection audit + slice generation for all 7 teams.

For each demand sector, live-code references (expression text BEFORE the first '?')
into Key\\ / Resources\\ define the connected-slice branch sets. Owner groups are
unioned in. Outputs per-team artifacts + a gap audit for the 3 shipped packages."""
import sys, io, csv, re, json
from collections import defaultdict, Counter
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
csv.field_size_limit(10_000_000)
DIG = Path(r"C:\Users\ThinkPad\AppData\Local\Temp\claude\c--Users-ThinkPad-Desktop-Py-YY-NEMO-read\fdb165f2-ee08-4c70-936a-5e3894ab9b7c\scratchpad\digest")
ART = DIG.parent / "team_artifacts"
REPO = Path(r"C:\Users\ThinkPad\Desktop\Py YY\NEMO_read")

REF_RE = re.compile(r"((?:Key|Resources)\\[^:\[\]()+*/,?]+)")
SCEN4 = ["Current Accounts", "Baseline Simulation", "AMS Target Scenario", "Regional Aspiration Scenario"]

def load_branches(sector):
    out = {}
    with open(DIG / f"{sector}_branches.csv", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            out[r["branch_path"].strip()] = r
    return out

KEYS_B = load_branches("keys")
RES_B = load_branches("resources")

def live_refs(sector):
    """Branch paths referenced in live code (pre-'?') of a sector's expressions."""
    refs = Counter()
    with open(DIG / f"{sector}_rows.csv", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            code = r["expression"].split("?")[0]
            for m in REF_RE.finditer(code):
                bp = m.group(1).strip().rstrip("\\").strip()
                # resolve to an existing branch (refs sometimes hit a variable suffix)
                if bp in KEYS_B or bp in RES_B:
                    refs[bp] += 1
    return refs

# ---- owner groups per team (hand-defined where no demand expressions exist) ----
OWNER = {
    "commercial":  ["Key\\Commercial"],
    "transport":   ["Key\\TransportDataStock", "Key\\Transport vehicle data_", "Key\\Other Transport",
                    "Key\\Net Zero Measures\\Transport", "Key\\Cal\\Transport"],
    "residential": ["Key\\Residential", "Key\\Residential end use data_", "Key\\Cal\\Residential",
                    "Key\\Net Zero Measures\\Residential", "Key\\Lighting_data"],
    "bioenergy":   ["Key\\Optimized Trade", "Key\\Biofuel Blending Targets"],
    "fossil":      [],
    "power":       ["Key\\Capacity Additions Multiplier", "Key\\Modeling Assumptions", "Key\\Job creations",
                    "Key\\Emission Externality Costs", "Key\\Transmission", "Key\\Region Group RE Targets",
                    "Key\\Cal\\Transformation", "Key\\End_cap multip", "Key\\Annual EI Reduction"],
}
DEMAND_SECTOR = {"commercial": "commercial", "transport": "transport", "residential": "residential"}

def slice_branches(team):
    keys, res = set(), set()
    for g in OWNER.get(team, []):
        keys.update(b for b in KEYS_B if b == g or b.startswith(g + "\\"))
    if team in DEMAND_SECTOR:
        for bp, n in live_refs(DEMAND_SECTOR[team]).items():
            (keys if bp.startswith("Key\\") else res).add(bp)
    if team in ("bioenergy", "fossil"):
        res.update(RES_B)          # full resources tree ships to both supply teams
    if team == "power":
        res.update(RES_B)          # renewables caps + fuel supply context
    return sorted(keys), sorted(res)

def units_map(sector):
    m = defaultdict(set)
    with open(DIG / f"{sector}_rows.csv", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            m[(r["branch_path"], r["variable"])].add((r["units"], r["scale"], r["per"]))
    return m

KEYS_UM = units_map("keys")
RES_UM = units_map("resources")

def write_slice_files(team, keys, res, dest):
    dest.mkdir(parents=True, exist_ok=True)
    if keys:
        with open(dest / f"keys_slice_{team}.txt", "w", encoding="utf-8") as fh:
            for bp in sorted(keys, key=str.lower):
                fh.write("  " * bp.count("\\") + bp.split("\\")[-1] + f"   [{bp}]  vars: {KEYS_B[bp]['variables']}\n")
        with open(dest / f"keys_slice_{team}_units.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh); w.writerow(["branch_path", "variable", "units", "scale", "per"])
            for (bp, var) in sorted(KEYS_UM):
                if bp in keys:
                    for u, s, p in sorted(KEYS_UM[(bp, var)]):
                        w.writerow([bp, var, u, s, p])
    if res:
        with open(dest / f"resources_slice_{team}_units.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh); w.writerow(["branch_path", "variable", "units", "scale", "per"])
            for (bp, var) in sorted(RES_UM):
                if bp in res:
                    for u, s, p in sorted(RES_UM[(bp, var)]):
                        w.writerow([bp, var, u, s, p])

def extract_4scen(sector, out_path, allowed=None):
    data = defaultdict(dict)
    with open(DIG / f"{sector}_rows.csv", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["scenario"] not in SCEN4:
                continue
            bp = r["branch_path"]
            if allowed is not None and bp not in allowed:
                continue
            data[(bp, r["variable"], r["scenario"])][r["region"]] = (r["expression"], r["units"], r["scale"], r["per"])
    n = 0
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(["branch_path", "variable", "scenario", "region", "expression", "units", "scale", "per"])
        for k in sorted(data):
            regmap = data[k]
            if len(set(v[0] for v in regmap.values())) == 1:
                e, u, s, p = next(iter(regmap.values()))
                w.writerow([*k, f"ALL ({len(regmap)} regions)", e, u, s, p]); n += 1
            else:
                for reg in sorted(regmap):
                    e, u, s, p = regmap[reg]
                    w.writerow([*k, reg, e, u, s, p]); n += 1
    return n

report = {}
for team in ["commercial", "keys", "fossil", "power", "bioenergy", "transport", "residential"]:
    if team == "keys":
        d = ART / "keys"; d.mkdir(parents=True, exist_ok=True)
        with open(d / "keys_branch_variables_units.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh); w.writerow(["branch_path", "variable", "units", "scale", "per"])
            for (bp, var) in sorted(KEYS_UM):
                for u, s, p in sorted(KEYS_UM[(bp, var)]):
                    w.writerow([bp, var, u, s, p])
        n = extract_4scen("keys", d / "current_expressions_keys_4scenarios.csv")
        report[team] = {"full_key_tree": len(KEYS_B), "extract_rows": n}
        print(f"[keys] full tree units + extract ({n} rows)")
        continue
    keys, res = slice_branches(team)
    d = ART / team
    write_slice_files(team, set(keys), set(res), d)
    nk = extract_4scen("keys", d / f"current_expressions_keys_slice_4scenarios.csv", set(keys)) if keys else 0
    nr = 0
    if team in ("commercial",):
        nr = extract_4scen("resources", d / "current_expressions_resources_slice_4scenarios.csv", set(res)) if res else 0
    if team in ("fossil", "power"):
        nr = extract_4scen("resources", d / "current_expressions_resources_4scenarios.csv")
    if team == "commercial":
        # own-tree artifacts
        m = units_map("commercial")
        with open(d / "commercial_branch_variables_units.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh); w.writerow(["branch_path", "variable", "units", "scale", "per"])
            for (bp, var) in sorted(m):
                for u, s, p in sorted(m[(bp, var)]):
                    w.writerow([bp, var, u, s, p])
        extract_4scen("commercial", d / "current_expressions_commercial_4scenarios.csv")
    report[team] = {"keys_slice": len(keys), "resources_slice": len(res),
                    "keys_extract_rows": nk, "res_extract_rows": nr}
    print(f"[{team}] keys_slice={len(keys)} resources_slice={len(res)} keys_extract={nk} res_extract={nr}")

# ---- gap audit for the 3 shipped packages ----
print("\n=== SHIPPED-PACKAGE SLICE GAP AUDIT ===")
gaps = {}
for team in ["bioenergy", "transport", "residential"]:
    shipped = set()
    f = REPO / "inject" / team / "structure_handover_20260703" / f"keys_slice_{team}.txt"
    for line in f.read_text(encoding="utf-8").splitlines():
        m = re.search(r"\[(Key\\[^\]]+)\]", line)
        if m:
            shipped.add(m.group(1))
    want = set(slice_branches(team)[0])
    missing = sorted(want - shipped)
    extra = sorted(shipped - want)
    gaps[team] = {"missing_from_shipped": missing, "extra_in_shipped_ok": len(extra)}
    print(f"[{team}] shipped={len(shipped)} want={len(want)} MISSING={len(missing)}")
    for b in missing[:15]:
        print(f"    - {b}")
(ART / "phase0_report.json").write_text(json.dumps({"report": report, "gaps": gaps}, indent=2, ensure_ascii=False), encoding="utf-8")
print("DONE")
