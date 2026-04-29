"""
Defensible, published unit-conversion proposals for the LEAP injection workflow.

Used by :func:`nemo_read.leap_area.audit_canonical_units` (which appends
``proposed_factor`` / ``confidence_stars`` / ``source`` columns to the audit
table) and :func:`nemo_read.leap_area.apply_audit_conversions` (which
rewrites expression values in a canonical CSV using the proposed factors).

Confidence rubric (5★):

    ★★★★★ — exact SI / NIST / ISO definition (no judgment)
    ★★★★  — international standard, negligible variance
    ★★★   — published default with material variance (~±10%)
    ★★    — regional / proxy default, significant variance (~±25%)
    ★     — best-guess; CSV owner must verify

Every entry carries a citation. The CSV owner can override per-row at
``apply_audit_conversions(..., overrides=...)`` time without touching this
table — preserving traceability.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ConversionProposal:
    """A proposed unit conversion with provenance and confidence."""
    factor: float            # multiply source value by this to get target
    confidence_stars: int    # 1..5
    source: str              # citation / methodology
    caveat: str = ""         # optional warning / variance note


# Canonical unit normalisation (must match leap_area._normalise upstream).
def normalise_unit(s: str | None) -> str:
    if not s:
        return ""
    s = str(s).lower().strip()
    return (s.replace("u.s. dollar", "usd")
              .replace("united states dollar", "usd")
              .replace("2020 usd", "usd")
              .replace("billion barrel of oil equivalent", "gbbl")
              .replace("barrel", "bbl")
              .replace("metric tonne", "tonne")
              .replace("million btu", "mmbtu")
              .replace("petajoule", "pj")
              .replace("thousand gigajoules", "tgj")
              .replace("thousand gigajoule", "tgj")
              .replace("gigajoules", "gj")
              .replace("gigajoule", "gj")
              .replace("megawatt", "mw")
              .replace("100l", "hundredliter"))


# (normalised_from, normalised_to, fuel_or_None) → ConversionProposal
# Fuel is matched case-insensitively; None acts as a fallback.
_REGISTRY: dict[tuple[str, str, str | None], ConversionProposal] = {

    # --- pure SI ----------------------------------------------------------
    ("usd/gj real usd", "usd/mmbtu", None): ConversionProposal(
        factor=1.05506,
        confidence_stars=5,
        source="ISO 31-4: 1 BTU = 1055.06 J → 1 GJ = 0.94782 MMBtu, "
               "so 1 USD/GJ = 1.05506 USD/MMBtu.",
    ),
    ("usd/gj", "usd/mmbtu", None): ConversionProposal(
        factor=1.05506,
        confidence_stars=5,
        source="ISO 31-4: 1 BTU = 1055.06 J → 1 GJ = 0.94782 MMBtu, "
               "so 1 USD/GJ = 1.05506 USD/MMBtu.",
    ),
    ("usd/100l real usd", "usd/bbl", None): ConversionProposal(
        factor=1.5899,
        confidence_stars=5,
        source="NIST Handbook 44: 1 US barrel = 158.987 L → "
               "1 USD/100L = 1.5899 USD/bbl.",
    ),
    ("usd/hundredliter real usd", "usd/bbl", None): ConversionProposal(
        factor=1.5899,
        confidence_stars=5,
        source="NIST Handbook 44: 1 US bbl = 158.987 L.",
    ),
    ("pj/year", "tgj/year", None): ConversionProposal(
        factor=1000.0,
        confidence_stars=5,
        source="SI: 1 PJ = 1e6 GJ; LEAP 'Thousand Gigajoules' = 1e3 GJ "
               "→ 1 PJ = 1000 thousand-GJ.",
    ),
    ("pj/year", "gj", None): ConversionProposal(
        factor=1.0e6,
        confidence_stars=5,
        source="SI: 1 PJ = 1e6 GJ. (Maximum Production for Secondary "
               "fuels in LEAP is annual energy in GJ.)",
    ),
    ("pj", "gj", None): ConversionProposal(
        factor=1.0e6,
        confidence_stars=5,
        source="SI: 1 PJ = 1e6 GJ.",
    ),

    # --- coal: USD/GJ → USD/tonne via fuel-specific LHV ------------------
    # IPCC 2019 Refinement Vol.2 Ch.1 Table 1.2 lists default Net Calorific
    # Values (LHVs). LEAP's Newcastle/HBA-style benchmarks align with these.
    ("usd/gj real usd", "usd/tonne", "coal bituminous"): ConversionProposal(
        factor=25.8,
        confidence_stars=3,
        source="IPCC 2019 Refinement Vol.2 Ch.1 Table 1.2 — bituminous "
               "coal default NCV 25.8 GJ/tonne. Newcastle 6000 kcal grade ≈ "
               "25.12 GJ/tonne (IEA Coal Information).",
        caveat="Regional variance ±10% (Indonesian Tarahan slightly "
               "lower, Australian export grades higher). Pin per AMS if "
               "domestic LHV is known.",
    ),
    ("usd/gj real usd", "usd/tonne", "coal sub bituminous"): ConversionProposal(
        factor=18.9,
        confidence_stars=3,
        source="IPCC 2019 Refinement Vol.2 Ch.1 Table 1.2 — sub-bituminous "
               "coal default NCV 18.9 GJ/tonne. Indonesian HBA grade typical.",
        caveat="±10% across HBA reference quality bands.",
    ),
    ("usd/gj real usd", "usd/tonne", "coal lignite"): ConversionProposal(
        factor=11.9,
        confidence_stars=2,
        source="IPCC 2019 Refinement Vol.2 Ch.1 Table 1.2 — lignite "
               "default NCV 11.9 GJ/tonne.",
        caveat="High regional variance (7–15 GJ/tonne): Mae Moh ≈ 9.7, "
               "Sumatran ≈ 11.5, Vietnamese ≈ 13+. Strongly recommend "
               "per-AMS override.",
    ),
    # Generic GJ → tonne fallback (no fuel known) — flag low confidence
    ("usd/gj real usd", "usd/tonne", None): ConversionProposal(
        factor=20.0,
        confidence_stars=1,
        source="Generic mid-range default (20 GJ/tonne) — used only when "
               "fuel context is missing.",
        caveat="DO NOT rely on this — supply fuel context for a real "
               "factor.",
    ),

    # --- crude/oil: USD/bbl ↔ USD/tonne (rare path) ----------------------
    ("usd/bbl real usd", "usd/tonne", "crude oil"): ConversionProposal(
        factor=7.33,
        confidence_stars=2,
        source="API gravity ≈ 33° → 7.33 bbl/tonne (BP Statistical "
               "Review default for Brent-equivalent).",
        caveat="±15% across crude grades (heavier crude = fewer bbl/tonne).",
    ),

    # --- LEAP capital-cost convention: USD/GJ → USD/(GJ/yr of capacity) ---
    # LEAP "2020 USD/Gigajoules/Year" denotes overnight USD per unit of
    # annual capacity. The author-side "USD/GJ" is treated by LEAP as
    # numerically equivalent (overnight per annual GJ).
    ("usd/gj", "usd/gj/year", None): ConversionProposal(
        factor=1.0,
        confidence_stars=3,
        source="LEAP capital-cost convention: USD/(GJ/yr of capacity) "
               "stores the same numeric value as overnight USD per annual "
               "GJ produced.",
        caveat="If your USD/GJ is amortised (LCOE-style) rather than "
               "overnight, divide by capital-recovery factor before using.",
    ),

    # --- USD/GJ → USD/(TCE/yr): cross-energy + capacity convention ------
    # 1 tonne-coal-equivalent (TCE) = 29.3076 GJ (IEA standard); the /Year
    # part is the same LEAP capacity convention as above.
    ("usd/gj", "usd/tonne coal equiv/year", None): ConversionProposal(
        factor=29.3076,
        confidence_stars=4,
        source="IEA: 1 TCE = 29.3076 GJ (7000 kcal/kg equivalent). "
               "USD/GJ × 29.3076 = USD/TCE; LEAP /Year denotes annual "
               "capacity, treated as identity.",
        caveat="Same overnight-vs-amortised caveat as USD/GJ → USD/(GJ/yr).",
    ),

    # --- Commodity-tagged tonne → Metric Tonne (descriptive only) -------
    # "USD/t FFB" or "USD/t fresh root" are physically the same unit as
    # "USD/Metric Tonne" — the commodity tag is a label, not a conversion.
    ("usd/t fresh root", "usd/tonne", None): ConversionProposal(
        factor=1.0, confidence_stars=5,
        source="One tonne of cassava fresh root is one tonne — commodity "
               "tag is descriptive only.",
    ),
    ("usd/t nuts-in-shell", "usd/tonne", None): ConversionProposal(
        factor=1.0, confidence_stars=5,
        source="One tonne of coconut nuts-in-shell is one tonne — "
               "commodity tag is descriptive only.",
    ),
    ("usd/t ffb", "usd/tonne", None): ConversionProposal(
        factor=1.0, confidence_stars=5,
        source="One tonne of palm FFB is one tonne — commodity tag is "
               "descriptive only.",
    ),
    ("usd/t cane", "usd/tonne", None): ConversionProposal(
        factor=1.0, confidence_stars=5,
        source="One tonne of sugarcane is one tonne — commodity tag is "
               "descriptive only.",
    ),
    ("usd/t grain", "usd/tonne", None): ConversionProposal(
        factor=1.0, confidence_stars=5,
        source="One tonne of corn grain is one tonne — commodity tag is "
               "descriptive only.",
    ),
    ("usd/t molasses", "usd/tonne", None): ConversionProposal(
        factor=1.0, confidence_stars=5,
        source="One tonne of molasses is one tonne — commodity tag is "
               "descriptive only.",
    ),
    ("usd/t pome wet", "usd/tonne", None): ConversionProposal(
        factor=1.0, confidence_stars=5,
        source="One tonne of POME (wet) is one tonne — commodity tag is "
               "descriptive only.",
    ),
    ("usd/t rice straw dry", "usd/tonne", None): ConversionProposal(
        factor=1.0, confidence_stars=5,
        source="One tonne of rice straw (dry) is one tonne — commodity "
               "tag is descriptive only.",
    ),
    ("usd/t uco", "usd/tonne", None): ConversionProposal(
        factor=1.0, confidence_stars=5,
        source="One tonne of UCO is one tonne — commodity tag is "
               "descriptive only.",
    ),

    # --- USD/t commodity → USD/TCE: cross-energy via commodity LHV -------
    ("usd/t grain", "usd/tonnes of coal equivalent", None): ConversionProposal(
        factor=2.0074,
        confidence_stars=3,
        source="Corn (maize) grain LHV 14.6 GJ/t (IPCC 2019 Refinement "
               "Vol.2 Ch.1 Table 1.2 default for cereals); 29.3076/14.6 "
               "= 2.0074. Used for both Import Cost and Fuel Cost variables.",
        caveat="±10% with moisture content; field-dry corn ≈ 14.6, "
               "post-harvest at 15% MC ≈ 13.6 GJ/t.",
    ),

    # --- USD/t feedstock → USD/GJ: cross-energy via feedstock LHV --------
    # Tropical wet-biomass LHVs vary widely; these are mid-range defaults
    # for ASEAN feedstock pricing typical of the bioenergy CSV.
    ("usd/t ffb", "usd/gj", None): ConversionProposal(
        factor=1.0 / 6.0,
        confidence_stars=2,
        source="Palm Fresh Fruit Bunches (FFB) LHV ≈ 6 GJ/t wet basis "
               "(MPOB, IRENA palm-biomass series).",
        caveat="±20% with ripeness and moisture (refined palm oil = 37 "
               "GJ/t; do not confuse).",
    ),
    ("usd/t nuts-in-shell", "usd/gj", None): ConversionProposal(
        factor=1.0 / 13.5,
        confidence_stars=2,
        source="Coconut nuts-in-shell LHV ≈ 13.5 GJ/t (FAO Coconut "
               "Statistical Compendium; shell + copra weighted).",
        caveat="±20% across mature/young nuts and copra:shell ratio.",
    ),
    ("usd/t cane", "usd/gj", None): ConversionProposal(
        factor=1.0 / 7.5,
        confidence_stars=2,
        source="Sugarcane (raw, wet, including bagasse mass) LHV ≈ 7.5 "
               "GJ/t (FAO Sugar Statistical Yearbook; bagasse 18 GJ/t × "
               "30% mass + sugar 16 GJ/t × 12% mass + water).",
        caveat="±25% — refined sugar removed before energy use.",
    ),
    ("usd/t fresh root", "usd/gj", None): ConversionProposal(
        factor=1.0 / 3.5,
        confidence_stars=2,
        source="Cassava fresh root LHV ≈ 3.5 GJ/t wet basis (IRENA "
               "starch-crop biomass series; high moisture).",
        caveat="±25% with moisture; dry chips ≈ 14 GJ/t.",
    ),

    # --- Capacity: Million Tonnes/yr × LHV → annual energy capacity -----
    # Output-fuel LHV converts mass throughput to LEAP's energy-based
    # capacity unit. Fuel context required to disambiguate.
    ("million tonnes/yr", "million gj/year", "biodiesel"): ConversionProposal(
        factor=37.0,
        confidence_stars=4,
        source="Biodiesel (FAME) LHV 37 GJ/t (IPCC 2006 Vol.2 Ch.1 "
               "Table 1.2 default for biodiesels).",
        caveat="±5% across FAME / CME / POME-biodiesel grades.",
    ),
    ("million tonnes/yr", "million tonne coal equiv/year", "ethanol"): ConversionProposal(
        factor=26.8 / 29.3076,
        confidence_stars=4,
        source="Ethanol LHV 26.8 GJ/t (IPCC 2006 Vol.2 Ch.1 default for "
               "biogasoline / anhydrous denatured); 26.8/29.3076 = 0.9145.",
        caveat="±3% — anhydrous vs hydrous ethanol differs by ~5%.",
    ),
    # Fallbacks (no fuel context): warn loudly via low confidence stars.
    ("million tonnes/yr", "million gj/year", None): ConversionProposal(
        factor=37.0,
        confidence_stars=1,
        source="Defaults to biodiesel LHV (37 GJ/t). Supply fuel context "
               "in canonical row to get the right factor.",
        caveat="STRONG — wrong if process output is not biodiesel.",
    ),
    ("million tonnes/yr", "million tonne coal equiv/year", None): ConversionProposal(
        factor=26.8 / 29.3076,
        confidence_stars=1,
        source="Defaults to ethanol LHV (26.8 GJ/t / 29.3076 = 0.9145). "
               "Supply fuel context in canonical row to get the right "
               "factor.",
        caveat="STRONG — wrong if process output is not ethanol.",
    ),
}


def _resolve_keys(from_unit: str, to_unit: str, fuel: str | None) -> list[tuple[str, str, str | None]]:
    """Generate lookup keys in fuel-specific → fallback order."""
    fnorm = normalise_unit(from_unit)
    tnorm = normalise_unit(to_unit)
    fuel_norm = (fuel or "").strip().lower() or None
    keys = []
    if fuel_norm:
        keys.append((fnorm, tnorm, fuel_norm))
    keys.append((fnorm, tnorm, None))
    return keys


def propose_conversion(
    from_unit: str,
    to_unit: str,
    fuel: str | None = None,
) -> ConversionProposal | None:
    """Return a conversion proposal if one is registered, else None.

    Tries fuel-specific match first, then falls back to fuel-agnostic.
    """
    for key in _resolve_keys(from_unit, to_unit, fuel):
        prop = _REGISTRY.get(key)
        if prop is not None:
            return prop
    return None


def list_known_conversions() -> list[tuple[tuple[str, str, str | None], ConversionProposal]]:
    """Return all registered (key, proposal) pairs — useful for docs/listing."""
    return list(_REGISTRY.items())


def fuel_specific_alternatives(from_unit: str, to_unit: str) -> list[str]:
    """Return the list of fuels for which a fuel-specific proposal exists
    on this unit pair.

    Used by :func:`nemo_read.leap_area.audit_canonical_units` to flag rows
    that hit a low-confidence fuel-agnostic fallback when a higher-
    confidence fuel-keyed alternative is available — i.e. the CSV owner
    could supply ``output_fuel=...`` to lift the proposal's stars.
    """
    fnorm = normalise_unit(from_unit)
    tnorm = normalise_unit(to_unit)
    return sorted({
        fuel for (f, t, fuel), _ in _REGISTRY.items()
        if f == fnorm and t == tnorm and fuel is not None
    })
