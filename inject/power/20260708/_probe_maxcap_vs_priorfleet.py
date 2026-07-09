"""Comprehensive MaxCap-vs-fleet sweep — our inject doc x the prior input.

For EVERY Maximum Capacity row in the joint delta (RAS), compare against the
exogenous fleet that PREVIOUSLY sat on that tech. Fleet source, in priority:
  (1) if the delta re-authors Existing/Additions/Retirement/Exo for the tech
      -> re-evaluate the NEW merged Exo expression (fleet changed);
  (2) else -> the authoritative ResidualCapacity from the last solved DB
      (feas/NEMO_25 41.sqlite), i.e. the actual input previously sitting on it.
MaxCap forms: numeric -> value; Max(Exo, N) / bare Exo-ref -> = fleet (safe by
construction); cross-branch ref -> resolve. Absent building block = LEAP
default 0 (FLAGGED, never a parse-failure guess). Flag MaxCap < fleet.
"""
import csv, re, sqlite3
from pathlib import Path
REPO = Path(__file__).resolve().parents[3]
BS = chr(92)
YEARS = list(range(2023, 2061))
AMS10 = ["Brunei","Cambodia","Indonesia","Laos","Malaysia","Myanmar",
         "Philippines","Singapore","Thailand","Vietnam"]
WIDE = {"CA":"Current Accounts","BAS":"Baseline Simulation",
        "ATS":"AMS Target Scenario","RAS":"Regional Aspiration Scenario"}
CAPVARS = {"Maximum Capacity","Exogenous Capacity","Existing Capacity",
           "Capacity Additions","Capacity Retirement"}
def leaf(b): return b.rstrip(BS).split(BS)[-1].strip()

state = {}
def put(rg, lf, var, sc, ex):
    ex = (ex or "").strip()
    if ex: state[(rg, lf, var, sc)] = ex
def load_wide(p):
    for r in csv.DictReader(open(p, encoding="utf-8-sig")):
        if r.get("variable") not in CAPVARS: continue
        for col, sc in WIDE.items():
            put(r["region"].strip(), r["node"].strip(), r["variable"].strip(), sc, r.get(col))
def load_long(p):
    rdr = csv.DictReader(open(p, encoding="utf-8-sig"))
    f = {k.lower().replace(" ","_"): k for k in rdr.fieldnames}
    bc = f.get("branch") or f.get("branch_path"); rc = f.get("ams") or f.get("region")
    for r in rdr:
        if (r[f['variable']] or "").strip() not in CAPVARS: continue
        regs = AMS10 if (r[rc] or "").startswith("ALL") else [(r[rc] or "").strip()]
        for rg in regs:
            put(rg, leaf(r[bc] or ""), (r[f['variable']] or "").strip(),
                (r[f['scenario']] or "").strip(), r[f['expression']])
H = REPO / "inject/power/structure_handover_20260703"
load_wide(H / "processes_full_dataset_4scenarios.csv")
load_long(H / "current_expressions_transformation_slice_4scenarios.csv")
load_long(H / "current_expressions_transformation_indonesia_nodes_4scenarios.csv")
load_long(REPO / "inject/power/20260707/power_sendback_canonical.csv")
DELTA_FILES = ["power_batch1_delta_20260708.csv",
               "power_batch1b_endogenous_ATS_BAS_delta_20260708.csv",
               "exo_negative_fix_ats_delta.csv"]
delta_keys = set()  # (rg, lf, var, scen) our inject doc actually edits
for bf in DELTA_FILES:
    p = REPO / "inject/power/20260708" / bf
    for r in csv.DictReader(open(p, encoding="utf-8-sig")):
        if (r["variable"] or "").strip() not in CAPVARS: continue
        put(r["ams"].strip(), leaf(r["branch"]), r["variable"].strip(),
            r["scenario"].strip(), r["expression"])
        delta_keys.add((r["ams"].strip(), leaf(r["branch"]), r["variable"].strip(), r["scenario"].strip()))

