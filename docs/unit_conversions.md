# Unit conversions reference

`nemo_read.unit_conversions` carries the package's defensible default factors
for converting source-unit values (USD/GJ, USD/100L, PJ/year, etc.) into the
unit each LEAP variable actually displays in the Analysis pane (USD/Metric
Tonne, USD/Barrel, Thousand Gigajoules/Year, etc.).

The fixed workflow (`mailbox/run_workflow.py`) calls these proposals
automatically. `apply_audit_conversions(canonical_df, audit_df, overrides=...)`
applies the proposed factor unless the caller pins a per-row override.

## Confidence rubric

| Stars | Meaning | Examples in this registry |
|:---:|---|---|
| ★★★★★ | Exact SI / NIST / ISO definition | `1 PJ = 1e6 GJ`, `1 BTU = 1055.06 J`, `1 bbl = 158.987 L` |
| ★★★★ | International standard, negligible variance | `1 toe = 41.868 GJ` (IEA) |
| ★★★ | Published default with material variance (~±10%) | IPCC LHV for bituminous coal (25.8 GJ/t) |
| ★★ | Regional/proxy default, significant variance (~±25%) | IPCC lignite LHV (11.9 GJ/t — varies 7–15) |
| ★ | Best-guess; user must verify | Generic GJ→tonne fallback when fuel context absent |

## Registered defaults

### SI / standard (★★★★★)

| From | To | Factor | Source |
|---|---|---:|---|
| `USD/GJ` | `USD/MMBtu` | × 1.05506 | ISO 31-4: 1 BTU = 1055.06 J |
| `USD/100L` | `USD/Barrel` | × 1.5899 | NIST Handbook 44: 1 US bbl = 158.987 L |
| `PJ/year` | `Thousand Gigajoules/Year` | × 1000 | SI |
| `PJ/year` | `Gigajoule` | × 1e6 | SI |
| `PJ` | `GJ` | × 1e6 | SI |

### Coal LHV — fuel-specific (★★★ / ★★)

| Fuel | LHV (GJ/tonne) | Stars | Source |
|---|---:|:---:|---|
| Coal Bituminous | 25.8 | ★★★ | IPCC 2019 Refinement Vol.2 Tbl 1.2; Newcastle 6000 kcal grade ≈ 25.12 |
| Coal Sub-bituminous | 18.9 | ★★★ | IPCC 2019 Refinement Vol.2 Tbl 1.2; Indonesian HBA grade typical |
| Coal Lignite | 11.9 | ★★ | IPCC 2019 Refinement Vol.2 Tbl 1.2; high regional variance (Mae Moh ≈ 9.7, Sumatran ≈ 11.5, Vietnamese ≈ 13+) |

### Crude oil API conversion (★★)

| From | To | Factor (bbl/tonne) | Source |
|---|---|---:|---|
| `USD/bbl` | `USD/Metric Tonne` | × 7.33 | API gravity ≈ 33° (Brent-equivalent); BP Statistical Review default |

## Per-row overrides

When the registry default doesn't fit your data, supply an override at apply time:

```python
overrides = {
    # AMS-specific
    ("Resources\\Primary\\Coal Lignite", "Production Cost", "Indonesia"): {
        "factor": 11.5,
        "source": "PT Bukit Asam Sumatran lignite contracts (avg LHV)",
        "confidence_stars": 4,
    },
    # Branch+variable wide (any AMS)
    ("Resources\\Primary\\Coal Bituminous", "Production Cost"): {
        "factor": 25.12,
        "source": "Newcastle 6000 kcal benchmark per IEA Coal Information",
        "confidence_stars": 4,
    },
}
out = apply_audit_conversions(canonical_df, audit_df, overrides=overrides)
```

The `unit_audit` column in the output records the factor + source actually used so the conversion is traceable.

## Adding a new conversion to the registry

Edit `nemo_read/unit_conversions.py` `_REGISTRY` dict. Always include:

- Canonical source units (use `normalise_unit()` for the key — lowercase, USD-collapsed, etc.)
- Factor (multiply source by this)
- Confidence stars (use the rubric above)
- Source citation
- Caveat for known variance

Run `tests/test_unit_conversions.py` after editing.

## What's not in the registry

- **Currency-year conversions** (2020 USD ↔ 2024 USD): out of scope. Inflate/deflate at data prep time using your own deflator (BLS CPI, IMF WEO PPP).
- **Power → energy** (kW · year vs PJ): handled implicitly by LEAP — supply data in the unit LEAP shows.
- **LEAP `[unit]` formula expressions** (e.g. `Import Cost[2020 USD/bbl] * 0.97`): LEAP converts these internally at evaluation; the audit marks them `formula_reference` and `apply_audit_conversions` leaves them alone.
