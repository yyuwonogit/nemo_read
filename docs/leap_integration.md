# LEAP integration notes

Working with NEMO scenario databases inside a live LEAP installation has quirks beyond the schema itself. This reference covers the file layout, lifecycle, and gotchas that come up when coordinating Python analysis with LEAP and NEMO.

## Contents

- [File layout in a LEAP installation](#file-layout-in-a-leap-installation)
- [Where scenario databases actually live](#where-scenario-databases-actually-live)
- [Life cycle of a scenario database](#life-cycle-of-a-scenario-database)
- [The `_def` view lifecycle](#the-_def-view-lifecycle)
- [`solvedtm` and result accumulation](#solvedtm-and-result-accumulation)
- [Version mismatches across LEAP releases](#version-mismatches-across-leap-releases)
- [Reading while LEAP is open](#reading-while-leap-is-open)
- [Writing to scenario databases](#writing-to-scenario-databases)
- [Driving LEAP from Python via the COM API](#driving-leap-from-python-via-the-com-api)

## File layout in a LEAP installation

LEAP stores several things in different folders. The one most relevant here is the **settings folder**, found in LEAP at Settings → Folders → Settings. NEMO scenario databases are created in a subdirectory of this folder by default. LEAP may also store them next to the area file in the working directory, depending on the version and configuration.

A typical Windows layout:

```
C:\Users\<user>\LEAP\            LEAP working / data directory
    <Area name>\
        *.leap                    the area file itself
        ...                       other LEAP data
    <Area name>.sqlite            some versions put scenario DB here

C:\Users\<user>\AppData\...\LEAP\Settings\
    <scenario>.sqlite             others put them here
```

The reliable way to locate the scenario database for an area is through the LEAP COM API:

```python
import win32com.client
leap = win32com.client.Dispatch("LEAP.LEAPApplication")
leap.ActiveArea = "MyArea"
working_dir = leap.WorkingDirectory
settings_dir = leap.SettingsDirectory
```

From there, scan both directories for `.sqlite` files matching the scenario names returned by `leap.Scenarios`.

## Where scenario databases actually live

In LEAP 2024+ with NEMO 2.0+ (data dictionary v11), each scenario in an area that uses NEMO-based optimisation gets its own SQLite file. The naming convention is typically `<Scenario>.sqlite` or `<Area>_<Scenario>.sqlite`. Non-NEMO scenarios (accounting-only) do not produce a SQLite file.

When NEMO recalculates a scenario, LEAP overwrites the existing file entirely: it calls `createnemodb` on the path, which drops and recreates all NEMO tables, then populates them from the LEAP area data. Any custom tables or columns added by the user between runs will be lost.

The FAQ page maintained by SEI explicitly warns about opening the scenario database in a SQLite client while LEAP is attempting to recalculate: the recalculation will fail with a file-lock error. Close the database in your client before pressing Calculate in LEAP.

## Life cycle of a scenario database

A normal calculation cycle proceeds like this:

1. LEAP collects the scenario data from the area file.
2. LEAP calls `NemoMod.createnemodb(path)` which drops all NEMO tables and recreates them at the current schema version.
3. LEAP inserts dimension members and parameter rows derived from the area.
4. LEAP calls `NemoMod.calculatescenario(path, ...)`.
5. NEMO creates `_def` views for every parameter with a registered default.
6. NEMO builds temporary working tables (`nodalstorage`, `yearintervals`).
7. NEMO builds and solves the optimisation problem.
8. NEMO writes each output variable in `varstosave` to its own `v*` table, stamping each row with the current `solvedtm`.
9. Temporary tables are dropped; `_def` views remain.

After step 9, the database is ready for analysis. Reading before step 5 means the `_def` views are not yet present; the library's `get_parameter` falls back to reconstructing the default overlay from `DefaultParams`.

## The `_def` view lifecycle

Parameter tables in NEMO are sparse. A row in `CapitalCost` exists only when the value differs from the default registered in `DefaultParams`. To surface the full cube, NEMO creates a view named `<Parameter>_def` during scenario calculation. The view left-joins the parameter table against the Cartesian product of its dimension members and uses `ifnull(val, default)` to fill gaps.

Three practical consequences:

- **Pre-calculation databases have no `_def` views.** If you open a scenario DB that LEAP has just written but not yet calculated, the views are absent. The library handles this by reconstructing the overlay in Python via `_reconstruct_default_overlay`.
- **Some defaults are zero and the view is intentionally skipped.** `OutputActivityRatio` and `InputActivityRatio` default to 0, and NEMO's source code explicitly skips creating their `_def` views because a zero default would not yield meaningful rows (a zero activity ratio means the technology does not produce or consume that fuel). Reading these parameters through the library returns only the stored rows, matching NEMO's semantics.
- **Manually altering a parameter invalidates views.** If you write directly to a parameter table, re-run `NemoMod.createviewwithdefaults(db, [table])` in Julia or call `setparamdefault` with the current default to rebuild the view. The library does not attempt this because writing is out of scope for the default workflow.

## `solvedtm` and result accumulation

Every `v*` result table carries a `solvedtm TEXT` column populated with the timestamp at which the row was written. NEMO does not clear old result rows between calculations; it appends. A scenario that has been recalculated three times will have three overlapping sets of results in each `v*` table, each with a distinct `solvedtm` string.

The library's `get_result` filters to the latest `solvedtm` by default. To see the full history:

```python
db.solvedtm_values("vtotaldiscountedcost")
```

When accumulation becomes unwieldy, clear with `NemoMod.dropresulttables(db)` from Julia (drops everything starting with `v` or `sqlite_stat`), or issue targeted `DELETE` statements via Python with `read_only=False`. Clearing results does not affect dimensions or parameters.

LEAP's own UI reads the latest `solvedtm`, so accumulation does not usually corrupt the LEAP experience; it just bloats the file.

## Version mismatches across LEAP releases

The NEMO data-dictionary version is the safest way to know what schema you are reading:

```python
db.version                                                     # integer, e.g. 11
```

LEAP releases map to NEMO versions loosely. Major transitions to watch for:

- **LEAP pre-2024** often ships with NEMO 1.x and data-dictionary version 9 or lower. `CapacityFactor` is the name of the availability parameter, not `AvailabilityFactor`. `ReserveMargin` is indexed by `(r, y)` without the fuel dimension.
- **LEAP 2024 with NEMO 2.0+** writes v10 or v11. `AvailabilityFactor` replaces `CapacityFactor`. `ReserveMargin` gains the `f` dimension.
- **LEAP 2024.1+ with NEMO 2.1+** writes v11. `MinAnnualTransmissionNodes` and `MaxAnnualTransmissionNodes` appear.

The library targets v11. It reads v9 and v10 databases without raising, but parameters that were renamed will show up under their current names in `schema.py` and may be absent in older databases. Use `list_tables()` to check presence before assuming a table exists.

To upgrade an older scenario database in place, use the `db_vN_to_vN+1` chain in NemoMod. This is a Julia operation; there is no Python equivalent.

## Reading while LEAP is open

SQLite allows multiple readers but only one writer. When LEAP has an area loaded and is in the middle of a calculation, the scenario database is held in an exclusive transaction and other connections will fail with `database is locked`.

The library defaults to read-only URI connections (`file:path?mode=ro`), which share well with LEAP's reads but still conflict with active writes. Practical pattern:

- For interactive analysis, close the database in any external SQLite client before pressing Calculate in LEAP.
- For scripts that run alongside LEAP, wrap reads in retries on `sqlite3.OperationalError` with exponential backoff, or use `PRAGMA busy_timeout = 5000` on the connection.

The library does not add a busy timeout by default. If you need one, extend the connect context manager locally.

## Writing to scenario databases

This library is designed for analysis and opens read-only by default. Writing is supported but discouraged except for narrow cases (fixing a typo, tagging rows for provenance). For bulk population or branch management, the supported paths are:

- **Julia with `NemoMod`.** The `createnemodb`, `setparamdefault`, and direct `SQLite.DBInterface.execute` calls are the canonical write API. Julia has the advantage of also being able to run `calculatescenario` afterwards.
- **Python with `pywin32` driving the LEAP COM API.** Create or modify branches in LEAP, then trigger `Calculate`, which regenerates the scenario database from the current area state. Suitable for scripted generation of scenario variants.

Direct Python writes to the scenario database bypass LEAP's validation and the next LEAP recalculation will overwrite them. Avoid unless you control the full lifecycle.

## Driving LEAP from Python via the COM API

The LEAP COM API is accessible on Windows with `pywin32`. Typical boilerplate:

```python
import win32com.client
leap = win32com.client.Dispatch("LEAP.LEAPApplication")
leap.ActiveArea = "MyArea"

# Enumerate scenarios:
for scenario in leap.Scenarios:
    print(scenario.Name, scenario.ResultsShown)

# Trigger a calculation:
leap.Calculate(False)                                          # False = foreground

# Locate the scenario database after calculation:
from pathlib import Path
working_dir = Path(leap.WorkingDirectory)
candidates = list(working_dir.rglob("*.sqlite"))
```

The COM type library (`TypeLib_LEAP_API_full.txt` in the LEAP install directory, or dumped to `config/` in SEI-international example projects) lists every Dispatch-accessible method and property. For building or editing branches programmatically, the key entry points are `Branches`, `Tree`, and the per-scenario value expressions.

After `Calculate`, open the resulting file with `NemoDB` for analysis. A common one-shot workflow:

```python
import win32com.client
from pathlib import Path
from nemo_read import NemoDB, print_overview

leap = win32com.client.Dispatch("LEAP.LEAPApplication")
leap.ActiveArea = "MyArea"
leap.Calculate(False)

scenario_db = Path(leap.SettingsDirectory) / f"{leap.Scenarios.Item(1).Name}.sqlite"
with NemoDB(scenario_db) as nothing:
    pass  # placeholder if NemoDB gains context manager support in future

db = NemoDB(scenario_db)
print_overview(db)
```

The COM API is synchronous; `Calculate(False)` blocks until NEMO finishes, so there is no race between the end of calculation and opening the file for reading.
