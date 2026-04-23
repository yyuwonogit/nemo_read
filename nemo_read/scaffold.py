"""
Scaffold a repo-ready Python package that wraps ``nemo_read`` for a specific
project.

Why this exists
---------------
``nemo_read`` is the generic reader. Most research repos want a project-level
package on top of it: a registry of known scenario paths, high-level loaders
that take friendly names (``load_scenario("BAS")``), a cache layer for
expensive reads, a CLI, and autocompletable dimension types derived from the
actual scenario data.

This module emits all of that as a modern ``src``-layout Python package. The
output is a self-contained directory the user can drop into a repo, run
``pip install -e .``, and start analysing.

Usage (CLI, after installing ``nemo_read``)::

    nemo_read-scaffold mypkg ./path/to/dest \\
        --author "Ahrin" \\
        --scenario BAS=data/BAS.sqlite \\
        --scenario ATS=data/ATS.sqlite \\
        --reference-db data/BAS.sqlite

Usage (Python)::

    from nemo_read.scaffold import scaffold_package
    scaffold_package(
        name="mypkg",
        dest="./mypkg",
        author="Ahrin",
        scenarios={"BAS": "data/BAS.sqlite", "ATS": "data/ATS.sqlite"},
        reference_db="data/BAS.sqlite",
    )

What gets generated
-------------------
::

    <dest>/
    ├── pyproject.toml
    ├── README.md
    ├── .gitignore
    ├── src/<pkg>/
    │   ├── __init__.py        re-exports public API
    │   ├── nemo_read/          vendored copy of the reader library
    │   ├── registry.py        Registry class backed by scenarios.toml
    │   ├── loaders.py         load_scenario, compare_scenarios
    │   ├── cache.py           Parquet cache for expensive reads
    │   ├── cli.py             argparse CLI with list/info/export/dims
    │   ├── dimensions.py      Literal types for region/tech/fuel (optional)
    │   └── scenarios.toml     user-editable scenario registry
    ├── tests/
    │   ├── __init__.py
    │   └── test_smoke.py
    └── notebooks/
        └── explore.py         starter script for interactive work

Design notes
------------
* ``nemo_read`` is vendored into ``src/<pkg>/nemo_read/`` rather than pulled
  as a dependency. Research repos rarely want external PyPI dependencies for
  internal libraries. The generated package imports via ``from .nemo_read``
  to keep the boundary explicit.
* The TOML registry keeps scenario paths in one place, versioned in git,
  and swappable per environment by pointing at a different config file.
* Dimension introspection (``--reference-db``) opens one scenario and emits
  ``typing.Literal`` aliases for region/technology/fuel/etc. codes. Editors
  pick these up and autocomplete scenario-specific values.
* Overwriting is opt-in. The scaffolder refuses to clobber existing files
  unless ``overwrite=True`` is passed.
"""

from __future__ import annotations

import argparse                                                # CLI parsing
import re                                                      # package-name validation
import shutil                                                  # file copy for vendoring
import sqlite3                                                 # introspect reference DB
from pathlib import Path                                       # path handling
from typing import Dict, Iterable, List, Mapping, Optional, Union

# Resolve the directory of the currently-executing nemo_read package so we
# can locate sibling modules to vendor into the generated package.
_PACKAGE_DIR = Path(__file__).resolve().parent

# Modules that belong in the vendored copy. Deliberately excludes scaffold.py
# itself (a scaffolded package does not need to re-scaffold).
_VENDOR_MODULES: tuple[str, ...] = (
    "__init__.py",
    "custom.py",
    "db.py",
    "dimensions.py",
    "export.py",
    "infeasibility.py",
    "inspect.py",
    "leap_conventions.py",
    "parameters.py",
    "schema.py",
    "timeslice.py",
    "validate.py",
    "variables.py",
)

