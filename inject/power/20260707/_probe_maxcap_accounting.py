"""Offline RAS Maximum-Capacity-vs-Exogenous-Capacity accounting (no COM).

Rebuilds the live area's RAS-effective power inputs from the layers WE hold
(user directive 2026-07-07: "we have the complete input file and we INJECT IT
OURSELVES so we know whats in there"):

  L0  v0.67 raw extracts (full_dataset wide + slice incl ALL-rows + Indonesia)
  L1  20260507 injected drops (ats_cap_add / ats_cap_ret / ats_exo_formula /
      bas_all_zero — inject logs on disk confirm they landed)
  L3  modeller v0.68/v0.69 edit records
  L4  today's payload (readback-verified 9,337 rows)

NOT layered (no inject log => never landed): 20260507 from-PowerTeam
fix_exogenous_capacity.csv, 20260705 exo_capacity_canonical.csv.

RAS-effective value of a slot: first hit in scenario tiers
RAS -> ATS -> BAS -> CA (LEAP inheritance approximation; the tier used is
recorded per result row so assumption-dependent verdicts are visible).

Expression evaluation is THREE-STATE (number / UNEVALUABLE / EMPTY):
a parse failure is NEVER coerced to 0; `? comment` citations are stripped
before parsing (naive float("1500.0 ? IES...") -> the exact 0-trap the user
flagged). Add() = cumulative additions to year; Interp linear w/ flat ends;
Step hold; Max/Min/+/- and same-branch var refs resolved recursively.
"""
import csv, re, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
BS = chr(92)
YEARS = list(range(2023, 2061))
AMS10 = ["Brunei", "Cambodia", "Indonesia", "Laos", "Malaysia", "Myanmar",
         "Philippines", "Singapore", "Thailand", "Vietnam"]
SCEN = {"CA": "Current Accounts", "BAS": "Baseline Simulation",
        "ATS": "AMS Target Scenario", "RAS": "Regional Aspiration Scenario"}
TIERS = ["Regional Aspiration Scenario", "AMS Target Scenario",
         "Baseline Simulation", "Current Accounts"]
VARS = ["Maximum Capacity", "Exogenous Capacity", "Existing Capacity",
        "Capacity Additions", "Capacity Retirement"]

sys.path.insert(0, str(REPO))
from nemo_read.inject_base import NODE_REGION_LOCK, BASE_BRANCH_NODE_ONLY

def leaf(b): return b.rstrip(BS).split(BS)[-1].strip()

def valid_pair(region, lf):
    for pat, home in NODE_REGION_LOCK.items():
        if pat.search(lf):
            return region == home
    return lf not in BASE_BRANCH_NODE_ONLY.get(region, frozenset())

# ---------- layered state store ----------
state = {}  # (region, leaf, var, scenario) -> (expr, layer)

def put(region, lf, var, scen, expr, layer):
    expr = (expr or "").strip()
    if not expr:
        return
    state[(region, lf, var, scen)] = (expr, layer)

