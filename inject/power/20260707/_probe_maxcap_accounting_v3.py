"""v3 RAS MaxCap-vs-ExoCap accounting — full offline closure.

Adds over v1/v2: Value(YYYY) resolution (CA-tier expression evaluated at that
year), % and * / arithmetic (no-space operators), cross-branch cap references
(Large Hydro:Maximum Capacity[MW], full-path refs), parenthesized terms.
Three-state discipline: number / UNRESOLVED (listed) / EMPTY — never silent 0.
"""
import csv, re, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
from nemo_read.inject_base import NODE_REGION_LOCK, BASE_BRANCH_NODE_ONLY

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

def leaf(b): return b.rstrip(BS).split(BS)[-1].strip()

state = {}
def put(rg, lf, var, sc, ex, layer):
    ex = (ex or "").strip()
    if ex:
        state[(rg, lf, var, sc)] = (ex, layer)

def load_wide(p, layer):
    for r in csv.DictReader(open(p, encoding="utf-8-sig")):
        if r.get("variable") not in VARS:
            continue
        for col, sc in SCEN.items():
            put(r["region"].strip(), r["node"].strip(),
                r["variable"].strip(), sc, r.get(col), layer)

def load_export(p, layer):
    rdr = csv.DictReader(open(p, encoding="utf-8-sig"))
    f = {k.lower().replace(" ", "_"): k for k in (rdr.fieldnames or [])}
    bp, var, sc, rg, ex = (f.get(x) for x in
                           ("branch_path", "variable", "scenario", "region",
                            "expression"))
    if not all([bp, var, sc, rg, ex]):
        return
    for r in rdr:
        v = (r[var] or "").strip()
        if v not in VARS:
            continue
        regs = AMS10 if (r[rg] or "").startswith("ALL") else [(r[rg] or "").strip()]
        for region in regs:
            put(region, leaf(r[bp] or ""), v, (r[sc] or "").strip(),
                r[ex], layer)

H = REPO / "inject/power/structure_handover_20260703"
load_wide(H / "processes_full_dataset_4scenarios.csv", "L0")
load_export(H / "current_expressions_transformation_slice_4scenarios.csv", "L0s")
load_export(H / "current_expressions_transformation_indonesia_nodes_4scenarios.csv", "L0i")
for f2 in ["ats_cap_add.csv", "ats_cap_ret.csv", "ats_exo_formula.csv",
           "bas_all_zero.csv"]:
    load_export(REPO / "inject/power/20260507" / f2, "L1-" + f2[:-4])
load_export(REPO / "inject/power/structure_handover_20260706/v068_unique_edits_52rows.csv", "L3")
load_export(REPO / "inject/power/structure_handover_20260706/v069_ras_edits_myid_25rows.csv", "L3")
for r in csv.DictReader(open(REPO / "inject/power/20260707/power_sendback_canonical.csv",
                             encoding="utf-8-sig")):
    if r["variable"].strip() in VARS:
        put(r["ams"].strip(), leaf(r["branch"]), r["variable"].strip(),
            r["scenario"].strip(), r["expression"], "L4")

def eff(rg, lf, var, tiers=TIERS):
    for sc in tiers:
        h = state.get((rg, lf, var, sc))
        if h:
            return h[0], h[1], sc
    return None, None, None

NUM = r"-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?"

class UE(Exception):
    pass

def sc_(s):
    return s.split("?", 1)[0].strip()

def toks_pairs(a):
    n = [float(x) for x in re.findall(NUM, a)]
    return list(zip(n[0::2], n[1::2]))

def split_top(s, seps):
    out, d, cur, i = [], 0, "", 0
    while i < len(s):
        ch = s[i]
        if ch == "(":
            d += 1
        if ch == ")":
            d -= 1
        unary = (ch == "-" and (not cur.strip() or cur.rstrip()[-1:] in "+-*/(,"))
        if d == 0 and ch in seps and not unary:
            out.append(cur)
            out.append(ch)
            cur = ""
        else:
            cur += ch
        i += 1
    out.append(cur)
    return out