# Characters allowed in a distribution name (PEP 508 / PEP 503 normalised form).
_DIST_NAME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_\-]*$")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def scaffold_package(
    name: str,
    dest: Union[str, Path],
    author: str = "",
    scenarios: Optional[Mapping[str, str]] = None,
    reference_db: Optional[Union[str, Path]] = None,
    description: str = "",
    overwrite: bool = False,
) -> Path:
    """Create a repo-ready Python package at ``dest``.

    Parameters
    ----------
    name
        Distribution name (PyPI-style). Hyphens are allowed; the Python
        module name is derived by replacing hyphens with underscores.
    dest
        Target directory. Created if it does not exist. If the directory
        already contains files and ``overwrite`` is False, the call raises.
    author
        Used in ``pyproject.toml`` and the README.
    scenarios
        Mapping of friendly scenario names to database paths. Paths are
        stored verbatim in ``scenarios.toml``, so keep them repo-relative
        if you want the package to work for collaborators.
    reference_db
        Optional path to one scenario database. If provided, it is opened
        read-only and used to generate ``dimensions.py`` with ``Literal``
        aliases for every populated dimension. Useful for IDE autocomplete.
    description
        One-line project description for ``pyproject.toml`` and the README.
    overwrite
        If True, existing files in ``dest`` are overwritten silently.

    Returns
    -------
    Path
        The ``dest`` directory as an absolute path.
    """
    # Validate the distribution name up front so we fail fast on typos.
    if not _DIST_NAME_RE.match(name):
        raise ValueError(
            f"Invalid package name {name!r}. Use letters, digits, hyphens, "
            f"or underscores, starting with a letter."
        )

    dest_path = Path(dest).expanduser().resolve()              # canonicalise path
    pkg_name = name.replace("-", "_")                          # Python module name
    cli_name = name.lower()                                    # CLI entry-point
    description = description or (
        f"Data access for LEAP/NEMO scenario databases in this repository."
    )

    # Scenario registry: default to a small example if the caller didn't
    # provide one, so the generated package runs out of the box.
    scenarios = dict(scenarios) if scenarios else {
        "BAS": "data/BAS.sqlite",
        "ATS": "data/ATS.sqlite",
    }

    # Ensure target exists; refuse to clobber unless overwrite is set.
    _prepare_destination(dest_path, overwrite=overwrite)

    # Build the directory skeleton.
    src_pkg_dir = dest_path / "src" / pkg_name                 # where our code lives
    src_pkg_dir.mkdir(parents=True, exist_ok=True)             # create full path
    (dest_path / "tests").mkdir(parents=True, exist_ok=True)   # test dir
    (dest_path / "notebooks").mkdir(parents=True, exist_ok=True)  # starter scripts

    # Write top-level project files.
    _write(dest_path / "pyproject.toml",
           _render_pyproject(name=name, pkg=pkg_name, cli_name=cli_name,
                             author=author, description=description),
           overwrite=overwrite)
    _write(dest_path / "README.md",
           _render_readme(name=name, pkg=pkg_name, cli_name=cli_name,
                          description=description, scenarios=scenarios),
           overwrite=overwrite)
    _write(dest_path / ".gitignore", _GITIGNORE, overwrite=overwrite)

    # Write package modules.
    _write(src_pkg_dir / "__init__.py",
           _render_init(pkg=pkg_name, name=name, description=description),
           overwrite=overwrite)
    _write(src_pkg_dir / "registry.py", _REGISTRY_PY, overwrite=overwrite)
    _write(src_pkg_dir / "loaders.py", _LOADERS_PY, overwrite=overwrite)
    _write(src_pkg_dir / "cache.py", _CACHE_PY, overwrite=overwrite)
    _write(src_pkg_dir / "cli.py",
           _render_cli(pkg=pkg_name, cli_name=cli_name),
           overwrite=overwrite)

    # scenarios.toml: user-editable registry.
    _write(src_pkg_dir / "scenarios.toml",
           _render_scenarios_toml(scenarios),
           overwrite=overwrite)

    # Optional: introspect a reference database to emit Literal types.
    if reference_db is not None:
        dims = _introspect_dimensions(Path(reference_db))      # dict of dim → members
        _write(src_pkg_dir / "dimensions.py",
               _render_dimensions(dims, ref_path=Path(reference_db)),
               overwrite=overwrite)

    # Vendor the nemo_read library.
    _vendor_nemo_read(src_pkg_dir / "nemo_read", overwrite=overwrite)

    # Tests.
    _write(dest_path / "tests" / "__init__.py", "", overwrite=overwrite)
    _write(dest_path / "tests" / "test_smoke.py",
           _render_test_smoke(pkg=pkg_name),
           overwrite=overwrite)

    # Starter notebook-as-script (works in any editor, runs as a module).
    _write(dest_path / "notebooks" / "explore.py",
           _render_explore(pkg=pkg_name),
           overwrite=overwrite)

    return dest_path


