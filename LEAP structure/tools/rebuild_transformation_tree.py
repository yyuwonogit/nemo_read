"""Rebuild trees/transformation_tree.txt by UNIONing the main Malaysia-scoped
transformation export with every region-specific supplement export
(`LEAP Input Transformation <Region>.xlsx`). Region-specific exports surface
sub-national process-node variants (`_MYxx`, `_IDxx`, ...) that a single
region-scoped export misses — see CLAUDE.md §11.1 + memory
reference_region_scoped_export. All exports share the branch_path convention,
so the union is clean.

Run from anywhere:  python rebuild_transformation_tree.py
Adds a new region: drop `LEAP Input Transformation <Region>.xlsx` next to the
main file; it is auto-discovered by the glob below.
"""
import sys, io, zipfile, re, glob
from pathlib import Path
from xml.etree.ElementTree import iterparse

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
BS = chr(92)
SRC = Path(__file__).resolve().parent.parent           # LEAP structure/
MAIN = SRC / "LEAP Input Transformation.xlsx"
TREE = SRC / "trees" / "transformation_tree.txt"

def shared(z):
    ss = []
    for ev, el in iterparse(io.BytesIO(z.read("xl/sharedStrings.xml"))):
        if el.tag.endswith("si"):
            ss.append("".join(t.text or "" for t in el.iter() if t.tag.endswith("t"))); el.clear()
    return ss

def stream(path):
    z = zipfile.ZipFile(path)
    ss = shared(z)
    bv = {}
    rownum = 0; cur = {}
    for ev, el in iterparse(z.open("xl/worksheets/sheet1.xml"), events=("start", "end")):
        tag = el.tag.split("}")[-1]
        if ev == "start" and tag == "row":
            cur = {}
        elif ev == "end" and tag == "c":
            ref = el.attrib.get("r", ""); m = re.match(r"([A-Z]+)", ref); L = m.group(1) if m else ""
            if L in ("E", "F"):
                t = el.attrib.get("t"); v = el.find("{*}v")
                if v is not None and v.text is not None:
                    cur[L] = ss[int(v.text)] if t == "s" else v.text
            el.clear()
        elif ev == "end" and tag == "row":
            rownum += 1
            if rownum >= 4 and cur.get("E"):
                bv.setdefault(cur["E"], set()).add(cur.get("F", ""))
            el.clear()
    return bv

merged = {}
sources = [MAIN] + sorted(Path(p) for p in glob.glob(str(SRC / "LEAP Input Transformation *.xlsx")))
for p in sources:
    print(f"streaming {p.name} ...", flush=True)
    bv = stream(p)
    for k, v in bv.items():
        merged.setdefault(k, set()).update(v)
    print(f"  {len(bv)} branches; running union = {len(merged)}", flush=True)

lines = []
for bp in sorted(merged, key=lambda s: s.lower()):
    parts = bp.split(BS)
    indent = "  " * (len(parts) - 1)
    vs = ";".join(sorted(x for x in merged[bp] if x))
    lines.append(f"{indent}{parts[-1]}   [vars: {vs}]")
TREE.write_text("\n".join(lines) + "\n", encoding="utf-8")

id_nodes = sorted(set(p.split(BS)[-1] for p in merged if re.search(r"_ID[A-Z]", p.split(BS)[-1])))
my_nodes = sorted(set(p.split(BS)[-1] for p in merged if re.search(r"_MY[A-Z]", p.split(BS)[-1])))
print(f"\nwrote {TREE} : {len(lines)} branches")
print(f"  Indonesia _ID* process nodes: {len(id_nodes)} | Malaysia _MY* process nodes: {len(my_nodes)}")
