"""Build an inject CSV that aligns LEAP Existing Capacity to the
authoritative source-of-truth: mailbox/existing_cap_historical_prod.xlsx.

Output: inject_existing_capacity.csv in the canonical inject format
(same columns as mailbox/bioenergy/canonical_leap_inputs.csv).

Logic:
  1. Read xlsx Mapping sheet → native-tech → LEAP-std-tech map per country.
  2. Read each country sheet (rows = native tech, cols = years 2005-2024).
  3. Translate native names to LEAP-std names.
  4. For each (country, leap_tech, year) build target MW.
  5. Generate an Existing Capacity Interp() expression covering 2005-2024.
  6. Routing per country:
     - 9 non-ID/MY countries: emit one row per (country, tech) at root branch
       Transformation\Centralized Electricity Generation\Processes\<tech>
     - Indonesia: redistribute the country total across existing nodes
       (_IDJW, _IDKA, _IDSA, _IDEast) using current Energy Generation
       proportions from joined_BAS.csv as the distribution proxy. If no
       current node activity, equal-split + flag note.
     - Malaysia: nodes don't exist yet in v0.36 (per IN file). Emit a
       zero-out for root AND a follow-up note row marked
       "needs_node_split_first". These rows are tagged so the power team
       can stage them: zero now, populate per-node after structural work.

Caveats called out in cover note:
  - xlsx covers 2005-2024 (historical). Projection years (2025+) come
    from LEAP-side Capacity Additions/Retirement; not in scope here.
  - For ID nodes, distribution proxy uses 2025 Energy Generation from
    joined_BAS.csv. If current LEAP nodes have no Energy Generation
    (post-workaround), we fall back to equal split.
  - Tech names not present in xlsx (e.g. CAES, Bioenergy with CCS) →
    not injected; existing LEAP value preserved.
"""
from __future__ import annotations
import csv
import warnings
from pathlib import Path
from collections import defaultdict
import pandas as pd

warnings.filterwarnings("ignore")

XLSX = Path(r"mailbox/existing_cap_historical_prod.xlsx")
JOINED_BAS = Path(r"mailbox/20260505/joined_BAS.csv")
OUT_INJECT = Path(r"mailbox/20260505/inject_existing_capacity_round1_other_AMS.csv")
OUT_AUDIT = Path(r"mailbox/20260505/audit_country_totals.csv")

COUNTRIES = ("Brunei", "Cambodia", "Indonesia", "Laos", "Malaysia",
             "Myanmar", "Philippines", "Singapore", "Thailand", "Vietnam")
NODE_COUNTRIES = {"Indonesia": ("_IDJW", "_IDKA", "_IDSA", "_IDEast"),
                  "Malaysia":  ("_MYP", "_MYS", "_MYK")}  # tentative MY suffixes
YEARS = list(range(2005, 2025))


# --------------------------------------------------------------------------
# Step 1: Mapping table — native tech name (per country) → LEAP std name
# --------------------------------------------------------------------------
def load_mapping() -> tuple[dict, set]:
    """Returns ({country: {native_tech: leap_std_tech}}, set_of_all_leap_std_names)"""
    df = pd.read_excel(XLSX, sheet_name="Mapping", header=None)
    country_cols: dict[str, int] = {}
    for c in range(2, 13):
        v = df.iat[1, c]
        if isinstance(v, str) and v.strip():
            country_cols[v.strip()] = c
    out: dict[str, dict[str, str]] = {c: {} for c in country_cols}
    all_leap_std: set = set()
    for r in range(2, len(df)):
        leap_std = df.iat[r, 1]
        if not isinstance(leap_std, str) or not leap_std.strip():
            continue
        leap_std = leap_std.strip()
        all_leap_std.add(leap_std)
        for country, c in country_cols.items():
            native = df.iat[r, c]
            if isinstance(native, str) and native.strip():
                out[country][native.strip()] = leap_std
    return out, all_leap_std


def normalize_tech_name(native: str, country_map: dict, all_leap_std: set) -> str | None:
    """Resolve native → LEAP-std with fallbacks.

    Order of attempts:
      1. Direct lookup in country_map.
      2. Native name IS a LEAP-std name (e.g. Indonesia uses "Coal Subcritical"
         literally; no Mapping entry needed).
      3. Strip parenthetical suffix (e.g. "Coal Ultrasupercritical (USC)" →
         "Coal Ultrasupercritical") and retry both.
      4. Give up — return None (caller skips).
    """
    if native in country_map:
        return country_map[native]
    if native in all_leap_std:
        return native
    # Strip parentheticals
    import re
    base = re.sub(r"\s*\([^)]*\)\s*$", "", native).strip()
    if base != native:
        if base in country_map:
            return country_map[base]
        if base in all_leap_std:
            return base
    return None