def cli_main(argv: Optional[List[str]] = None) -> int:
    """Entry point exposed as ``nemo_read-scaffold`` via ``pyproject.toml``."""
    parser = argparse.ArgumentParser(
        prog="nemo_read-scaffold",
        description="Generate a repo-ready Python package around nemo_read.",
    )
    parser.add_argument("name", help="Distribution name (e.g. 'myproject-nemo').")
    parser.add_argument("dest", help="Target directory.")
    parser.add_argument("--author", default="", help="Author name for pyproject.toml.")
    parser.add_argument(
        "--scenario",
        action="append",
        default=[],
        metavar="NAME=PATH",
        help="Register a scenario. Repeatable. Example: --scenario BAS=data/BAS.sqlite",
    )
    parser.add_argument(
        "--reference-db",
        default=None,
        help="Path to one scenario database; used to emit Literal "
             "dimension types for IDE autocomplete.",
    )
    parser.add_argument("--description", default="", help="One-line description.")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing files instead of refusing.",
    )
    args = parser.parse_args(argv)                             # parse inputs

    # Parse --scenario NAME=PATH pairs into a dict.
    scenarios: Dict[str, str] = {}
    for item in args.scenario:
        if "=" not in item:
            parser.error(f"Expected NAME=PATH for --scenario, got {item!r}")
        key, val = item.split("=", 1)
        scenarios[key.strip()] = val.strip()

    # Delegate to the Python API.
    out = scaffold_package(
        name=args.name,
        dest=args.dest,
        author=args.author,
        scenarios=scenarios or None,
        reference_db=args.reference_db,
        description=args.description,
        overwrite=args.overwrite,
    )
    print(f"Scaffolded package at {out}")
    return 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _prepare_destination(dest: Path, overwrite: bool) -> None:
    """Create ``dest`` or verify it is empty enough to write into."""
    if dest.exists():                                          # existing dir
        if not dest.is_dir():                                  # something non-dir
            raise NotADirectoryError(f"{dest} exists and is not a directory.")
        if any(dest.iterdir()) and not overwrite:              # non-empty + guard
            raise FileExistsError(
                f"{dest} is not empty. Pass overwrite=True to clobber."
            )
    else:
        dest.mkdir(parents=True)                               # create fresh


def _write(path: Path, text: str, overwrite: bool) -> None:
    """Write text to ``path``, honouring the overwrite flag."""
    if path.exists() and not overwrite:                        # guard
        raise FileExistsError(f"{path} already exists (pass overwrite=True).")
    path.parent.mkdir(parents=True, exist_ok=True)             # ensure parent dir
    path.write_text(text, encoding="utf-8")                    # atomic-ish write


