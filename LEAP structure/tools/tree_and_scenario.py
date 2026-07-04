"""Per sector: (1) indented branch tree with variable attachment,
(2) scenario-variation matrix — for each (branch, variable), how many distinct
expressions exist across scenarios and which scenarios diverge from Current
Accounts / Baseline, (3) region-variation — which rows differ across regions."""
import sys, io, csv, json
from collections import defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
csv.field_size_limit(10_000_000)

DIG = Path(r"C:\Users\ThinkPad\AppData\Local\Temp\claude\c--Users-ThinkPad-Desktop-Py-YY-NEMO-read\fdb165f2-ee08-4c70-936a-5e3894ab9b7c\scratchpad\digest")
sectors = sys.argv[1:] or ["commercial", "transport", "residential"]

for sector in sectors:
    # ---- tree ----
    rows = list(csv.DictReader(open(DIG / f"{sector}_branches.csv", encoding="utf-8")))
    with open(DIG / f"{sector}_tree.txt", "w", encoding="utf-8") as fh:
        for r in sorted(rows, key=lambda r: r["branch_path"].lower()):
            parts = r["branch_path"].split("\\")
            indent = "  " * (len(parts) - 1)
            fh.write(f"{indent}{parts[-1]}   [vars: {r['variables']}]\n")

    # ---- scenario + region variation ----
    # expr[(branch, variable)][scenario][region] = expression
    expr = defaultdict(lambda: defaultdict(dict))
    with open(DIG / f"{sector}_rows.csv", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            expr[(r["branch_path"], r["variable"])][r["scenario"]][r["region"]] = r["expression"]

    out = DIG / f"{sector}_scenario_variation.csv"
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["branch_path","variable","n_scenarios_present","scenarios_missing_or_extra",
                    "n_distinct_expr_across_scenarios","scenarios_diverging_from_CA",
                    "n_regions_with_regional_variation","sample_CA_expr","sample_diverging_expr"])
        all_scen = set()
        for scmap in expr.values():
            all_scen.update(scmap)
        for (bp, var), scmap in sorted(expr.items()):
            missing = sorted(all_scen - set(scmap))
            # per-scenario fingerprint: tuple of (region, expr) sorted
            fps = {sc: tuple(sorted(rm.items())) for sc, rm in scmap.items()}
            distinct = len(set(fps.values()))
            ca = fps.get("Current Accounts")
            diverging = sorted(sc for sc, fp in fps.items()
                               if sc != "Current Accounts" and ca is not None and fp != ca)
            # regional variation within CA (or first scenario)
            base_sc = "Current Accounts" if "Current Accounts" in scmap else next(iter(scmap))
            regmap = {k: v for k, v in scmap[base_sc].items() if k != "Base Template"}
            n_reg_var = len(set(regmap.values()))
            ca_expr = (scmap.get("Current Accounts", {}) or next(iter(scmap.values()))).get("Indonesia", "")
            div_expr = ""
            if diverging:
                div_expr = scmap[diverging[0]].get("Indonesia", "")
            w.writerow([bp, var, len(scmap), ";".join(missing), distinct,
                        ";".join(diverging), n_reg_var, ca_expr[:300], div_expr[:300]])
    print(f"[DONE {sector}] tree + scenario_variation written", flush=True)
print("OK", flush=True)