# prior fleet from the last solved DB (ResidualCapacity, GW -> MW)
db = sqlite3.connect(REPO / "feas/NEMO_25 41.sqlite"); cur = db.cursor()
prior_fleet = {}  # (region, tech) -> {year: MW}
for rgn, tech, y, val in cur.execute(
        """SELECT r.desc, t.desc, rc.y, rc.val FROM ResidualCapacity rc
           JOIN REGION r ON r.val=rc.r JOIN TECHNOLOGY t ON t.val=rc.t"""):
    prior_fleet.setdefault((rgn, tech), {})[str(y)] = val * 1000.0

NUM = r"-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?"
class UE(Exception): pass
ABSENT = set()
def eff(rg, lf, var, scen):
    for s in (scen, "Current Accounts"):
        if (rg, lf, var, s) in state: return state[(rg, lf, var, s)]
    return None
def ev(expr, rg, lf, var, scen, d=0, allow_absent=False):
    if d > 9: raise UE("depth")
    s = expr.split("?")[0].strip()
    if not s: raise UE("empty")
    s = re.sub(r"("+NUM+r")\s*%", lambda m:"("+repr(float(m.group(1))/100)+")", s)
    def sp(x, seps):
        o, dd, c, i = [], 0, "", 0
        while i < len(x):
            ch = x[i]
            if ch == "(": dd += 1
            if ch == ")": dd -= 1
            un = (ch == "-" and (not c.strip() or c.rstrip()[-1:] in "+-*/(,"))
            if dd == 0 and ch in seps and not un: o.append(c); o.append(ch); c = ""
            else: c += ch
            i += 1
        o.append(c); return o
    for ops in ("+-", "*/"):
        parts = sp(s, ops)
        if len(parts) > 1:
            tot = ev(parts[0], rg, lf, var, scen, d+1, allow_absent)
            for op, tm in zip(parts[1::2], parts[2::2]):
                tv = ev(tm, rg, lf, var, scen, d+1, allow_absent)
                if op == "+": tot = [a+b for a,b in zip(tot,tv)]
                elif op == "-": tot = [a-b for a,b in zip(tot,tv)]
                elif op == "*": tot = [a*b for a,b in zip(tot,tv)]
                else: tot = [a/b if b else float("inf") for a,b in zip(tot,tv)]
            return tot
    s = s.strip()
    if s.startswith("(") and s.endswith(")"): return ev(s[1:-1], rg, lf, var, scen, d+1, allow_absent)
    if re.fullmatch(NUM, s): return [float(s)]*len(YEARS)
    m = re.fullmatch(r"(Interp|Step|Add)\s*\((.*)\)", s, re.I|re.S)
    if m:
        fn = m.group(1).lower(); nums = [float(x) for x in re.findall(NUM, m.group(2))]
        pr = list(zip(nums[0::2], nums[1::2]))
        if not pr: raise UE("pairs")
        out = []
        for y in YEARS:
            if fn == "add": out.append(sum(v for yy,v in pr if yy <= y))
            elif fn == "step":
                vs = [v for yy,v in pr if yy <= y]; out.append(vs[-1] if vs else 0.0)
            else:
                if y <= pr[0][0]: out.append(pr[0][1])
                elif y >= pr[-1][0]: out.append(pr[-1][1])
                else:
                    for (y1,v1),(y2,v2) in zip(pr, pr[1:]):
                        if y1 <= y <= y2: out.append(v1+(v2-v1)*(y-y1)/(y2-y1)); break
        return out
    m = re.fullmatch(r"(Max|Min)\s*\((.*)\)", s, re.I|re.S)
    if m:
        args, dd, c = [], 0, ""
        for ch in m.group(2):
            if ch == "(": dd += 1
            if ch == ")": dd -= 1
            if ch == "," and dd == 0: args.append(c); c = ""
            else: c += ch
        args.append(c)
        se = [ev(a.strip(), rg, lf, var, scen, d+1, allow_absent) for a in args]
        f = max if m.group(1).lower() == "max" else min
        return [f(col) for col in zip(*se)]
    m = re.fullmatch(r"Value\s*\(\s*(\d{4})\s*\)", s, re.I)
    if m:
        y = int(m.group(1)); ca = eff(rg, lf, var, "Current Accounts")
        if ca is None:
            if allow_absent: ABSENT.add((rg, lf, var)); return [0.0]*len(YEARS)
            raise UE("Value()-CA-empty")
        vs = ev(ca, rg, lf, var, scen, d+1, allow_absent)
        yy = min(max(y, YEARS[0]), YEARS[-1]); return [vs[YEARS.index(yy)]]*len(YEARS)
    m = re.fullmatch(r"(?:(.+?):)?\s*([A-Za-z][A-Za-z _]*?)\s*\[[^\]]*\]", s)
    if m:
        tgt = leaf(m.group(1).strip()) if m.group(1) else lf; rv = m.group(2).strip()
        e = eff(rg, tgt, rv, scen)
        if e is None:
            if allow_absent and rv in CAPVARS: ABSENT.add((rg, tgt, rv)); return [0.0]*len(YEARS)
            raise UE("ref %s:%s" % (tgt, rv))
        if tgt == lf and rv == var: raise UE("self")
        return ev(e, rg, tgt, rv, scen, d+1, allow_absent)
    raise UE(s[:40])