def ev(expr, rg, lf, var, depth=0):
    if depth > 8:
        raise UE("depth")
    s = sc_(expr)
    if not s:
        raise UE("empty")
    s = re.sub(r"(" + NUM + r")\s*%",
               lambda m: "(" + repr(float(m.group(1)) / 100) + ")", s)
    add = split_top(s, "+-")
    if len(add) > 1:
        tot = ev(add[0], rg, lf, var, depth + 1)
        for op, term in zip(add[1::2], add[2::2]):
            tv = ev(term, rg, lf, var, depth + 1)
            tot = [a + b if op == "+" else a - b for a, b in zip(tot, tv)]
        return tot
    mul = split_top(s, "*/")
    if len(mul) > 1:
        tot = ev(mul[0], rg, lf, var, depth + 1)
        for op, term in zip(mul[1::2], mul[2::2]):
            tv = ev(term, rg, lf, var, depth + 1)
            tot = [a * b if op == "*" else (a / b if b else float("inf"))
                   for a, b in zip(tot, tv)]
        return tot
    s = s.strip()
    if s.startswith("(") and s.endswith(")"):
        return ev(s[1:-1], rg, lf, var, depth + 1)
    if re.fullmatch(NUM, s):
        return [float(s)] * len(YEARS)
    m = re.fullmatch(r"(Interp|Step|Add)\s*\((.*)\)", s, re.I | re.S)
    if m:
        fn = m.group(1).lower()
        pr = toks_pairs(m.group(2))
        if not pr:
            raise UE(s[:40])
        out = []
        for y in YEARS:
            if fn == "add":
                out.append(sum(v for yy, v in pr if yy <= y))
            elif fn == "step":
                vs = [v for yy, v in pr if yy <= y]
                out.append(vs[-1] if vs else 0.0)
            else:
                if y <= pr[0][0]:
                    out.append(pr[0][1])
                elif y >= pr[-1][0]:
                    out.append(pr[-1][1])
                else:
                    for (y1, v1), (y2, v2) in zip(pr, pr[1:]):
                        if y1 <= y <= y2:
                            out.append(v1 + (v2 - v1) * (y - y1) / (y2 - y1))
                            break
        return out
    m = re.fullmatch(r"(Max|Min)\s*\((.*)\)", s, re.I | re.S)
    if m:
        args, d, cur = [], 0, ""
        for ch in m.group(2):
            if ch == "(":
                d += 1
            if ch == ")":
                d -= 1
            if ch == "," and d == 0:
                args.append(cur)
                cur = ""
            else:
                cur += ch
        args.append(cur)
        se = [ev(a.strip(), rg, lf, var, depth + 1) for a in args]
        f = max if m.group(1).lower() == "max" else min
        return [f(col) for col in zip(*se)]
    m = re.fullmatch(r"Value\s*\(\s*(\d{4})\s*\)", s, re.I)
    if m:
        y = int(m.group(1))
        ca, _, _ = eff(rg, lf, var, tiers=["Current Accounts"])
        if ca is None:
            raise UE("Value(%d): CA empty for %s" % (y, var))
        vs = ev(ca, rg, lf, var, depth + 1)
        yr = min(max(y, YEARS[0]), YEARS[-1])
        return [vs[YEARS.index(yr)]] * len(YEARS)
    m = re.fullmatch(r"(?:(.+?):)?\s*([A-Za-z][A-Za-z _]*?)\s*\[[^\]]*\]", s)
    if m:
        ref_branch, ref_var = m.group(1), m.group(2).strip()
        tgt = leaf(ref_branch.strip()) if ref_branch else lf
        e, _, _ = eff(rg, tgt, ref_var)
        if e is None:
            raise UE("ref %s:%s EMPTY" % (tgt, ref_var))
        if tgt == lf and ref_var == var:
            raise UE("self-ref " + var)
        return ev(e, rg, tgt, ref_var, depth + 1)
    raise UE(s[:60])

tree = (REPO / "LEAP structure/trees/transformation_tree.txt").read_text(
    encoding="utf-8").splitlines()
def dp(l): return (len(l) - len(l.lstrip(" "))) // 2
def nm(l): return l.lstrip(" ").split("   [vars:")[0].strip()
procs, blk = set(), None
for l in tree:
    if dp(l) == 1:
        blk = nm(l)
    elif dp(l) == 3 and blk in ("Centralized Electricity Generation",
                                "Distributed Electricity Generation"):
        procs.add(nm(l))

def valid(rg, lf):
    for pat, home in NODE_REGION_LOCK.items():
        if pat.search(lf):
            return rg == home
    return lf not in BASE_BRANCH_NODE_ONLY.get(rg, frozenset())

SAFE = re.compile(r"^Exogenous Capacity\s*\[[^\]]*\]\s*(\+.*)?$")
viol, unknown, ok, safe = [], [], 0, 0
for rg in AMS10:
    for lf in sorted(procs):
        if not valid(rg, lf):
            continue
        mc, mcl, mct = eff(rg, lf, "Maximum Capacity")
        if mc is None or "unlimited" in mc.lower():
            continue
        if SAFE.match(sc_(mc)):
            safe += 1
            continue
        exo, _, _ = eff(rg, lf, "Exogenous Capacity")
        if exo is None:
            ok += 1
            continue
        try:
            mcv = ev(mc, rg, lf, "Maximum Capacity")
            exv = ev(exo, rg, lf, "Exogenous Capacity")
        except UE as e:
            unknown.append((rg, lf, str(e)[:70], mc[:60]))
            continue
        br = [(y, e_, m_) for y, e_, m_ in zip(YEARS, exv, mcv)
              if e_ > m_ + 1e-9]
        if br:
            viol.append((rg, lf, br[0][0], br[0][2], br[0][1],
                         max(b[1] for b in br), mc))
        else:
            ok += 1

print("caps checked: safe-formula=%d  evaluated-OK=%d  VIOLATIONS=%d  UNRESOLVED=%d\n"
      % (safe, ok, len(viol), len(unknown)))
print("=== ALL VIOLATIONS (RAS-effective, full evaluation) ===")
for rg, lf, y0, m0, e0, pk, mc in sorted(viol):
    print("%-12s%-26s 1st=%d  cap@1st=%.1f  exo@1st=%.1f  exoPeak=%.1f"
          % (rg, lf, y0, m0, e0, pk))
    print("    current cap expr: " + mc)
print("\n=== UNRESOLVED (honest list) ===")
for u in unknown:
    print("  %-12s%-26s %s | cap=%s" % u)
