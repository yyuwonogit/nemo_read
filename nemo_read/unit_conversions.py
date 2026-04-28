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
