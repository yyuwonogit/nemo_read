# Handover — aeo9_v0.42 RAS infeasibility resolved

## Changes applied (cumulative, chronological)

1. Bioenergy MinUtil=0 + cost + structure inputs across all 11 AMS incl Timor Leste (FAME, CME, POME, HVO, Sugarcane, Cassava, Molasses, Corn Ethanol, SAF).
2. Placeholder import costs for Methanol, Coke Oven Gas, MSW.
3. Malaysia Sugarcane + Vietnam Coconut Oil Maximum Imports raised 10×, still physically plausible.
4. Fossil cost input — 229 rows for all AMS in Resources and Refinery branches.
5. VRE MU swept to 0 (Solar PV/Rooftop/Floating/CSP, Wind On/Off, Tidal, Wave, Small Hydro + subregional); Solar CSP + Wind Onshore needed a manual pass.
6. Incumbent dispatch techs (Biomass Other, Large Hydro, Geothermal) shifted from bare `MU = Maximum Availability` to soft phase-out `Min(Interp(historical CF → 0 over phase-out horizon), Max Availability)`.
7. Biomass + Wood `Maximum Production = 10000` on 8 AMS — replaces `Unlimited` string which silently broke LEAP→NEMO export.
8. Biomass + Wood `Maximum Imports` extended across all 11 AMS (base template wasn't inheriting).
9. Unhid all branches in `Transformation\Centralized Electricity Generation\Processes\` in Base Template region.
10. In CA and Base Template, set `Variable OM Cost` and `Fixed OM Cost` for all Unmet Load processes in Centralized Electricity Generation module to 500.
11. Unhid Unmet Load processes in Centralized Electricity Generation module — node-specific processes in Indonesia and Malaysia; non-node-specific in other regions.
12. Corrected parameters in CA, Set up and Base Template for `Transformation\Centralized Electricity Generation\Processes\Unmet Load_MYSR`.
13. Corrected parameters in Set up and Malaysia for `Transformation\Centralized Electricity Generation\Processes\Unmet Load_MYSR`.
14. Added optimized trade plug-in to model.
15. Removed `add_trade_routes` function from the model's NEMO before-scenario script.
16. Added trade routes in `Key\Optimized Trade` for all regions and the following fuels: Ethanol, Biodiesel, Coconut Oil, Palm Oil, Palm Oil Mill Effluent, Cassava, Molasses, Sugarcane, Corn. Enabled trade routes in RAS.

## Status

RAS now solving cleanly. Items 9–16 were the load-bearing fixes that resolved the 24k residual infeasibility:
- Unmet Load slack capacity wasn't visible/usable (hidden branches + missing cost) — model had no expensive backstop, so any unmet demand → INFEASIBLE rather than high-cost.
- Inter-region biofuel feedstock trade wasn't enabled — regions with zero local feedstock cap (Indonesia Sugarcane=0, Vietnam/Laos/Timor Leste Palm Oil=0) couldn't import from AMS with surplus, blocking MinShareProduction blend mandates from being satisfiable.

The earlier hypotheses (1e12 ResCap on Blending, RMTag on non-power techs, biogenic CO2 EAR magnitudes) remain real data quality issues worth cleaning up at some point, but were not the actual structural cause.