# --------------------------------------------------------------------------
# Step 2: Load country sheets — native tech × year MW
# --------------------------------------------------------------------------
def load_country_truth(mapping: dict, all_leap_std: set) -> dict:
    """Returns {country: {leap_std_tech: {year: MW}}}"""
    truth: dict = defaultdict(lambda: defaultdict(dict))
    skipped: dict = defaultdict(set)
    for country in COUNTRIES:
        try:
            df = pd.read_excel(XLSX, sheet_name=country)
        except Exception as e:
            print(f"  WARNING: cannot read sheet {country!r}: {e}")
            continue
        if "Technology" not in df.columns:
            continue
        country_map = mapping.get(country, {})
        for _, row in df.iterrows():
            native = row["Technology"]
            if not isinstance(native, str) or not native.strip():
                continue
            native = native.strip()
            leap_std = normalize_tech_name(native, country_map, all_leap_std)
            if not leap_std:
                skipped[country].add(native)
                continue
            for y in YEARS:
                # Year columns can be int or str depending on excel read
                col = y if y in df.columns else (str(y) if str(y) in df.columns else None)
                if col is None:
                    continue
                v = row[col]
                try:
                    v = float(v)
                    if pd.notna(v):
                        truth[country][leap_std][y] = v
                except (TypeError, ValueError):
                    pass
    if skipped:
        print(f"\n  Tech names skipped (not in Mapping AND not in LEAP-std):")
        for c, ts in skipped.items():
            print(f"    {c}: {sorted(ts)[:8]}{'...' if len(ts) > 8 else ''}")
    return dict(truth)


# --------------------------------------------------------------------------
# Step 3: Distribution proxies for Indonesia nodes
# --------------------------------------------------------------------------
def load_id_node_proxy() -> dict:
    """Use 2025 Energy Generation per (Indonesia, _IDxx branch) from joined_BAS.csv
    to infer node distribution shape for each tech.
    Returns {leap_tech: {node_suffix: proportion}}.
    """
    proxy: dict = defaultdict(lambda: defaultdict(float))
    with JOINED_BAS.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["ams"] != "Indonesia":
                continue
            if r["variable"] != "Energy Generation":
                continue
            if r["year"] != "2025":
                continue
            leaf = r["branch"].rsplit("\\", 1)[-1]
            for suf in NODE_COUNTRIES["Indonesia"]:
                if leaf.endswith(suf):
                    tech = leaf[: -len(suf)]
                    proxy[tech][suf] += float(r["value"])
                    break
    # Normalize per tech
    norm: dict = {}
    for tech, suf_d in proxy.items():
        total = sum(suf_d.values())
        if total > 0:
            norm[tech] = {s: v / total for s, v in suf_d.items()}
    return norm


# --------------------------------------------------------------------------
# Step 4: Build inject rows
# --------------------------------------------------------------------------
def fmt_interp(year_val: dict[int, float]) -> str:
    """Build Interp(2005, V05, ..., 2024, V24) — only years with data."""
    parts = []
    for y in sorted(year_val):
        v = year_val[y]
        # Trim trailing .0 for cleaner inject text
        s = f"{v:.6f}".rstrip("0").rstrip(".")
        if not s:
            s = "0"
        parts.append(f"{y}, {s}")
    return f"Interp({', '.join(parts)})"


def root_branch(tech: str) -> str:
    return rf"Transformation\Centralized Electricity Generation\Processes\{tech}"


def node_branch(tech: str, suf: str) -> str:
    return rf"Transformation\Centralized Electricity Generation\Processes\{tech}{suf}"


def build_inject(truth: dict, id_proxy: dict) -> list[dict]:
    """ROUND 1 (per user direction 2026-05-05): handle 8 non-ID/MY AMS only.
    Indonesia + Malaysia are deferred to ROUND 2 (which must combine
    root EC=0 + root HP=0 in Current Accounts to avoid recreating the
    v0.35 Historical-Production-without-Existing-Capacity infeasibility).
    """
    rows = []
    skipped_id_my = 0
    for country, tech_d in truth.items():
        if country in ("Indonesia", "Malaysia"):
            skipped_id_my += sum(1 for y_d in tech_d.values() if y_d)
            continue
        for tech, year_d in tech_d.items():
            if not year_d:
                continue
            rows.append(_make_row(
                country, root_branch(tech),
                expression=fmt_interp(year_d),
                note=f"Round 1 — align historical Existing Capacity to source-of-truth xlsx (Current Accounts)",
                confidence="High"))
    if skipped_id_my:
        print(f"  [round 1] skipping {skipped_id_my} ID/MY (country, tech) combos — deferred to round 2")
    return rows


