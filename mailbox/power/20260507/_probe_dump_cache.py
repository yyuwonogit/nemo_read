"""Diagnostic: dump every branch FullName the cache enumerates under
each ActiveRegion (Brunei/Indonesia/Malaysia). Lets us grep for real
branches we expected to see (e.g. `Wind Onshore_MYPE`) and confirm
whether COM's Branches collection is failing to enumerate them."""
from __future__ import annotations
from pathlib import Path
from nemo_read._leap_com import LeapTreeCache, dispatch_leap

HERE = Path(__file__).parent
EXPECT_AREA = "aeo9_v0.38_yy"
PROBE_REGIONS = ["Brunei", "Indonesia", "Malaysia"]


def main() -> int:
    leap = dispatch_leap()
    if leap.ActiveArea.Name != EXPECT_AREA:
        print(f"ERROR: ActiveArea is {leap.ActiveArea.Name!r}, "
              f"expected {EXPECT_AREA!r}")
        return 3

    for region in PROBE_REGIONS:
        leap.ActiveRegion = region
        cache = LeapTreeCache(leap=leap)
        names = sorted(cache.fullname_to_idx)
        out = HERE / f"_cache_dump_{region.lower().replace(' ', '_')}.txt"
        out.write_text("\n".join(names), encoding="utf-8")
        print(f"[{region:<10}] {len(names)} branches dumped -> {out.name} "
              f"(build_errors={cache._build_errors})")
        # Quick checks of interest
        my_count = sum(1 for n in names if "_MY" in n.split("\\")[-1])
        id_count = sum(1 for n in names if "_ID" in n.split("\\")[-1])
        cl_gas_cc = any(n.endswith("\\Gas Combined Cycle") for n in names)
        cl_wind_on = any(n.endswith("\\Wind Onshore") for n in names)
        cl_solar_pv = any(n.endswith("\\Solar PV") for n in names)
        print(f"  _MY* leaves: {my_count}, _ID* leaves: {id_count}")
        print(f"  country-level Gas Combined Cycle present: {cl_gas_cc}")
        print(f"  country-level Wind Onshore present: {cl_wind_on}")
        print(f"  country-level Solar PV present: {cl_solar_pv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
