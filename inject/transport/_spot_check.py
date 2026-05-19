"""Pull 3 spot-check rows from the canonical for UI verification."""
import csv

rows = list(csv.DictReader(
    open("inject/transport/canonical_leap_inputs.csv", encoding="utf-8")))

picks = [
    ("Brunei",
     r"Key\TransportDataStock\Vehicle_Sales\Bus",
     "Activity Level",
     "Current Accounts"),
    ("Indonesia",
     r"Key\TransportDataStock\Vehicles_Sales_Share\PassengerCar\Electricity",
     "Activity Level",
     "Regional Aspiration Scenario"),
    ("Vietnam",
     r"Demand\Transport\Road\Truck\Blended Diesel\Blended Diesel",
     "Mileage",
     "Current Accounts"),
]

for ams, branch, var, scen in picks:
    found = [r for r in rows if r["ams"] == ams and r["branch"] == branch
             and r["variable"] == var and r["scenario"] == scen]
    print("---")
    if not found:
        print(f"  MISSING in canonical: {ams} | {branch} | {var} | {scen}")
        continue
    r = found[0]
    print(f"  AMS:      {r['ams']}")
    print(f"  Scenario: {r['scenario']}")
    print(f"  Branch:   {r['branch']}")
    print(f"  Variable: {r['variable']}")
    expr = r["expression"]
    print(f"  Expected expression:")
    print(f"    {expr if len(expr) <= 200 else expr[:197] + '...'}")