def _vendor_nemo_read(target: Path, overwrite: bool) -> None:
    """Copy nemo_read's source files into ``target/`` as a subpackage."""
    target.mkdir(parents=True, exist_ok=True)                  # ensure dir exists
    for module in _VENDOR_MODULES:                             # copy each file
        src = _PACKAGE_DIR / module                            # source file in skill
        if not src.exists():                                   # defensive
            continue
        dst = target / module                                  # destination
        if dst.exists() and not overwrite:                     # guard
            raise FileExistsError(f"{dst} exists; pass overwrite=True.")
        shutil.copyfile(src, dst)                              # preserve text

    # The stock ``__init__.py`` re-exports ``scaffold_package`` from
    # ``nemo_read.scaffold``. The scaffolder itself is intentionally NOT
    # vendored (a scaffolded package has no reason to re-scaffold), so we
    # scrub those references from the copy.
    init_path = target / "__init__.py"                         # vendored init
    if init_path.exists():                                     # defensive
        text = init_path.read_text(encoding="utf-8")           # read
        text = text.replace("from .scaffold import scaffold_package\n", "")
        text = text.replace('    "scaffold_package",\n', "")
        init_path.write_text(text, encoding="utf-8")           # write back


def _introspect_dimensions(db_path: Path) -> Dict[str, List[str]]:
    """Open ``db_path`` read-only and read members of every scalar dimension."""
    if not db_path.exists():                                   # early failure
        raise FileNotFoundError(db_path)

    # Use a URI so we can enforce read-only mode without touching the file.
    con = sqlite3.connect(f"file:{db_path.resolve()}?mode=ro", uri=True)
    try:
        # Only pull dimensions where the primary key is the `val` column
        # and membership is a flat list of strings. This excludes mapping
        # tables like LTsGroup and the hybrid TransmissionLine.
        targets = ("REGION", "REGIONGROUP", "TECHNOLOGY", "FUEL", "EMISSION",
                   "MODE_OF_OPERATION", "STORAGE", "YEAR", "TIMESLICE", "NODE")
        out: Dict[str, List[str]] = {}                         # accumulator
        for dim in targets:                                    # iterate
            try:
                rows = con.execute(f"SELECT val FROM {dim} ORDER BY val").fetchall()
            except sqlite3.DatabaseError:
                continue                                       # dim not present
            members = [str(r[0]) for r in rows if r[0] is not None]
            if members:                                        # only keep populated
                out[dim] = members
        return out
    finally:
        con.close()                                            # always tidy


# ---------------------------------------------------------------------------
# Renderers (templates are plain strings with str.format placeholders)
# ---------------------------------------------------------------------------

def _render_pyproject(name: str, pkg: str, cli_name: str,
                      author: str, description: str) -> str:
    author_line = f'{{name = "{author}"}}' if author else "{name = \"\"}"
    return f"""\
[build-system]
requires = ["setuptools>=61"]
build-backend = "setuptools.build_meta"

[project]
name = "{name}"
version = "0.1.0"
description = "{description}"
authors = [{author_line}]
requires-python = ">=3.11"
readme = "README.md"
dependencies = [
    "pandas>=2.0",
    "numpy>=1.24",
    "xarray>=2023.1",
    "pyarrow>=14",
]

[project.optional-dependencies]
dev = [
    "pytest>=7",
    "ruff>=0.6",
]

[project.scripts]
{cli_name} = "{pkg}.cli:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-data]
"{pkg}" = ["scenarios.toml"]

[tool.pytest.ini_options]
testpaths = ["tests"]
"""


