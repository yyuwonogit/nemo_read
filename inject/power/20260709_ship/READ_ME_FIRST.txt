AEO-9 v0.71 — power inject complete + results (2026-07-09)
=========================================================

Hi team,

Your batch-1 payload is injected and the model solved (now v0.71). This package
has the results, exactly what we pushed into the model, and the open items on
both sides.

WHAT'S IN HERE
  READ_ME_FIRST.txt   - this note
  POWER_RESULTS_v0.71.csv
        Your sector's results, one row per technology / region / year / scenario.
        Generation in TWh, Capacity in GW (unit is stamped on every row).
        Scenarios: Baseline (BAS), AMS Target (ATS), Regional Aspiration (RAS).
  INTAKE_VALIDATION.md
        What we did with your batch-1: the gate checks it passed, the rows we
        cleaned or held, and the fixes we added before injecting.
  OPEN_ITEMS.md
        The to-do list on both sides - your actions and ours. Please read this.
  inject_files/
        The exact rows we pushed, so you can see everything that went in:
          01_joint_inject_delta_ALL_817rows.csv - the full injected payload
          02_our_dispatch_fullcapacity_delta.csv - our ATS/BAS FullCapacity flip
          03_our_negative_exo_fix.csv            - our ATS negative-Exo fix
          04_our_maxcap_wrapper_patch.csv        - our 4 MaxCap wrappers (see #2)

THREE THINGS TO FLAG
  1. Injected clean. 817 rows across CA/BAS/ATS/RAS, every row read back from
     the model and verified byte-exact.
  2. The 4 MaxCap fixes (Cambodia Wind, PH Small Hydro, Vietnam Wind, Malaysia
     Large Hydro_MYPE) now use Max(Exogenous Capacity[MW], N). PLEASE CARRY THESE
     FORWARD in every future payload - a full re-inject without them breaks the
     calc. Details + the exact expressions are in OPEN_ITEMS.md (#2).
  3. Held: your stranded-cost test row. It's on the Capital Cost variable but
     needs to be on Stranded Cost (unit U.S. Dollar). Re-send corrected and we
     inject it. See OPEN_ITEMS.md (#1).

Open items in full: OPEN_ITEMS.md. Shout if anything's unclear.
