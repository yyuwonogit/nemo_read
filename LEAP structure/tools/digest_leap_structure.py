"""Convert each 'LEAP Input <Sector>.xlsx' Export sheet to a flat CSV and
emit deterministic digest artifacts (branches, variables, scenarios, regions,
expression-pattern counts) for downstream analysis."""
import sys, io, csv, re, json, time
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
import openpyxl

SRC = Path(r"C:\Users\ThinkPad\Desktop\Py YY\NEMO_read\LEAP structure")
OUT = Path(r"C:\Users\ThinkPad\AppData\Local\Temp\claude\c--Users-ThinkPad-Desktop-Py-YY-NEMO-read\fdb165f2-ee08-4c70-936a-5e3894ab9b7c\scratchpad\digest")
OUT.mkdir(exist_ok=True)

COLS = ["branch_id","variable_id","scenario_id","region_id","branch_path",
        "variable","scenario","region","scale","units","per","expression"]

FUNC_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)\s*\(")
NUM_RE = re.compile(r"^-?\d+(\.\d+)?([eE][+-]?\d+)?$")

def classify(expr: str) -> str:
    e = expr.strip()
    if e == "":
        return "empty"
    if NUM_RE.match(e):
        return "constant:0" if float(e) == 0 else ("constant:1" if float(e) == 1 else "constant:other")
    funcs = sorted(set(f for f in FUNC_RE.findall(e)))
    has_branch_ref = "\\" in e
    if funcs:
        tag = "func:" + "+".join(funcs[:4])
    elif has_branch_ref:
        tag = "branch_ref"
    else:
        tag = "other"
    if has_branch_ref and funcs:
        tag += "+branchref"
    return tag

def process(fname, sector):
    t0 = time.time()
    wb = openpyxl.load_workbook(SRC / fname, read_only=True, data_only=True)
    ws = wb["Export"]

    csv_path = OUT / f"{sector}_rows.csv"
    n = 0
    scen = {}          # scenario_id -> name
    regions = {}       # region_id -> name
    branches = {}      # branch_path -> {"id": set, "depth": int}
    var_ids = defaultdict(set)                 # variable -> ids
    var_units = defaultdict(Counter)           # variable -> Counter(units|scale|per)
    var_count = Counter()                      # variable rows
    var_branch = defaultdict(set)              # variable -> set of branch paths (capped)
    branch_vars = defaultdict(set)             # branch_path -> set of variables
    var_expr_class = defaultdict(Counter)      # variable -> Counter(expr class)
    var_expr_samples = defaultdict(dict)       # variable -> {class: sample expr}
    scen_rows = Counter()
    region_rows = Counter()
    key_refs = Counter()                       # referenced Key\... paths inside expressions
    extra_col_hits = Counter()                 # data beyond col 21 (Level 8)
    max_depth = 0

    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(COLS)
        for row in ws.iter_rows(min_row=4, values_only=True):
            if row[0] is None and row[4] is None:
                continue
            vals = ["" if v is None else str(v) for v in row[:12]]
            bid, vid, sid, rid, bpath, var, sname, rname, scale, units, per, expr = vals
            w.writerow(vals)
            n += 1
            scen[sid] = sname
            regions[rid] = rname
            depth = bpath.count("\\") + 1 if bpath else 0
            max_depth = max(max_depth, depth)
            b = branches.get(bpath)
            if b is None:
                branches[bpath] = {"ids": {bid}, "depth": depth}
            else:
                b["ids"].add(bid)
            var_ids[var].add(vid)
            var_units[var][f"{units}|{scale}|{per}"] += 1
            var_count[var] += 1
            if len(var_branch[var]) < 2000:
                var_branch[var].add(bpath)
            branch_vars[bpath].add(var)
            cls = classify(expr)
            var_expr_class[var][cls] += 1
            if cls not in var_expr_samples[var]:
                var_expr_samples[var][cls] = expr[:400]
            scen_rows[sname] += 1
            region_rows[rname] += 1
            for m in re.finditer(r"Key\\[^\[\]+*/(),]+", expr):
                key_refs[m.group(0).strip()[:120]] += 1
            for ci in range(21, len(row)):
                if row[ci] not in (None, ""):
                    extra_col_hits[ci] += 1
            if n % 100000 == 0:
                print(f"  [{sector}] {n} rows, {time.time()-t0:.0f}s", flush=True)
    wb.close()

    # branches.csv
    with open(OUT / f"{sector}_branches.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["branch_path","branch_ids","depth","n_variables","variables"])
        for bp in sorted(branches):
            w.writerow([bp, ";".join(sorted(branches[bp]["ids"])), branches[bp]["depth"],
                        len(branch_vars[bp]), ";".join(sorted(branch_vars[bp]))])

    # variables.csv
    with open(OUT / f"{sector}_variables.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["variable","variable_ids","rows","n_branches","units_scale_per_top",
                    "expr_classes_top","sample_expressions"])
        for var in sorted(var_count, key=lambda v: -var_count[v]):
            units_top = "; ".join(f"{k} ({c})" for k, c in var_units[var].most_common(6))
            cls_top = "; ".join(f"{k} ({c})" for k, c in var_expr_class[var].most_common(8))
            samples = " || ".join(f"[{k}] {v}" for k, v in list(var_expr_samples[var].items())[:6])
            w.writerow([var, ";".join(sorted(var_ids[var])), var_count[var],
                        len(var_branch[var]), units_top, cls_top, samples])

    summary = {
        "sector": sector, "source_file": fname, "rows": n,
        "n_branches": len(branches), "max_branch_depth": max_depth,
        "n_variables": len(var_count),
        "scenarios": {k: v for k, v in sorted(scen.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 0)},
        "scenario_row_counts": dict(scen_rows),
        "regions": {k: v for k, v in sorted(regions.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 0)},
        "region_row_counts": dict(region_rows),
        "top_key_refs": dict(key_refs.most_common(40)),
        "extra_cols_beyond_level8": {f"col_{k+1}": v for k, v in sorted(extra_col_hits.items())},
        "elapsed_s": round(time.time() - t0, 1),
    }
    with open(OUT / f"{sector}_summary.json", "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, ensure_ascii=False)
    print(f"[DONE {sector}] rows={n} branches={len(branches)} vars={len(var_count)} "
          f"scen={len(scen)} regions={len(regions)} in {time.time()-t0:.0f}s", flush=True)

FILES = [
    ("LEAP Input Commercial.xlsx", "commercial"),
    ("LEAP Input Transport.xlsx", "transport"),
    ("LEAP Input Residential.xlsx", "residential"),
    ("LEAP Input Industry.xlsx", "industry"),
    ("LEAP Input Keys.xlsx", "keys"),
    ("LEAP Input Resources.xlsx", "resources"),
]
if len(sys.argv) > 1:
    FILES = [(f, s) for f, s in FILES if s in sys.argv[1:]]
for fname, sector in FILES:
    print(f"=== {fname} ===", flush=True)
    process(fname, sector)
print("ALL DONE", flush=True)