def _render_readme(name: str, pkg: str, cli_name: str,
                   description: str, scenarios: Mapping[str, str]) -> str:
    scenario_block = "\n".join(f"    {k} = \"{v}\"" for k, v in scenarios.items())
    return f"""\
# {name}

{description}

Generated by `nemo_read-scaffold`. Wraps the vendored `nemo_read` reader with a
project-specific scenario registry, high-level loaders, a Parquet cache, and
a small CLI.

## Install

```
pip install -e .
```

## Configure scenarios

Edit `src/{pkg}/scenarios.toml`. Paths are resolved relative to the TOML
file by default; flip `paths_relative_to_config = false` to resolve against
the current working directory instead.

```toml
paths_relative_to_config = true

[scenarios]
{scenario_block}
```

## Use from Python

```python
from {pkg} import load_scenario, compare_scenarios, print_overview

db = load_scenario("BAS")
print_overview(db)

delta = compare_scenarios(["BAS", "ATS"], "vtotalcapacityannual")
```

## Use from the CLI

```
{cli_name} list
{cli_name} info BAS
{cli_name} dims BAS
{cli_name} export BAS --out exports/
```

## Dimension autocompletion

If the package was scaffolded with `--reference-db`, a `dimensions.py`
module defines `Literal` aliases for region, technology, fuel, and other
dimension members. Import them for IDE autocomplete:

```python
from {pkg}.dimensions import Region, Technology
def summarise(r: Region, t: Technology) -> None: ...
```

## Layout

```
src/{pkg}/
├── __init__.py          public API re-exports
├── nemo_read/            vendored NEMO reader (the thing that decodes SQLite)
├── registry.py          ScenarioRegistry backed by scenarios.toml
├── loaders.py           load_scenario, compare_scenarios
├── cache.py             ParquetCache for expensive reads
├── cli.py               argparse CLI
├── dimensions.py        Literal dimension types (optional)
└── scenarios.toml       registry configuration
```
"""


def _render_init(pkg: str, name: str, description: str) -> str:
    return f'''\
"""{name}: {description}

Public API
----------
* :class:`NemoDB`, :func:`print_overview`, :func:`inspect_scenario` from
  the vendored ``nemo_read`` reader.
* :class:`Registry` and the :func:`load_scenario` / :func:`compare_scenarios`
  loaders for project-specific scenario access.
* :class:`ParquetCache` for caching expensive reads to disk.
"""

from __future__ import annotations

# Re-export the most common reader API so callers rarely need the nested
# ``nemo_read`` import path.
from .nemo_read import (
    NemoDB,
    inspect_scenario,
    print_overview,
    get_parameter,
    get_result,
    list_present_results,
    list_populated_parameters,
    parameter_to_dataarray,
    result_to_dataarray,
)

# Project-level additions.
from .registry import Registry
from .loaders import load_scenario, compare_scenarios
from .cache import ParquetCache

__all__ = [
    "NemoDB",
    "inspect_scenario",
    "print_overview",
    "get_parameter",
    "get_result",
    "list_present_results",
    "list_populated_parameters",
    "parameter_to_dataarray",
    "result_to_dataarray",
    "Registry",
    "load_scenario",
    "compare_scenarios",
    "ParquetCache",
]

__version__ = "0.1.0"
'''


def _render_cli(pkg: str, cli_name: str) -> str:
    return f'''\
"""Command-line interface for {pkg}."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .registry import Registry
from .loaders import load_scenario
from .nemo_read import print_overview, inspect_scenario, dump_to_csv


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="{cli_name}",
        description="Inspect and export LEAP/NEMO scenario databases.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="List scenarios in the registry.")

    p_info = sub.add_parser("info", help="Print an overview of a scenario.")
    p_info.add_argument("scenario")

    p_dims = sub.add_parser("dims", help="Show dimension sizes for a scenario.")
    p_dims.add_argument("scenario")

    p_export = sub.add_parser("export", help="Dump tables to CSV.")
    p_export.add_argument("scenario")
    p_export.add_argument("--out", required=True, help="Output directory.")
    p_export.add_argument(
        "--include", default="all",
        choices=["all", "dimensions", "parameters", "results"],
        help="Which table families to export.",
    )
    p_export.add_argument(
        "--with-defaults", action="store_true",
        help="Materialise parameter tables with defaults applied.",
    )

    args = parser.parse_args(argv)

    if args.cmd == "list":
        reg = Registry.from_default()
        for nm in reg.names():
            print(f"{{nm}}  {{reg.path(nm)}}")
        return 0

    if args.cmd == "info":
        db = load_scenario(args.scenario)
        print_overview(db)
        return 0

    if args.cmd == "dims":
        db = load_scenario(args.scenario)
        ov = inspect_scenario(db)
        print(ov["dimensions"].to_string(index=False))
        return 0

    if args.cmd == "export":
        db = load_scenario(args.scenario)
        written = dump_to_csv(db, args.out, include=args.include,
                              with_defaults=args.with_defaults)
        print(f"Wrote {{len(written)}} tables to {{Path(args.out).resolve()}}")
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
'''


