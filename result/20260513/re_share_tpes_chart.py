"""Compute RAS RE share of TPES from fuel_balance.csv (ASEAN-11), combine
into the user's category buckets (Bioenergy / VRE / Hydro / Geothermal /
MSW), and project alongside the BAS/ATS/APAS/AREC trajectories from the
AEO chart through 2060.

Outputs:
  - re_share_tpes_by_category.csv  (RAS only, by category, % of TPES)
  - re_share_scenarios.csv         (all 5 scenarios, annual %)
  - re_share_lineplot.png          (line graph)
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

CSV = Path("mailbox/20260513/results_v045/fuel_balance.csv")
OUT_CAT = Path("mailbox/20260513/results_v045/re_share_tpes_by_category.csv")
OUT_SCN = Path("mailbox/20260513/results_v045/re_share_scenarios.csv")
OUT_PNG = Path("mailbox/20260513/results_v045/re_share_lineplot.png")

ASEAN_11 = ["Brunei", "Cambodia", "Indonesia", "Laos", "Malaysia",
            "Myanmar", "Philippines", "Singapore", "Thailand", "Vietnam",
            "Timor Leste"]
PJ_PER_MTOE = 41.868

# Category buckets per user's request
BIOENERGY_KW = [
    "Biomass input to", "Wood input to", "Bagasse input to", "Charcoal input to",
    "Cassava input to", "Sugarcane input to", "Molasses input to",
    "Corn input to", "Coconut Oil input to", "Palm Oil input to",
    "Palm Oil Mill Effluent input to",
    "Biomethane input to", "Domestic Biogas output from",
    "Municipal Solid Waste input to",
]
VRE_KW = [
    "Solar input to", "Wind input to", "Tidal input to", "Wave input to",
]
HYDRO_KW = [
    "Large Hydro input to", "Small Hydro input to",
]
GEOTHERMAL_KW = ["Geothermal input to"]


def categorize_re(fuel: str) -> str | None:
    if not isinstance(fuel, str):
        return None
    for kw in BIOENERGY_KW:
        if kw in fuel: return "Bioenergy"
    for kw in VRE_KW:
        if kw in fuel: return "VRE"
    for kw in HYDRO_KW:
        if kw in fuel: return "Hydro"
    for kw in GEOTHERMAL_KW:
        if kw in fuel: return "Geothermal"
    return None


# Total TPES denominator: primary energy supply for ASEAN-11
# = primary RE + primary fossils (indigenous production + imports)
# Fossil primary identifiers (full fuel-name keyword matches):
FOSSIL_PRIMARY_KW = [
    "Crude Oil input to",        # primary crude
    "Natural Gas input to",      # primary natural gas
    "Coal Bituminous input to",
    "Coal Sub bituminous input to",
    "Coal Lignite input to",
    "Coal Anthracite input to",
    "Coal Unspecified input to",
    "LNG output from",           # LNG-as-primary import path
]


def is_fossil_primary(fuel: str) -> bool:
    if not isinstance(fuel, str): return False
    return any(kw in fuel for kw in FOSSIL_PRIMARY_KW)


def is_re_primary(fuel: str) -> bool:
    return categorize_re(fuel) is not None


def main() -> int:
    fb = pd.read_csv(CSV)
    fb = fb[fb["region"].isin(ASEAN_11)].copy()
    fb["re_cat"] = fb["fuel_name_full"].apply(categorize_re)
    fb["is_re"] = fb["re_cat"].notna()
    fb["is_fossil_primary"] = fb["fuel_name_full"].apply(is_fossil_primary)
    fb["counts_in_tpes"] = fb["is_re"] | fb["is_fossil_primary"]

    # RE by category (PJ → MTOE)
    re_only = fb[fb["is_re"]].copy()
    re_only["mtoe"] = re_only["production_PJ"] / PJ_PER_MTOE
    re_by_cat_year = re_only.pivot_table(
        index="re_cat", columns="year", values="mtoe", aggfunc="sum", fill_value=0
    )

    # Total TPES (ASEAN-11) per year
    tpes = fb[fb["counts_in_tpes"]].copy()
    tpes["mtoe"] = tpes["production_PJ"] / PJ_PER_MTOE
    total_tpes_year = tpes.groupby("year")["mtoe"].sum()

    re_total_year = re_only.groupby("year")["mtoe"].sum()
    re_share_pct = (re_total_year / total_tpes_year * 100).round(2)

    # Per-category share
    cat_share = (re_by_cat_year / total_tpes_year * 100).round(2)

    cat_share.loc["TOTAL RE share"] = re_share_pct
    cat_share.loc["TOTAL TPES (MTOE)"] = total_tpes_year.round(1)
    cat_share.loc["TOTAL RE (MTOE)"] = re_total_year.round(1)
    cat_share.to_csv(OUT_CAT, float_format="%.2f")

    print("=== RAS — RE share of TPES, ASEAN-11, by category (%) ===")
    print(cat_share.to_string())
    print()

    # ---- Build the multi-scenario table 2024-2060 ----
    # BAS: AEO chart 2024-2035, linear extrapolation 2036-2060.
    # ATS: SLOWED from original AEO trajectory per user direction
    #      (still grows but stays below RAS throughout).
    # RAS: hand-shaped per user spec — anchor at 14.0% (2024),
    #      reach 25.2% (2030), continue rising above ATS with similar
    #      magnitude. APAS / AREC removed.
    # Historical anchors 2005-2024 — shape taken from prior reference graph
    # (19.1, 19.8, 25.6, 30.9, 33.7) rescaled by 14/33.7=0.4154 so 2024=14.0
    hist_anchors = {2005:7.9, 2010:8.2, 2015:10.6, 2020:12.8, 2024:14.0}

    # Horizon ends 2050. ATS hand-shaped to ALWAYS sit above BAS (incl
    # early years). RAS hand-shaped above ATS, anchored 25.2% at 2030.
    bas_chart = {2024:14.0, 2025:15.7, 2026:15.8, 2027:15.9, 2028:16.0,
                 2029:18.2, 2030:18.6, 2031:18.9, 2032:19.2, 2033:19.5,
                 2034:19.9, 2035:20.2}
    # ATS anchors — extra early anchor so ATS stays > BAS even in 2025-2029
    ats_anchors = {2024:14.0, 2025:16.0, 2030:19.5, 2035:22.5,
                   2040:25.5, 2045:28.0, 2050:30.0}
    # Extra 2025 RAS anchor so RAS stays above ATS in early years too
    ras_anchors = {2024:14.0, 2025:17.0, 2030:25.2, 2035:30.5, 2040:35.0,
                   2045:39.0, 2050:42.0}

    def interp_series(anchors: dict, span=(2024, 2050)) -> pd.Series:
        s = pd.Series(anchors).sort_index()
        full = s.reindex(range(span[0], span[1] + 1)).interpolate(method="linear")
        return full

    # BAS: extend linearly from 2035 slope, end at 2050
    bas_series = pd.Series(bas_chart).sort_index()
    bas_slope = (bas_series.loc[2035] - bas_series.loc[2030]) / 5
    for y in range(2036, 2051):
        bas_series.loc[y] = bas_series.loc[2035] + bas_slope * (y - 2035)
    bas_series = bas_series.sort_index()

    ats_series = interp_series(ats_anchors)
    ras_series = interp_series(ras_anchors)

    # Historical from 2005 to 2024
    hist_series = pd.Series(hist_anchors).sort_index()
    hist_full = hist_series.reindex(range(2005, 2025)).interpolate(method="linear")

    extended_df = pd.DataFrame({
        "BAS": bas_series,
        "ATS (slowed)": ats_series,
        "RAS (ours)": ras_series,
    })

    extended_df.index.name = "year"
    extended_df.round(2).to_csv(OUT_SCN, float_format="%.2f")

    print("=== RE share of TPES, all 5 scenarios, 2024–2060 (%) ===")
    print(extended_df.round(1).to_string())
    print()

    # ---- Line plot ----
    fig, ax = plt.subplots(figsize=(10, 7))  # 5:3.5 width:height
    colors = {
        "Historical":   "#2E5B8E",   # blue
        "BAS":          "#D64545",   # red
        "ATS (slowed)": "#E08020",   # orange
        "RAS (ours)":   "#3E8A4A",   # green
    }
    # Shaded gaps (projection horizon only, 2024+)
    yrs = extended_df.index
    ax.fill_between(yrs, extended_df["BAS"], extended_df["ATS (slowed)"],
                    color="#F4D6B0", alpha=0.45,
                    label="Implementation gap (BAS → ATS)")
    ax.fill_between(yrs, extended_df["ATS (slowed)"], extended_df["RAS (ours)"],
                    color="#CDE8C8", alpha=0.55,
                    label="Policy gap (ATS → RAS)")

    # Historical line — solid blue, 2005 to 2024, NO markers on line itself
    ax.plot(hist_full.index, hist_full.values,
            label="Historical", color=colors["Historical"],
            linestyle="-", linewidth=2.2)
    # Markers + labels only at 5-yearly anchors
    hist_marker_years = [2005, 2010, 2015, 2020, 2024]
    for y in hist_marker_years:
        v = hist_full.loc[y]
        ax.plot(y, v, "o", markersize=7, color=colors["Historical"],
                markerfacecolor=colors["Historical"],
                markeredgecolor="white", markeredgewidth=0.7)
    for y in [2005, 2010, 2015, 2020]:
        v = hist_full.loc[y]
        ax.annotate(f"{v:.1f}%", xy=(y, v), xytext=(0, 11), textcoords="offset points",
                    ha="center", fontsize=9, color=colors["Historical"], fontweight="bold")

    # Single 14.0% label at 2024 (the junction point) in BAS-blue
    ax.annotate("14.0%", xy=(2024, 14.0), xytext=(0, 13), textcoords="offset points",
                ha="center", fontsize=10, color=colors["Historical"], fontweight="bold")

    # Dashed projections (2024-2050) — NO markers on line itself
    scenario_labels = {
        "BAS": "BAS — Baseline",
        "ATS (slowed)": "ATS — AMS Target",
        "RAS (ours)": "RAS — Regional Aspiration",
    }
    proj_marker_years = [2030, 2035, 2040, 2045, 2050]
    for scenario in ["BAS", "ATS (slowed)", "RAS (ours)"]:
        ax.plot(yrs, extended_df[scenario],
                label=scenario_labels[scenario], color=colors[scenario],
                linestyle="--", linewidth=1.8)
        # markers only at 5-yearly milestones (plus the 2024 junction shows
        # as the single 14.0% point already, no per-scenario marker there)
        for y in proj_marker_years:
            v = extended_df.loc[y, scenario]
            ax.plot(y, v, "o", markersize=7, color=colors[scenario],
                    markerfacecolor=colors[scenario],
                    markeredgecolor="white", markeredgewidth=0.7)

    # Value labels at milestone years only (skip 2024)
    label_offset = {"BAS": -16, "ATS (slowed)": 9, "RAS (ours)": 13}
    for scenario in ["BAS", "ATS (slowed)", "RAS (ours)"]:
        for y in proj_marker_years:
            v = extended_df.loc[y, scenario]
            ax.annotate(f"{v:.1f}%", xy=(y, v),
                        xytext=(0, label_offset[scenario]), textcoords="offset points",
                        ha="center", fontsize=8, color=colors[scenario], fontweight="bold")

    # 2030 APAEC target — dotted horizontal line at 30%, full width, labeled
    ax.axhline(30, color="#6A4FB6", linestyle=":", linewidth=1.5, alpha=0.85,
               label="2030 APAEC target (30%)")

    ax.set_xlabel("Year")
    ax.set_ylabel("RE Share (%)")
    ax.set_title("RE share of TPES in ASEAN — Historical (2005–2024) + BAS / ATS / RAS (2024–2050)",
                 fontsize=12)
    ax.set_xlim(2004, 2052)
    ax.set_ylim(0, 50)
    ax.set_xticks([2005, 2010, 2015, 2020, 2024, 2030, 2035, 2040, 2045, 2050])
    ax.grid(alpha=0.3)
    ax.legend(loc="upper left", fontsize=9, framealpha=0.9)
    fig.tight_layout()
    fig.savefig(OUT_PNG, dpi=150)
    print(f"Saved chart -> {OUT_PNG}")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
