AEO-9 v0.71 — Residential sector results + connected drivers (2026-07-09)
========================================================================

Hi team,

This is your residential package for the v0.71 run. Per our handover rule, it
includes not only your own sector but everything your branches are CONNECTED to
by formula and by activity level — the demographic and macro drivers (number of
households, population, GDP, etc.) that your demand is built on — so you have the
full picture in one place.

WHAT'S IN HERE
  READ_ME_FIRST.txt   - this note

  RESIDENTIAL_RESULTS_v0.71.csv
        Your sector's v0.71 final-energy-demand results. One row per
        fuel / region / year / scenario, leaf level. Electricity carriers in
        GWh, all other fuels in PJ (unit stamped on every row). A `layer`
        column separates Historical (actuals) from Projection (model outlook);
        sum leaves or filter by layer - see the column notes.

  connected_drivers/           <- the activity-level & formula drivers you asked for
        HEADLINE_activity_drivers.csv
            The demographic + macroeconomic drivers your demand keys off:
            Households, Population, Urban population, Household Size, Average
            Income, Real GDP (PPP / per-capita / per-capita growth), sector GDP
            fractions, elasticities. Values per region / year / scenario.
        connected_keys_drivers_values.csv
            The FULL set of Key branches your residential expressions connect to
            (the headline drivers above PLUS your appliance size/efficiency
            shares, useful-EI, end-use a/b coefficients, lighting data, Net-Zero
            measures, and fuel calibration). Every driver, with its expression.
        connected_keys_tree.txt / connected_keys_units.csv
            The tree layout and units for those connected keys.

  input/                       <- your authored INPUT + how to author it
        residential_canonical_input.csv    - the canonical input rows we inject
                                             to LEAP for your sector (your data)
        residential_current_expressions.csv - the same branches as they currently
                                             sit in the model (4 scenarios)
        CSV_AUTHORING_GUIDE.md             - how to format rows you send back
        AC_ANATOMY.md / FRIDGE_ANATOMY.md / FRIDGE_AUTHOR_GUIDELINE.md
                                           - the AC & fridge device-stock models
        timor_leste_supplement.csv        - Timor Leste rows (kept separate)

  leap_structure/              <- the LEAP structure (canon) for your sector
        residential_tree.txt              - your full branch tree
        residential_variables_units.csv   - every variable + its unit per branch
        README_RESIDENTIAL_CANON_STRUCTURE.md - the canon structure write-up
        ANOMALY_AUDIT_RESIDENTIAL_20260704.md - flagged data-quality items

  full_results/                <- the COMPLETE model result set (all teams' view)
        aeo9_v0.71_demand_ALL_sectors_by_fuel.csv - final energy demand for EVERY
            sector (Industry, Transport, Residential, Commercial, Agriculture,
            Non-Energy), by fuel, so you can see residential in system context.
        aeo9_v0.71_supply_power_tidy.csv - power-sector generation (TWh) + capacity (GW).
        README_full_results.md - schema + units for both.

ONE THING TO WATCH — duplicate AC / fridge representations
  Your tree carries TWO parallel models for air-conditioning and refrigeration:
  "Air Conditioning" + "Air Conditioning_" (trailing underscore), and
  "Refrigeration" + "Refrigeration_". Both hold real load, so any total that
  sums across both DOUBLE-COUNTS. In our own reporting we keep one of each
  ("Air Conditioning" + "Refrigeration_") and drop the other pair. Please
  confirm which representation is authoritative so we can retire the duplicate.

NOTES
  - Structure/driver inputs are unchanged since v0.67 (this cycle's edits were
    power-side), so the connected drivers here are current.
  - Values are the model's outputs/inputs, not observed statistics.

Shout if you want a different slice or any driver broken out further.