def _render_scenarios_toml(scenarios: Mapping[str, str]) -> str:
    header = (
        "# Scenario registry. Paths are resolved relative to this file\n"
        "# unless paths_relative_to_config is set to false.\n"
        "paths_relative_to_config = true\n\n"
        "[scenarios]\n"
    )
    body = "\n".join(f'{k} = "{v}"' for k, v in scenarios.items())
    return header + body + "\n"


def _render_dimensions(dims: Mapping[str, List[str]], ref_path: Path) -> str:
    """Generate ``dimensions.py`` with ``Literal`` aliases for each populated
    dimension."""
    lines: List[str] = []
    lines.append('"""')
    lines.append("Generated dimension literals from a reference scenario.")
    lines.append("")
    lines.append(f"Source: {ref_path}")
    lines.append("")
    lines.append("Import these aliases to get IDE autocomplete for dimension")
    lines.append("members when writing analysis code. Regenerate this file")
    lines.append("after adding new regions, technologies, or fuels to the")
    lines.append("reference scenario.")
    lines.append('"""')
    lines.append("")
    lines.append("from __future__ import annotations")
    lines.append("from typing import Literal")
    lines.append("")

    # Map dimension names to the idiomatic Python alias name.
    alias_map = {
        "REGION":            "Region",
        "REGIONGROUP":       "RegionGroup",
        "TECHNOLOGY":        "Technology",
        "FUEL":              "Fuel",
        "EMISSION":          "Emission",
        "MODE_OF_OPERATION": "ModeOfOperation",
        "STORAGE":           "Storage",
        "YEAR":              "Year",
        "TIMESLICE":         "Timeslice",
        "NODE":              "Node",
    }

    for dim, members in dims.items():                          # iterate known dims
        alias = alias_map.get(dim, dim.title())                # Pythonic name
        if not members:                                        # skip empty
            continue
        # Format the Literal with one member per line to keep diffs readable
        # when the scenario grows.
        member_lines = ",\n    ".join(repr(m) for m in members)
        lines.append(f"{alias} = Literal[\n    {member_lines},\n]")
        lines.append("")

    # All-members list for iteration convenience.
    lines.append("__all__ = [")
    for dim in dims:
        alias = alias_map.get(dim, dim.title())
        lines.append(f'    "{alias}",')
    lines.append("]")
    lines.append("")
    return "\n".join(lines)


def _render_test_smoke(pkg: str) -> str:
    return f'''\
"""Smoke tests for {pkg}.

These verify the package imports cleanly and that its public API is wired
up. Tests that require a real scenario database live alongside that data
and are skipped here.
"""
from __future__ import annotations

import importlib


def test_package_imports():
    mod = importlib.import_module("{pkg}")
    for attr in ("NemoDB", "Registry", "load_scenario", "compare_scenarios",
                 "ParquetCache", "print_overview", "inspect_scenario"):
        assert hasattr(mod, attr), f"{{{{attr}}}} missing from {pkg} public API"


def test_vendored_nemo_read_imports():
    from {pkg} import nemo_read
    assert nemo_read.TARGET_DB_VERSION >= 11


def test_registry_roundtrip(tmp_path):
    from {pkg}.registry import Registry
    cfg = tmp_path / "scenarios.toml"
    cfg.write_text(
        'paths_relative_to_config = true\\n'
        '[scenarios]\\n'
        'DEMO = "demo.sqlite"\\n'
    )
    reg = Registry.from_toml(cfg)
    assert reg.names() == ["DEMO"]
    assert reg.path("DEMO").name == "demo.sqlite"
'''


