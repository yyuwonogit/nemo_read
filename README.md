# nemo_read

Read, decode, and analyse LEAP-generated NEMO scenario SQLite databases. Targets NEMO data-dictionary v11 (LEAP 2024+, NemoMod 2.0+); reads older v9 / v10 databases with graceful degradation.

> **Project conventions.** The build method and repository layout follow the **tyuwono PyPI template** that is reused across similar scientific-data reader packages — flat src layout with `pyproject.toml` at the root, `tests/` and `docs/` as siblings, Apache-2.0 licensing, and tag-driven PyPI releases via GitHub Actions trusted publishing.

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

## Infeasibility resolution — the 11-stage methodology

When the solver chokes on `Infeasible column 'xN'` or any other dead end,
this package owns the full path from "what broke?" to "real fix landed".
Every stage has a tool and an exit criterion. See
[docs/infeasibility_methodology.md](docs/infeasibility_methodology.md)
for the worked diagram.

```
1  PRE-FLIGHT          validate_scenario, find_infeasibilities, check_scenario
2  SOLVER RUN          (LEAP/NEMO/CPLEX)
3  POST-MORTEM TRIAGE  decode_lp_column        ← "x435004 = vaccumulatednewcapacity[R19,P16166,2025]"
4  PATTERN FORENSICS   classify_parameter      ← bug vs intent classification per (r,t) cluster
5  PLACEHOLDER         propose_placeholders    ← ranked diagnostic patches, lex-sorted
6  DIAGNOSTIC TEST     inject_to_leap.py --placeholder-mode  →  re-run Stage 2
7  PROBE BRIEF         emit_probe_brief        ← minimum LEAP COM read list (only if Stage 6 stuck)
8  LEAP COM PROBING    nemo_read._leap_com
9  REAL-FIX DESIGN     (manual, informed by 4+6+8)
10 PATCH INJECTION     inject_to_leap.py
11 VERIFICATION        loop back to Stage 1
```

The principle: exhaust the SQLite + solver report first; reduce the
residual question to the smallest possible LEAP probe; propose a
testable placeholder before any real fix is committed. Three mechanically
distinct outcomes per placeholder run (solves / same column / new column)
turn debugging into hypothesis testing — no rabbit-chase.

```python
from nemo_read import (
    NemoDB, decode_lp_column, forensics_for_pinned_variable,
    propose_placeholders, emit_probe_brief,
)

db = NemoDB("scenario.sqlite")
ident = decode_lp_column(db, 435004)                 # Stage 3
reports = forensics_for_pinned_variable(db, ident)   # Stage 4
mu = next(r for r in reports if r.parameter == "MinimumUtilization")
for p in propose_placeholders(mu, max_per_report=5): # Stage 5
    print(p, "→", p.real_fix_prompt)
brief = emit_probe_brief(*reports)                   # Stage 7 (if needed)
print(brief.to_text())
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
