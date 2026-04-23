# nemo_read

Read, decode, and analyse LEAP-generated NEMO scenario SQLite databases. Targets NEMO data-dictionary v11 (LEAP 2024+, NemoMod 2.0+); reads older v9 / v10 databases with graceful degradation. Hoisted in tyuwono PyPI template structure.

## Install

```bash
pip install nemo_read
```

With optional extras:

```bash
pip install "nemo_read[parquet]"   # adds pyarrow for dump_to_parquet
pip install "nemo_read[dev]"       # adds pytest for the test suite
```

From source:

```bash
git clone https://github.com/<user>/nemo_read.git
cd nemo_read
pip install -e .[dev,parquet]
```

## Quick tour

```python
from nemo_read import NemoDB, print_overview, check_scenario, get_parameter, get_result

db = NemoDB("scenario.sqlite")
print_overview(db)                                  # inventory + validation + infeasibility

# Before calculating:
report = check_scenario(db)
if not report.ok():
    for issue in report.errors():
        print(issue.severity, issue.category, issue.message)

cc  = get_parameter(db, "CapitalCost")              # defaults applied
cap = get_result(db, "vtotalcapacityannual")        # latest solvedtm
```

## Repository layout

```
nemo_read/
├── pyproject.toml
├── README.md
├── CHANGELOG.md
├── LICENSE
├── nemo_read/                       # library source
│   ├── __init__.py                  # public API surface
│   ├── db.py                        # NemoDB connection class
│   ├── schema.py                    # frozen NEMO v11 schema
│   ├── dimensions.py                # typed dim readers
│   ├── parameters.py                # default-overlay reader
│   ├── variables.py                 # result reader with solvedtm filter
│   ├── timeslice.py                 # year_split, tsgroup_hours
│   ├── export.py                    # xarray + CSV + Parquet
│   ├── custom.py                    # __NEMOcc tables + slack detection
│   ├── leap_conventions.py          # units, LEAP IDs, D/P/S classification
│   ├── validate.py                  # structural validation
│   ├── infeasibility.py             # find_infeasibilities + check_scenario
│   ├── inspect.py                   # inspect_scenario + print_overview
│   └── scaffold.py                  # project-package generator
├── tests/                           # five pytest suites
└── docs/                            # topic references
    ├── schema.md                    # NEMO v11 column reference
    ├── cookbook.md                  # analysis recipes
    ├── leap_integration.md          # LEAP COM API + _def view semantics
    ├── scaffolding.md               # project-package scaffolder
    ├── conventions_and_validation.md# units, IDs, validation, infeasibility
    └── leap_area_wishlist.md        # OPEN WORK: LEAP-area decoding backlog
```

## Scaffold a project package

`nemo_read` ships with a scaffolder that generates a project-specific Python package wrapping the reader. The generated package has a scenario registry, high-level loaders, a Parquet cache, and a CLI.

```bash
nemo_read-scaffold mypkg ./mypkg \
    --author "Your Name" \
    --scenario BAS=data/BAS.sqlite \
    --scenario ATS=data/ATS.sqlite \
    --reference-db data/BAS.sqlite
```

See [docs/scaffolding.md](docs/scaffolding.md) for details.

## Status

| Area | Status |
|---|---|
| NEMO v11 schema coverage | Complete |
| Parameter reading with defaults | Complete |
| Time-slicing math | Complete |
| LEAP ID extraction (fuels) | Complete |
| Technology kind classification (D/P/S) | Complete |
| Custom constraint (`__NEMOcc`) discovery and reading | Complete |
| Slack technology detection | Complete |
| Unit labelling (PJ / GW / t / M$) | Complete |
| Structural validation | Complete |
| Static infeasibility analysis | Complete |
| Result-variable reading with solvedtm filter | Complete |
| xarray / CSV / Parquet export | Complete |
| Project-package scaffolder | Complete |
| **LEAP branch hierarchy decoding** | **Pending — see [docs/leap_area_wishlist.md](docs/leap_area_wishlist.md)** |
| **`__NEMOcc.bid` → technology name resolution** | **Pending** |
| **`nemo.cfg` / `customconstraints.txt` parsing** | **Pending** |

The pending items require exports from the LEAP Areas folder; the SQLite file does not carry the branch hierarchy or runtime configuration.

## Running the tests

```bash
python -m pytest
```

Five suites cover ~300 assertions against synthetic databases plus a regression fixture derived from a real 11-region SE Asia scenario.

## License

Apache-2.0 — see [LICENSE](LICENSE).

## References

- NEMO documentation: https://sei-international.github.io/NemoMod.jl/stable/
- LEAP: https://leap.sei.org/