def _render_explore(pkg: str) -> str:
    return f'''\
"""Starter script for exploratory work with {pkg}.

Run as a normal Python file, or convert to a Jupyter notebook with
``jupytext --to ipynb explore.py``.
"""
from __future__ import annotations

from {pkg} import (
    load_scenario,
    compare_scenarios,
    print_overview,
    get_parameter,
    get_result,
    Registry,
)


def main() -> None:
    # List registered scenarios.
    reg = Registry.from_default()
    print("Registered scenarios:")
    for nm in reg.names():
        print(f"  {{nm}}: {{reg.path(nm)}}")

    if not reg.names():
        print("No scenarios registered. Edit scenarios.toml to add some.")
        return

    # Open the first scenario and print an overview.
    first = reg.names()[0]
    db = load_scenario(first)
    print_overview(db)

    # Example: read total installed capacity by year.
    if "vtotalcapacityannual" in db.list_tables():
        cap = get_result(db, "vtotalcapacityannual")
        print(cap.groupby("y")["val"].sum().to_string())


if __name__ == "__main__":
    main()
'''


# ---------------------------------------------------------------------------
# Static template bodies (no interpolation needed)
# ---------------------------------------------------------------------------

_GITIGNORE = """\
# Python
__pycache__/
*.py[cod]
*.egg-info/
.venv/
venv/
env/
.eggs/
build/
dist/

# Pytest / coverage
.pytest_cache/
.coverage
htmlcov/

# Editors
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db

# Data
*.sqlite-journal
*.sqlite-wal
*.sqlite-shm

# Cache
.cache/
"""


_REGISTRY_PY = '''\
"""Scenario registry backed by a TOML file.

The registry maps friendly scenario names (``"BAS"``, ``"ATS"``, ...) to
SQLite database paths. A single TOML file is the source of truth for the
whole project, so analysts, collaborators, and CI all see the same
scenarios without editing code.
"""
from __future__ import annotations

import tomllib                                                 # stdlib (3.11+)
from pathlib import Path
from typing import Iterator, List, Mapping, Union

# Default location: the scenarios.toml shipped with this package.
_DEFAULT_CONFIG = Path(__file__).resolve().parent / "scenarios.toml"


class Registry:
    """Mapping of scenario names to database paths.

    Instances behave like read-only dictionaries keyed by scenario name.
    """

    def __init__(
        self,
        mapping: Mapping[str, Union[str, Path]],
        root: Path,
    ) -> None:
        # ``root`` is the directory that relative paths are resolved against.
        # We normalise everything to absolute paths up front so callers can
        # pass the values straight into ``NemoDB``.
        self._root = Path(root).resolve()
        self._paths: dict[str, Path] = {}
        for name, raw in mapping.items():
            p = Path(raw)
            self._paths[name] = p if p.is_absolute() else (self._root / p).resolve()

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    @classmethod
    def from_toml(cls, path: Union[str, Path]) -> "Registry":
        """Load from a TOML file.

        The file layout is::

            paths_relative_to_config = true

            [scenarios]
            BAS = "../data/BAS.sqlite"
            ATS = "../data/ATS.sqlite"
        """
        cfg_path = Path(path).resolve()
        with open(cfg_path, "rb") as fh:                       # tomllib needs bytes
            data = tomllib.load(fh)
        scenarios = data.get("scenarios", {}) or {}
        rel_to_cfg = bool(data.get("paths_relative_to_config", True))
        root = cfg_path.parent if rel_to_cfg else Path.cwd()
        return cls(scenarios, root=root)

    @classmethod
    def from_default(cls) -> "Registry":
        """Load from the scenarios.toml shipped with the package."""
        return cls.from_toml(_DEFAULT_CONFIG)

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------
    def names(self) -> List[str]:
        """Sorted list of registered scenario names."""
        return sorted(self._paths)

    def path(self, name: str) -> Path:
        """Absolute path to the SQLite file for ``name``."""
        if name not in self._paths:                            # friendly error
            known = ", ".join(self.names()) or "<none>"
            raise KeyError(f"Scenario {name!r} not in registry. Known: {known}")
        return self._paths[name]

    def __contains__(self, name: object) -> bool:              # `in` support
        return name in self._paths

    def __iter__(self) -> Iterator[str]:                       # `for` support
        return iter(self.names())

    def __len__(self) -> int:
        return len(self._paths)

    def __repr__(self) -> str:
        inner = ", ".join(f"{k!r}: {str(v)!r}" for k, v in self._paths.items())
        return f"Registry({{{inner}}})"
'''