def load_wide(path, layer):
    with open(path, encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            if r.get("variable") not in VARS: continue
            for col, scen in SCEN.items():
                put(r["region"].strip(), r["node"].strip(),
                    r["variable"].strip(), scen, r.get(col), layer)

def load_export(path, layer):
    with open(path, encoding="utf-8-sig") as fh:
        rdr = csv.DictReader(fh)
        f = {k.lower().replace(" ", "_"): k for k in (rdr.fieldnames or [])}
        bp, var = f.get("branch_path"), f.get("variable")
        sc, rg, ex = f.get("scenario"), f.get("region"), f.get("expression")
        if not all([bp, var, sc, rg, ex]): return
        for r in rdr:
            v = (r[var] or "").strip()
            if v not in VARS: continue
            regions = ([x for x in AMS10] if (r[rg] or "").startswith("ALL")
                       else [(r[rg] or "").strip()])
            for region in regions:
                put(region, leaf(r[bp] or ""), v, (r[sc] or "").strip(),
                    r[ex], layer)

H = "inject/power/structure_handover_20260703"
load_wide(REPO / H / "processes_full_dataset_4scenarios.csv", "L0-full")
load_export(REPO / H / "current_expressions_transformation_slice_4scenarios.csv", "L0-slice")
load_export(REPO / H / "current_expressions_transformation_indonesia_nodes_4scenarios.csv", "L0-idn")
for f in ["ats_cap_add.csv", "ats_cap_ret.csv", "ats_exo_formula.csv",
          "bas_all_zero.csv"]:
    load_export(REPO / "inject/power/20260507" / f, f"L1-{f[:-4]}")
load_export(REPO / "inject/power/structure_handover_20260706/v068_unique_edits_52rows.csv", "L3-v068")
load_export(REPO / "inject/power/structure_handover_20260706/v069_ras_edits_myid_25rows.csv", "L3-v069")
with open(REPO / "inject/power/20260707/power_sendback_canonical.csv",
          encoding="utf-8-sig") as fh:
    for r in csv.DictReader(fh):
        if r["variable"].strip() in VARS:
            put(r["ams"].strip(), leaf(r["branch"]), r["variable"].strip(),
                r["scenario"].strip(), r["expression"], "L4-payload")

def effective(region, lf, var):
    """RAS-effective (expr, layer, tier) or (None, None, None)."""
    for scen in TIERS:
        hit = state.get((region, lf, var, scen))
        if hit:
            return hit[0], hit[1], scen
    return None, None, None

# ---------- three-state expression evaluator ----------
class Unevaluable(Exception): pass

NUM = r"-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?"

def strip_comment(s):
    return s.split("?", 1)[0].strip()

def _pairs(argstr):
    nums = [float(x) for x in re.findall(NUM, argstr)]
    if len(nums) < 2 or len(nums) % 2: raise Unevaluable(f"odd args: {argstr[:40]}")
    return list(zip(nums[0::2], nums[1::2]))

def evaluate(expr, env, depth=0):
    """-> list of values per YEARS. env: varname -> expr (same branch)."""
    if depth > 6: raise Unevaluable("ref depth")
    s = strip_comment(expr)
    if not s: raise Unevaluable("empty")
    if re.fullmatch(NUM, s): return [float(s)] * len(YEARS)
    m = re.fullmatch(r"(Interp|Step|Add)\s*\((.*)\)", s, re.I | re.S)
    if m:
        fn, pairs = m.group(1).lower(), _pairs(m.group(2))
        out = []
        for y in YEARS:
            if fn == "add":
                out.append(sum(v for yy, v in pairs if yy <= y))
            elif fn == "step":
                vals = [v for yy, v in pairs if yy <= y]
                out.append(vals[-1] if vals else 0.0)
            else:  # interp: flat ends, linear between
                if y <= pairs[0][0]: out.append(pairs[0][1])
                elif y >= pairs[-1][0]: out.append(pairs[-1][1])
                else:
                    for (y1, v1), (y2, v2) in zip(pairs, pairs[1:]):
                        if y1 <= y <= y2:
                            out.append(v1 + (v2 - v1) * (y - y1) / (y2 - y1))
                            break
        return out
    m = re.fullmatch(r"(Max|Min)\s*\((.*)\)", s, re.I | re.S)
    if m:
        # split args at top level
        args, d, cur = [], 0, ""
        for ch in m.group(2):
            if ch == "(": d += 1
            if ch == ")": d -= 1
            if ch == "," and d == 0: args.append(cur); cur = ""
            else: cur += ch
        args.append(cur)
        series = [evaluate(a.strip(), env, depth + 1) for a in args]
        f = max if m.group(1).lower() == "max" else min
        return [f(col) for col in zip(*series)]
    # arithmetic chain of terms: A + B - C  (terms = refs/numbers/calls)
    parts = re.split(r"\s([+-])\s", s)
    if len(parts) > 1:
        total = evaluate(parts[0], env, depth + 1)
        for op, term in zip(parts[1::2], parts[2::2]):
            tv = evaluate(term, env, depth + 1)
            total = [a + b if op == "+" else a - b for a, b in zip(total, tv)]
        return total
    m = re.fullmatch(r"([A-Za-z][A-Za-z ]*?)\s*\[[^\]]*\]", s)
    if m:
        ref = m.group(1).strip()
        if ref in env and env[ref] is not None:
            return evaluate(env[ref], env, depth + 1)
        if ref in VARS:  # referenced building block empty at all layers
            raise Unevaluable(f"ref '{ref}' EMPTY at all layers")
        raise Unevaluable(f"unknown ref '{ref}'")
    raise Unevaluable(s[:60])

# ---------- branch universe: canon tree, Centralized + Distributed ----------
tree = (REPO / "LEAP structure/trees/transformation_tree.txt").read_text(
    encoding="utf-8").splitlines()
def depth_of(l): return (len(l) - len(l.lstrip(" "))) // 2
def name_of(l): return l.lstrip(" ").split("   [vars:")[0].strip()
procs = set()
block = None
for l in tree:
    if depth_of(l) == 1:
        block = name_of(l)
    elif depth_of(l) == 3 and block in ("Centralized Electricity Generation",
                                        "Distributed Electricity Generation"):
        procs.add(name_of(l))

# ---------- the accounting ----------
viol, unev, empty0, ok = [], [], 0, 0
for region in AMS10:
    for lf in sorted(procs):
        if not valid_pair(region, lf): continue
        mc_expr, mc_layer, mc_tier = effective(region, lf, "Maximum Capacity")
        if mc_expr is None: continue
        if "unlimited" in mc_expr.lower(): continue
        env = {}
        for v in VARS[1:]:
            e, _, _ = effective(region, lf, v)
            env[v] = e
        exo_expr = env.get("Exogenous Capacity")
        if exo_expr is None: continue
        # MaxCap expressed as the exo formula itself => equal, never a breach
        try:
            mc = evaluate(mc_expr, env)
        except Unevaluable as e:
            unev.append((region, lf, "Maximum Capacity", mc_expr[:70], str(e)[:50]))
            continue
        try:
            # empty building blocks referenced by the formula -> flag, not 0
            exo = evaluate(exo_expr, env)
        except Unevaluable as e:
            unev.append((region, lf, "Exogenous Capacity", exo_expr[:70], str(e)[:50]))
            continue
        breach = [(y, e_, m_) for y, e_, m_ in zip(YEARS, exo, mc) if e_ > m_ + 1e-9]
        if breach:
            y0, e0, m0 = breach[0]
            peak = max(b[1] for b in breach)
            viol.append((region, lf, y0, m0, e0, peak, mc_layer, mc_tier,
                         (state.get((region, lf, "Capacity Additions", t))
                          for t in TIERS)))
        else:
            ok += 1

print(f"pairs OK={ok}  VIOLATIONS={len(viol)}  UNEVALUABLE={len(unev)}\n")
print("=== VIOLATIONS (RAS-effective): MaxCap < ExoCap ===")
print(f"{'region':<12} {'tech':<24} {'1st yr':<7} {'MaxCap':>10} {'Exo@1st':>10} {'ExoPeak':>10}  maxcap-src")
for region, lf, y0, m0, e0, peak, ml, mt, _ in sorted(viol):
    print(f"{region:<12} {lf:<24} {y0:<7} {m0:>10.1f} {e0:>10.1f} {peak:>10.1f}  {ml}/{mt[:3]}")
print("\n=== UNEVALUABLE (listed, NEVER assumed 0) ===")
for row in unev:
    print("  " + " | ".join(str(x) for x in row))

with open(REPO / "inject/power/20260707/_maxcap_accounting_RAS.csv", "w",
          newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["region", "tech", "first_breach_year", "maxcap_at_breach",
                "exo_at_breach", "exo_peak", "maxcap_layer", "maxcap_tier"])
    for region, lf, y0, m0, e0, peak, ml, mt, _ in sorted(viol):
        w.writerow([region, lf, y0, m0, e0, peak, ml, mt])
print(f"\nfull CSV: inject/power/20260707/_maxcap_accounting_RAS.csv")
