# Bioenergy 2G branches to create manually in LEAP — 2026-07-23

`MISSING_2G_BRANCHES_for_manual_creation_20260723.csv` (61 rows) holds every
authored value for three branches that **do not exist in the `aeo9_v0.80`
structure**. Create the branches in LEAP, then paste these expressions.

Source: `inject/bioenergy/bioenergy_leap_input.csv` (the hand-authored input).
These rows are currently **dropped by `build_canonical.py`** — they are not in
`canonical_leap_inputs.csv` and have never been injected, so nothing in the
model depends on them yet.

## What v0.80 has today

| module | processes present |
|---|---|
| `Transformation\Bioethanol Production\Processes\` | Cassava, Corn Ethanol, Molasses, Sugarcane — **all 1G** |
| `Transformation\Biodiesel Production\Processes\` | CME Biodiesel, FAME Biodiesel, POME Biodiesel — **all 1G / oleochemical** |
| `Resources\Primary\` (residues) | Bagasse, Municipal Solid Waste only |

No cellulosic/2G conversion route, and no straw or waste-oil feedstock.

## The three branches to create

### 1. `Resources\Primary\Rice Straw` — 20 rows
| variable | rows | unit | confidence |
|---|---|---|---|
| `Maximum Production` | 10 (one per AMS) | Tonne | Medium |
| `Production Cost` | 10 | USD/t rice straw dry | Medium |

Production Cost is a common trajectory across all 10 AMS
(`Interp(2025, 45.0000, 2030, 46.3663, …)`); Maximum Production is per-country
(Brunei ~1,515 t → Cambodia ~1.67e7 t in 2025).

### 2. `Resources\Primary\Used Cooking Oil` — 20 rows
| variable | rows | unit | confidence |
|---|---|---|---|
| `Maximum Production` | 10 | Tonne | Medium |
| `Production Cost` | 10 | USD/t UCO | Medium |

Production Cost common across AMS (`Interp(2025, 300.0000, 2030, 309.1086, …)`).

### 3. `Transformation\Bioethanol Production\Processes\Cellulosic Rice Straw` — 21 rows
| variable | rows | unit | confidence |
|---|---|---|---|
| `Capital Cost` | 1 (applies to all 10 AMS) | USD/GJ | Medium |
| `Maximum Capacity` | 10 | Million Tonnes/yr | **Low** |
| `Variable OM Cost` | 10 | USD/GJ | Medium |

Output fuel is **Ethanol** (`fuel` column). `Maximum Capacity` is authored as
**all zeros across 2025–2060 for every AMS** — the capacity pathway is a
placeholder, so creating the branch will not by itself change any result.

## Before injecting these

1. **Create the branches**, then confirm the variable panel matches the table
   above — units especially (`USD/t rice straw dry`, `USD/t UCO` are
   non-standard and may need adding as LEAP units).
2. **Pair every supply cap with a cost row** — the 2026-05-19 POME lesson
   (`project_bioenergy_resolved_pome_import_cost`): a `Maximum Production`
   without a companion `Production Cost` makes the LP route through the
   unauthored ≈0-cost region. Both branches here already carry the pair; keep
   it that way.
3. **Wire the conversion chain.** `Cellulosic Rice Straw` needs its Feedstock
   Fuels input pointing at `Rice Straw`, and Ethanol as output — the CSV
   carries no `Process Efficiency` / IAR-OAR rows, so those must be authored
   separately or the process cannot convert anything.
4. **`Used Cooking Oil` has no consuming process** in this payload. It is a
   feedstock with no route to a fuel until an HVO/UCO-biodiesel process is
   created under `Biodiesel Production`. Flag back to the bioenergy team.
5. Re-run `build_canonical.py` afterwards — the adapter currently filters these
   rows out; confirm they survive into `canonical_leap_inputs.csv` before an
   inject is attempted.
6. §A.18: decide Timor Leste inclusion. These 10-AMS rows exclude TL.
