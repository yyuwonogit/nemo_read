"""Negative Exogenous Capacity sweep — ATS + BAS, all techs/regions, layered.

ATS/BAS Exo formula is the BARE `Existing + Additions - Retirement` (no
Max(...,0) guard, unlike RAS). If a retirement schedule ever exceeds
Existing+Additions in a year, Exo goes negative -> NEMO ResidualCapacity < 0
-> infeasible / garbage. Sweep the LAYERED state (raw v0.67 + injected
baseline + this batch's main + batch1b) and flag any (region, tech, year, scen)
with Exo < 0. Three-state: number / UNRESOLVED (listed, never assumed 0).
"""
import csv, re, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

BS = chr(92)
YEARS = list(range(2023, 2061))
AMS10 = ["Brunei","Cambodia","Indonesia","Laos","Malaysia","Myanmar",
         "Philippines","Singapore","Thailand","Vietnam"]
WIDE = {"CA":"Current Accounts","BAS":"Baseline Simulation",
        "ATS":"AMS Target Scenario","RAS":"Regional Aspiration Scenario"}
VARS = {"Exogenous Capacity","Existing Capacity","Capacity Additions",
        "Capacity Retirement"}

def leaf(b): return b.rstrip(BS).split(BS)[-1].strip()

# state[(region, leaf, var, scenario)] = expr  (later layers overwrite)
state = {}
def put(rg, lf, var, sc, ex):
    ex = (ex or "").strip()
    if ex: state[(rg, lf, var, sc)] = ex

def load_wide(p):
    for r in csv.DictReader(open(p, encoding="utf-8-sig")):
        if r.get("variable") not in VARS: continue
        for col, sc in WIDE.items():
            put(r["region"].strip(), r["node"].strip(), r["variable"].strip(), sc, r.get(col))

def load_long(p, rcol, bcol):
    rdr = csv.DictReader(open(p, encoding="utf-8-sig"))
    f = {k.lower().replace(" ","_"): k for k in rdr.fieldnames}
    rc = f.get(rcol); bc = f.get(bcol); vc = f.get("variable")
    sc = f.get("scenario"); ec = f.get("expression")
    for r in rdr:
        if (r[vc] or "").strip() not in VARS: continue
        regs = AMS10 if (r[rc] or "").startswith("ALL") else [(r[rc] or "").strip()]
        for region in regs:
            put(region, leaf(r[bc] or ""), (r[vc] or "").strip(), (r[sc] or "").strip(), r[ec])

H = REPO / "inject/power/structure_handover_20260703"
load_wide(H / "processes_full_dataset_4scenarios.csv")
load_long(H / "current_expressions_transformation_slice_4scenarios.csv", "region", "branch_path")
load_long(H / "current_expressions_transformation_indonesia_nodes_4scenarios.csv", "region", "branch_path")
# injected baseline (ams/branch long)
load_long(REPO / "inject/power/20260707/power_sendback_canonical.csv", "ams", "branch")
# this batch
B = REPO / "inject/power/20260708"
load_long(B / "power_batch1_delta_20260708.csv", "ams", "branch")
load_long(B / "power_batch1b_endogenous_ATS_BAS_delta_20260708.csv", "ams", "branch")

NUM = r"-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?"
class UE(Exception): pass
def strip_c(s): return s.split("?", 1)[0].strip()

def eff(rg, lf, var, scen):
    """Scenario-specific with CA parent fallback (LEAP inheritance)."""
    for s in (scen, "Current Accounts"):
        if (rg, lf, var, s) in state: return state[(rg, lf, var, s)]
    return None

