"""Per-team 'what is currently written in LEAP' extracts, scoped to the 4 scenarios
the user cares about (CA, Baseline, ATS, RAS). Region-deduplicated: when all regions
share one expression for a (branch, variable, scenario), emit a single region='ALL' row."""
import sys, io, csv
from collections import defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
csv.field_size_limit(10_000_000)
DIG = Path(r"C:\Users\ThinkPad\AppData\Local\Temp\claude\c--Users-ThinkPad-Desktop-Py-YY-NEMO-read\fdb165f2-ee08-4c70-936a-5e3894ab9b7c\scratchpad\digest")
ART = DIG.parent / "team_artifacts"

SCEN = ["Current Accounts", "Baseline Simulation", "AMS Target Scenario", "Regional Aspiration Scenario"]

def extract(sector, out_path, prefix_filter=None):
    data = defaultdict(dict)   # (branch, var, scenario) -> {region: (expr, units, scale, per)}
    with open(DIG / f"{sector}_rows.csv", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["scenario"] not in SCEN:
                continue
            bp = r["branch_path"]
            if prefix_filter and not any(bp.startswith(p) for p in prefix_filter):
                continue
            data[(bp, r["variable"], r["scenario"])][r["region"]] = (
                r["expression"], r["units"], r["scale"], r["per"])
    n = 0
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["branch_path", "variable", "scenario", "region", "expression", "units", "scale", "per"])
        for (bp, var, sc) in sorted(data):
            regmap = data[(bp, var, sc)]
            vals = set(v[0] for v in regmap.values())
            if len(vals) == 1:
                expr, u, s, p = next(iter(regmap.values()))
                w.writerow([bp, var, sc, f"ALL ({len(regmap)} regions)", expr, u, s, p])
                n += 1
            else:
                for reg in sorted(regmap):
                    expr, u, s, p = regmap[reg]
                    w.writerow([bp, var, sc, reg, expr, u, s, p])
                    n += 1
    print(f"  {out_path.name}: {n} rows")

KEY_PREFIX = {
    "bioenergy": ["Key\\Optimized Trade", "Key\\Biofuel Blending Targets"],
    "transport": ["Key\\TransportDataStock", "Key\\Transport vehicle data_", "Key\\Other Transport",
                  "Key\\Net Zero Measures\\Transport", "Key\\Annual EI Reduction", "Key\\Cal\\Transport",
                  "Key\\Macroeconomic"],
    "residential": ["Key\\Residential", "Key\\Residential end use data_", "Key\\Cal\\Residential",
                    "Key\\Demographic", "Key\\Energy Access", "Key\\Net Zero Measures\\Residential",
                    "Key\\Macroeconomic", "Key\\Lighting_data"],
}

print("[bioenergy]")
extract("resources", ART / "bioenergy" / "current_expressions_resources_4scenarios.csv")
extract("keys", ART / "bioenergy" / "current_expressions_keys_slice_4scenarios.csv", KEY_PREFIX["bioenergy"])
print("[transport]")
extract("transport", ART / "transport" / "current_expressions_transport_4scenarios.csv")
extract("keys", ART / "transport" / "current_expressions_keys_slice_4scenarios.csv", KEY_PREFIX["transport"])
print("[residential]")
extract("residential", ART / "residential" / "current_expressions_residential_4scenarios.csv")
extract("keys", ART / "residential" / "current_expressions_keys_slice_4scenarios.csv", KEY_PREFIX["residential"])
print("DONE")