def _make_row(ams, branch, expression, note,
              confidence="High", data_confidence=None) -> dict:
    return {
        "ams": ams,
        "branch": branch,
        "variable": "Existing Capacity",
        "expression": expression,
        "unit": "Megawatt",
        "fuel": "",
        "source": "existing_cap_historical_prod.xlsx (mailbox source-of-truth, 2026-05-05)",
        "note": note,
        "src_csv": "existing_cap_historical_prod.xlsx",
        "domain": "power_existing_capacity",
        "data_confidence": data_confidence or confidence,
    }


# --------------------------------------------------------------------------
# Step 5: Audit — country totals 2024 (current vs truth)
# --------------------------------------------------------------------------
def write_audit(truth: dict) -> None:
    # For non-ID/MY countries, current "root" 2025 EC from joined_BAS as a proxy
    # for what's authored. For ID/MY, get sum across all nodes (since root is
    # zero per workaround; we want to know if node sum matches truth).
    current = defaultdict(lambda: defaultdict(float))
    with JOINED_BAS.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["variable"] != "Existing Capacity":
                continue
            if r["year"] != "2025":
                continue
            ams = r["ams"]
            leaf = r["branch"].rsplit("\\", 1)[-1]
            # Strip _IDxx / _MY* suffix to identify the parent tech
            tech = leaf
            for suf_set in NODE_COUNTRIES.values():
                for suf in suf_set:
                    if leaf.endswith(suf):
                        tech = leaf[: -len(suf)]
                        break
            current[ams][tech] += float(r["value"])

    rows = []
    for country, tech_d in truth.items():
        for tech, year_d in tech_d.items():
            tr_2024 = year_d.get(2024, 0)
            cur = current.get(country, {}).get(tech, 0)
            delta = tr_2024 - cur
            rows.append({
                "country": country, "leap_tech": tech,
                "truth_2024_MW": round(tr_2024, 3),
                "current_2025_MW": round(cur, 3),
                "delta_MW": round(delta, 3),
                "pct_diff": "" if not tr_2024 else f"{(delta/tr_2024*100 if tr_2024 else 0):.1f}%"
            })
    rows.sort(key=lambda r: (r["country"], r["leap_tech"]))
    fields = ["country","leap_tech","truth_2024_MW","current_2025_MW","delta_MW","pct_diff"]
    with OUT_AUDIT.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(rows)


# --------------------------------------------------------------------------
# Run
# --------------------------------------------------------------------------
def main():
    print("=== loading mapping ===")
    mapping, all_leap_std = load_mapping()
    n_countries = len(mapping)
    n_pairs = sum(len(d) for d in mapping.values())
    print(f"  {n_countries} countries, {n_pairs} (country, native_tech) translations, "
          f"{len(all_leap_std)} distinct LEAP-std tech names")

    print("\n=== loading country source-of-truth tables ===")
    truth = load_country_truth(mapping, all_leap_std)
    for c in COUNTRIES:
        if c in truth:
            print(f"  {c:<14}: {len(truth[c])} techs with historical EC data")

    print("\n=== loading Indonesia node distribution proxy ===")
    id_proxy = load_id_node_proxy()
    print(f"  {len(id_proxy)} Indonesia techs with node-distribution data from joined_BAS")

    print("\n=== building inject rows ===")
    rows = build_inject(truth, id_proxy)
    print(f"  {len(rows)} total inject rows")
    by_ams = defaultdict(int)
    by_kind = defaultdict(int)
    for r in rows:
        by_ams[r["ams"]] += 1
        if r["expression"] == "0":
            by_kind["zero_out_root"] += 1
        elif r["data_confidence"] == "STAGED":
            by_kind["staged_for_after_structural"] += 1
        elif "node-split" in r["note"]:
            by_kind["node_distributed"] += 1
        else:
            by_kind["root_aligned"] += 1
    print(f"  by ams: {dict(by_ams)}")
    print(f"  by kind: {dict(by_kind)}")

    fields = ["ams","branch","variable","expression","unit","fuel",
              "source","note","src_csv","domain","data_confidence"]
    with OUT_INJECT.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(rows)
    print(f"\n  wrote inject CSV: {OUT_INJECT}")

    print("\n=== writing audit (truth_2024 vs current_2025) ===")
    write_audit(truth)
    print(f"  wrote: {OUT_AUDIT}")


if __name__ == "__main__":
    main()