def fleet_of(rg, lf):
    """New Exo if delta changed the tech's fleet inputs, else prior ResidualCapacity."""
    changed = any((rg, lf, v, "Regional Aspiration Scenario") in delta_keys
                  for v in ("Existing Capacity","Capacity Additions","Capacity Retirement","Exogenous Capacity"))
    if changed:
        exo = eff(rg, lf, "Exogenous Capacity", "Regional Aspiration Scenario")
        if exo:
            try: return dict(zip(YEARS, ev(exo, rg, lf, "Exogenous Capacity",
                                           "Regional Aspiration Scenario", allow_absent=True))), "new-Exo"
            except UE: pass
    pf = prior_fleet.get((rg, lf))
    if pf: return {int(y): v for y, v in pf.items()}, "prior-ResidualCapacity"
    # fall back to evaluating merged Exo
    exo = eff(rg, lf, "Exogenous Capacity", "Regional Aspiration Scenario")
    if exo:
        try: return dict(zip(YEARS, ev(exo, rg, lf, "Exogenous Capacity",
                                       "Regional Aspiration Scenario", allow_absent=True))), "merged-Exo"
        except UE: pass
    return None, "NO-FLEET"

breaches, safe, nofleet = [], 0, []
for (rg, lf, var, scen) in sorted(delta_keys):
    if var != "Maximum Capacity" or scen != "Regional Aspiration Scenario": continue
    mc_expr = eff(rg, lf, "Maximum Capacity", scen)
    fl, fsrc = fleet_of(rg, lf)
    if fl is None: nofleet.append((rg, lf)); continue
    try:
        mc = ev(mc_expr, rg, lf, "Maximum Capacity", scen, allow_absent=True)
    except UE as e:
        breaches.append((rg, lf, "UNEVAL-CAP", str(e), fsrc, mc_expr[:45])); continue
    bad = [(y, mc[i], fl.get(y, 0.0)) for i, y in enumerate(YEARS)
           if fl.get(y, 0.0) - mc[i] > 1.0]  # fleet exceeds cap by >1 MW
    if bad:
        y0, c0, f0 = bad[0]
        breaches.append((rg, lf, y0, c0, f0, max(b[2]-b[1] for b in bad), fsrc, mc_expr[:40]))
    else: safe += 1

print("MaxCap rows in delta checked: safe=%d  BREACHES=%d  no-fleet=%d\n" % (safe, len(breaches), len(nofleet)))
print("=== MaxCap < prior fleet (RAS) — THE VIOLATIONS ===")
if not breaches: print("  none")
for b in sorted(breaches):
    if len(b) == 6:
        print("  %-11s %-24s UNEVALUABLE cap (%s) [%s] %s" % (b[0], b[1], b[3], b[4], b[5]))
    else:
        rg, lf, y0, c0, f0, gap, fsrc, ex = b
        print("  %-11s %-24s @%d cap=%.0f < fleet=%.0f (gap %.0f)  [%s]  cap-expr=%s"
              % (rg, lf, y0, c0, f0, gap, fsrc, ex))
if ABSENT:
    print("\n=== building blocks taken as LEAP-default 0 (absent everywhere) ===")
    for a in sorted(ABSENT)[:20]: print("  ", a)