def ev(expr, rg, lf, var, scen, depth=0):
    if depth > 8: raise UE("depth")
    s = strip_c(expr)
    if not s: raise UE("empty")
    s = re.sub(r"("+NUM+r")\s*%", lambda m: "("+repr(float(m.group(1))/100)+")", s)
    def split_top(x, seps):
        out, d, cur, i = [], 0, "", 0
        while i < len(x):
            ch = x[i]
            if ch == "(": d += 1
            if ch == ")": d -= 1
            unary = (ch == "-" and (not cur.strip() or cur.rstrip()[-1:] in "+-*/(,"))
            if d == 0 and ch in seps and not unary:
                out.append(cur); out.append(ch); cur = ""
            else: cur += ch
            i += 1
        out.append(cur); return out
    add = split_top(s, "+-")
    if len(add) > 1:
        tot = ev(add[0], rg, lf, var, scen, depth+1)
        for op, term in zip(add[1::2], add[2::2]):
            tv = ev(term, rg, lf, var, scen, depth+1)
            tot = [a+b if op == "+" else a-b for a, b in zip(tot, tv)]
        return tot
    mul = split_top(s, "*/")
    if len(mul) > 1:
        tot = ev(mul[0], rg, lf, var, scen, depth+1)
        for op, term in zip(mul[1::2], mul[2::2]):
            tv = ev(term, rg, lf, var, scen, depth+1)
            tot = [a*b if op == "*" else (a/b if b else float("inf")) for a, b in zip(tot, tv)]
        return tot
    s = s.strip()
    if s.startswith("(") and s.endswith(")"): return ev(s[1:-1], rg, lf, var, scen, depth+1)
    if re.fullmatch(NUM, s): return [float(s)]*len(YEARS)
    m = re.fullmatch(r"(Interp|Step|Add)\s*\((.*)\)", s, re.I|re.S)
    if m:
        fn = m.group(1).lower()
        nums = [float(x) for x in re.findall(NUM, m.group(2))]
        pr = list(zip(nums[0::2], nums[1::2]))
        if not pr: raise UE(s[:40])
        out = []
        for y in YEARS:
            if fn == "add": out.append(sum(v for yy, v in pr if yy <= y))
            elif fn == "step":
                vs = [v for yy, v in pr if yy <= y]; out.append(vs[-1] if vs else 0.0)
            else:
                if y <= pr[0][0]: out.append(pr[0][1])
                elif y >= pr[-1][0]: out.append(pr[-1][1])
                else:
                    for (y1,v1),(y2,v2) in zip(pr, pr[1:]):
                        if y1 <= y <= y2: out.append(v1+(v2-v1)*(y-y1)/(y2-y1)); break
        return out
    m = re.fullmatch(r"(Max|Min)\s*\((.*)\)", s, re.I|re.S)
    if m:
        args, d, cur = [], 0, ""
        for ch in m.group(2):
            if ch == "(": d += 1
            if ch == ")": d -= 1
            if ch == "," and d == 0: args.append(cur); cur = ""
            else: cur += ch
        args.append(cur)
        se = [ev(a.strip(), rg, lf, var, scen, depth+1) for a in args]
        f = max if m.group(1).lower() == "max" else min
        return [f(col) for col in zip(*se)]
    m = re.fullmatch(r"Value\s*\(\s*(\d{4})\s*\)", s, re.I)
    if m:
        y = int(m.group(1)); ca = eff(rg, lf, var, "Current Accounts")
        if ca is None: raise UE("Value(%d) CA-empty %s" % (y, var))
        vs = ev(ca, rg, lf, var, scen, depth+1)
        yy = min(max(y, YEARS[0]), YEARS[-1]); return [vs[YEARS.index(yy)]]*len(YEARS)
    m = re.fullmatch(r"(?:(.+?):)?\s*([A-Za-z][A-Za-z _]*?)\s*\[[^\]]*\]", s)
    if m:
        tgt = leaf(m.group(1).strip()) if m.group(1) else lf
        rv = m.group(2).strip()
        e = eff(rg, tgt, rv, scen)
        if e is None: raise UE("ref %s:%s empty" % (tgt, rv))
        if tgt == lf and rv == var: raise UE("self " + var)
        return ev(e, rg, tgt, rv, scen, depth+1)
    raise UE(s[:50])

# technology universe = every leaf that has an Exo expression in ATS or BAS
techs = {(rg, lf) for (rg, lf, v, s) in state
         if v == "Exogenous Capacity" and s in ("AMS Target Scenario", "Baseline Simulation")}
neg, unresolved, ok = [], [], 0
for scen in ("AMS Target Scenario", "Baseline Simulation"):
    for (rg, lf) in sorted(techs):
        exo = eff(rg, lf, "Exogenous Capacity", scen)
        if exo is None: continue
        try:
            v = ev(exo, rg, lf, "Exogenous Capacity", scen)
        except UE as e:
            unresolved.append((scen[:3], rg, lf, str(e)[:40])); continue
        bad = [(YEARS[i], v[i]) for i in range(len(YEARS)) if v[i] < -1e-6]
        if bad:
            y0, val0 = bad[0]; neg.append((scen[:3], rg, lf, y0, val0, min(x[1] for x in bad), exo[:45]))
        else: ok += 1

print("Exo pairs evaluated OK=%d  NEGATIVE=%d  UNRESOLVED=%d\n" % (ok, len(neg), len(unresolved)))
print("=== NEGATIVE Exogenous Capacity (ATS/BAS) ===")
if not neg: print("  NONE — no tech/region/year goes negative in ATS or BAS")
for scen, rg, lf, y0, v0, vmin, ex in sorted(neg):
    print("  [%s] %-12s %-24s 1st<0 @ %d = %.1f  (min %.1f)  exo=%s" % (scen, rg, lf, y0, v0, vmin, ex))
print("\n=== UNRESOLVED (building block empty at all layers — listed, not assumed 0) ===")
from collections import Counter
c = Counter((u[0], u[3]) for u in unresolved)
for (scn, reason), n in sorted(c.items()): print("  [%s] %3dx  %s" % (scn, n, reason))
