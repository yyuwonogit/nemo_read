# Scaffolding a repo-ready package

`nemo_read-scaffold` generates a Python package that wraps the reader with a project-specific registry, loaders, cache, CLI, and tests. The result is a self-contained directory the user can drop into a repo, run `pip install -e .`, and start using.

## Contents

- [When to use the scaffolder](#when-to-use-the-scaffolder)
- [Invocation](#invocation)
- [Generated layout](#generated-layout)
- [The scenario registry](#the-scenario-registry)
- [Loaders and cache](#loaders-and-cache)
- [The CLI](#the-cli)
- [Dimension Literal types](#dimension-literal-types)
- [Regenerating after scenario changes](#regenerating-after-scenario-changes)
- [Customising the generated package](#customising-the-generated-package)
- [CI integration](#ci-integration)

## When to use the scaffolder

Use `nemo_read` directly for one-off scripts and notebooks. Use the scaffolder when:

- Multiple analysts in a team need to access the same scenarios with the same friendly names.
- Scenario paths should be versioned in git alongside analysis code.
- The codebase will grow a CLI for routine reporting (`mypkg export BAS --out exports/`).
- IDE autocomplete for region/technology/fuel codes matters.
- Expensive reads should be cached to Parquet between runs.

For throwaway analysis, skip it; direct `NemoDB("path.sqlite")` is fine.

## Invocation

After `pip install nemo_read` (or `pip install -e .` from the library source directory), the `nemo_read-scaffold` command is available:

```bash
nemo_read-scaffold PACKAGE_NAME DEST_DIR [options]
```

Positional arguments:

| Argument | Description |
|---|---|
| `PACKAGE_NAME` | Distribution name. Hyphens allowed; the Python module name is the name with hyphens converted to underscores (e.g. `my-pkg` → `my_pkg`). |
| `DEST_DIR` | Target directory. Created if missing; refuses to overwrite a non-empty existing directory unless `--overwrite` is passed. |

Options:

| Flag | Purpose |
|---|---|
| `--author NAME` | Author for `pyproject.toml` and README. |
| `--description TEXT` | One-line description for `pyproject.toml` and README. |
| `--scenario NAME=PATH` | Register a scenario. Repeat for each one. |
| `--reference-db PATH` | Path to one scenario DB; introspected to emit `dimensions.py` with `Literal` aliases. |
| `--overwrite` | Clobber existing files. |

Equivalent Python API:

```python
from nemo_read.scaffold import scaffold_package
scaffold_package(
    name="mypkg",
    dest="./mypkg",
    author="Ahrin",
    description="LEAP-NEMO data access for the SE Asia energy modelling repo.",
    scenarios={"BAS": "../data/BAS.sqlite", "ATS": "../data/ATS.sqlite"},
    reference_db="../data/BAS.sqlite",
    overwrite=False,
)
```

## Generated layout

```
mypkg/
├── pyproject.toml           src-layout, setuptools backend
├── README.md                how to install and use the package
├── .gitignore               Python + SQLite WAL/journal + .cache
├── src/mypkg/
│   ├── __init__.py          re-exports public API
│   ├── nemo_read/            vendored reader (no external dependency on nemo_read)
│   ├── registry.py          Registry class
│   ├── loaders.py           load_scenario, compare_scenarios
│   ├── cache.py             ParquetCache
│   ├── cli.py               argparse CLI
│   ├── dimensions.py        generated Literal types (only with --reference-db)
│   └── scenarios.toml       user-editable scenario registry
├── tests/
│   ├── __init__.py
│   └── test_smoke.py        imports + registry roundtrip
└── notebooks/
    └── explore.py           starter exploratory script
```

The `nemo_read` reader is vendored rather than depended on via PyPI. Research repos tend to prefer this for two reasons: it keeps the dependency graph minimal, and it lets the team pin a known-good reader version without worrying about upstream churn. The trade-off is that bug fixes in upstream `nemo_read` don't flow automatically; re-running the scaffolder with `--overwrite` pulls in the current version.

## The scenario registry

`scenarios.toml` is the source of truth for scenario paths. The format is intentionally minimal:

```toml
# Paths are resolved relative to this file by default.
paths_relative_to_config = true

[scenarios]
BAS = "../data/BAS.sqlite"
ATS = "../data/ATS.sqlite"
NZ  = "../data/NetZero.sqlite"
```

Setting `paths_relative_to_config = false` resolves against the current working directory instead, which is useful when different collaborators check out the repo to different locations and keep data outside the repo root.

At runtime:

```python
from mypkg import Registry

reg = Registry.from_default()          # uses the packaged scenarios.toml
reg.names()                            # ['ATS', 'BAS', 'NZ']
reg.path("BAS")                        # absolute Path to BAS.sqlite
"BAS" in reg                           # True
```

To use a different config (for example, a local override in dev):

```python
reg = Registry.from_toml("configs/dev-scenarios.toml")
```

The loaders accept an explicit `registry=` argument so scripts can swap registries without patching globals.

## Loaders and cache

Two high-level functions handle the common cases:

```python
from mypkg import load_scenario, compare_scenarios

db = load_scenario("BAS")                        # NemoDB instance
stacked = compare_scenarios(                     # long-form DataFrame
    ["BAS", "ATS", "NZ"],
    variable="vtotalcapacityannual",
)
stacked.head()
#      r     t     y      val  solvedtm             scenario
# 0  IDN  COAL  2024   1234.5  2026-03-01 ...       BAS
# 1  IDN  COAL  2024    890.2  2026-03-01 ...       ATS
# ...
```

The Parquet cache is a thin wrapper for expensive derived tables:

```python
from mypkg import ParquetCache

cache = ParquetCache(".cache/nemo")

def expensive_pivot():
    db = load_scenario("BAS")
    raw = db.query("SELECT ... big join here ...")
    return raw.groupby(...).agg(...).reset_index()

df = cache.get_or_compute("BAS-capacity-pivot-v1", expensive_pivot)
```

The cache key is just text; SHA-1 is used internally to derive the filename. Include anything that affects the result (scenario name, variable, filter values, computation version tag) in the key. Bump the version suffix when the computation changes.

Clearing:

```python
cache.clear()                          # delete all cached files
```

## The CLI

Installing the scaffolded package registers a console script named after the package. For a package named `mypkg` the command is `mypkg`:

```bash
mypkg list                                  # list registered scenarios
mypkg info BAS                              # print overview
mypkg dims BAS                              # show dimension sizes
mypkg export BAS --out exports/             # dump to CSV
mypkg export BAS --out exports/ --include parameters --with-defaults
```

Extending the CLI is straightforward: edit `src/mypkg/cli.py`, add a subparser, and call into the loaders.

## Dimension Literal types

When `--reference-db` is given, the scaffolder opens the scenario database read-only and emits `dimensions.py` with `Literal` aliases for each populated dimension:

```python
# src/mypkg/dimensions.py (generated)
from typing import Literal

Region = Literal["IDN", "MYS"]
Technology = Literal["PWRCOAL", "PWRSOL", ...]
Fuel = Literal["ELC", "COA", ...]
# ...
```

Analysts writing functions can annotate parameters with these aliases:

```python
from mypkg.dimensions import Region, Technology

def capacity_for(r: Region, t: Technology, year: int) -> float:
    ...
```

Editors with type-awareness (VS Code with Pylance, PyCharm) autocomplete the literal values. Mypy flags typos at static-check time. This matters most on teams where new analysts need to discover what codes exist without spelunking the database.

## Regenerating after scenario changes

When the reference scenario gains new regions, technologies, or fuels, regenerate with `--overwrite`:

```bash
nemo_read-scaffold mypkg ./mypkg \
    --scenario BAS=data/BAS.sqlite \
    --scenario ATS=data/ATS.sqlite \
    --reference-db data/BAS.sqlite \
    --overwrite
```

This rewrites every generated file, including `dimensions.py` and the vendored `nemo_read` copy. Hand-edited files in `src/mypkg/` will be lost. Two mitigations:

1. Keep project-specific code in new modules (e.g. `src/mypkg/analysis.py`), not in the generated ones.
2. Commit the generated files before regenerating, so a diff reviewer can spot unexpected changes.

For partial regeneration, call `scaffold_package` with `overwrite=True` on a specific temp directory, then copy only the files you want.

## Customising the generated package

The scaffolder is deliberately opinionated. If the template doesn't fit:

- **Edit once, commit, move on.** For most projects, the generated files are a starting point, not a library. Modify `cli.py`, `loaders.py`, and so on as the project matures; don't regenerate.
- **Patch the scaffolder.** The templates live in `nemo_read/scaffold.py` as plain Python strings. Forking is a one-file change.
- **Skip the vendored copy.** Replace `from .nemo_read import ...` with `from nemo_read import ...` in every generated module and delete `src/mypkg/nemo_read/`. This makes the scaffolded package depend on PyPI `nemo_read` instead.

## CI integration

The generated `tests/test_smoke.py` verifies package importability and registry roundtripping without needing a real scenario database. This runs anywhere:

```yaml
# .github/workflows/ci.yml (example)
- run: pip install -e .[dev]
- run: pytest
```

For tests that exercise real data, put the scenario databases in a shared location (S3, Nextcloud) and provide a small fixture that downloads them on demand. The registry already resolves paths relative to the config file, so a test-time TOML pointing at `/tmp/downloaded/BAS.sqlite` works without code changes.
