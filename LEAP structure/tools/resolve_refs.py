"""Cross-check: every Key\\... and Resources\\... reference inside the four
demand-sector expressions vs the branches (and variables) actually present in
the keys/resources exports. Writes ref_resolution.csv + prints a summary."""
import sys, io, csv, re
from collections import defaultdict, Counter
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
csv.field_size_limit(10_000_000)
DIG = Path(r"C:\Users\ThinkPad\AppData\Local\Temp\claude\c--Users-ThinkPad-Desktop-Py-YY-NEMO-read\fdb165f2-ee08-4c70-936a-5e3894ab9b7c\scratchpad\digest")

# Reference forms: Prefix\Path\To\Branch:Variable Name[unit]  or bare Prefix\Path[unit]
REF_RE = re.compile(r"((?:Key|Resources)\\[^:\[\]()+*/,?]+)(?::([^\[\]()+*/,:\\]+))?")

def load_targets(sector):
    """branch_path -> set of variables, from the digest branches csv."""
    out = {}
    with open(DIG / f"{sector}_branches.csv", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            out[r["branch_path"].strip()] = set(v for v in r["variables"].split(";") if v)
    return out

keys_b = load_targets("keys")
res_b = load_targets("resources")

refs = defaultdict(Counter)   # (branch, variable) -> Counter(sector)
for sector in ["commercial", "transport", "residential", "industry"]:
    with open(DIG / f"{sector}_rows.csv", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            for m in REF_RE.finditer(row["expression"]):
                bp = m.group(1).strip().rstrip("\\").strip()
                var = (m.group(2) or "").strip()
                refs[(bp, var)][sector] += 1

def status(bp, var):
    tgt = keys_b if bp.startswith("Key\\") else res_b
    if bp not in tgt:
        return "BRANCH_MISSING"
    if var and var not in tgt[bp]:
        return "VAR_MISSING_ON_BRANCH"
    return "OK"

rows_out = []
for (bp, var), cnt in sorted(refs.items()):
    st = status(bp, var)
    rows_out.append({
        "referenced_branch": bp, "referenced_variable": var, "status": st,
        "commercial": cnt.get("commercial", 0), "transport": cnt.get("transport", 0),
        "residential": cnt.get("residential", 0), "industry": cnt.get("industry", 0),
        "total": sum(cnt.values()),
    })

with open(DIG / "ref_resolution.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows_out[0].keys()))
    w.writeheader()
    w.writerows(rows_out)

sc = Counter(r["status"] for r in rows_out)
print("Distinct (branch, variable) references:", len(rows_out), dict(sc))
print()
for st in ["BRANCH_MISSING", "VAR_MISSING_ON_BRANCH"]:
    bad = [r for r in rows_out if r["status"] == st]
    print(f"--- {st}: {len(bad)}")
    for r in bad[:40]:
        print(f"  {r['referenced_branch']}  :{r['referenced_variable']}  "
              f"(total {r['total']}: c{r['commercial']}/t{r['transport']}/r{r['residential']}/i{r['industry']})")