_LOADERS_PY = '''\
"""High-level loaders.

These wrap the vendored ``nemo_read`` primitives with project-aware helpers
that know how to resolve scenario names against the ``Registry``.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Optional

import pandas as pd

from .nemo_read import NemoDB, get_result
from .registry import Registry


def load_scenario(
    name: str,
    registry: Optional[Registry] = None,
    read_only: bool = True,
) -> NemoDB:
    """Open the scenario registered under ``name`` and return a ``NemoDB``."""
    reg = registry or Registry.from_default()                  # fall back to default
    return NemoDB(reg.path(name), read_only=read_only)


def compare_scenarios(
    names: Iterable[str],
    variable: str,
    registry: Optional[Registry] = None,
) -> pd.DataFrame:
    """Stack a result variable across scenarios into a single long frame.

    The returned frame has all dimension columns of the variable, its
    ``val``, plus a ``scenario`` column identifying the source. Latest
    ``solvedtm`` per scenario is used.
    """
    reg = registry or Registry.from_default()                  # default registry
    frames: List[pd.DataFrame] = []                            # accumulator
    for name in names:                                         # iterate scenarios
        db = NemoDB(reg.path(name))                            # open each
        df = get_result(db, variable).copy()                   # latest solve
        df["scenario"] = name                                  # tag
        frames.append(df)                                      # collect
    if not frames:                                             # empty input
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)                # one long frame
'''


_CACHE_PY = '''\
"""Parquet cache for expensive derived tables.

Typical workflow: the first call computes a DataFrame from one or more
scenarios and writes a Parquet file. Subsequent calls read the Parquet
file directly, which is typically an order of magnitude faster than
re-opening the SQLite databases and re-pivoting.

The cache key is arbitrary text chosen by the caller. Convention: include
the scenario name, variable name, and any filters in the key so changing
them produces a distinct cache file.
"""
from __future__ import annotations

import hashlib                                                 # stable key hashing
from pathlib import Path
from typing import Callable, Optional

import pandas as pd


class ParquetCache:
    """Filesystem-backed cache for pandas DataFrames.

    Parameters
    ----------
    cache_dir
        Directory where Parquet files are stored. Created if missing.
    """

    def __init__(self, cache_dir: Path | str = ".cache/nemo"):
        self.cache_dir = Path(cache_dir)                       # store config
        self.cache_dir.mkdir(parents=True, exist_ok=True)      # ensure present

    def _path_for(self, key: str) -> Path:
        """Deterministic path inside the cache directory for a given key."""
        digest = hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]
        return self.cache_dir / f"{digest}.parquet"

    def get(self, key: str) -> Optional[pd.DataFrame]:
        """Return the cached frame for ``key`` if present, else ``None``."""
        p = self._path_for(key)                                # resolve
        return pd.read_parquet(p) if p.exists() else None      # load or miss

    def put(self, key: str, df: pd.DataFrame) -> Path:
        """Write ``df`` to the cache under ``key``; return the path."""
        p = self._path_for(key)                                # resolve
        df.to_parquet(p, index=False)                          # write Parquet
        return p

    def get_or_compute(
        self,
        key: str,
        compute: Callable[[], pd.DataFrame],
    ) -> pd.DataFrame:
        """Return the cached value for ``key`` or compute, store, and return it."""
        cached = self.get(key)                                 # try hot path
        if cached is not None:                                 # cache hit
            return cached
        df = compute()                                         # cache miss
        self.put(key, df)                                      # persist
        return df

    def clear(self) -> None:
        """Delete every Parquet file in the cache directory."""
        for f in self.cache_dir.glob("*.parquet"):             # iterate files
            f.unlink()                                         # remove each
'''
