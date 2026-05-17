# nemo_read

**Read, decode, author, and analyse LEAP/NEMO scenario data — with every LEAP COM operation funneled through a standardised, CI-enforced framework so the same mistake never ships twice.**

## Why

A NEMO scenario `.sqlite` carries the numbers but loses the LEAP-side context — sectors, branch hierarchy, custom-constraint sources, formula expressions. `nemo_read` recovers all of it AND closes the loop by authoring upstream fixes back into LEAP via COM. Every LEAP write goes through a sealed chokepoint with pre-flight CSV validation; every long-running probe runs in one warm COM session with structured heartbeat monitoring. Lessons from real failure modes (LP infeasibilities, COM modal popups, separator-encoding traps) are encoded as pytest tripwires, not just prose.

## The thirteen capabilities

| # | The Name | What it does | Primary entry points |
|---|---|---|---|
| 1 | **THE ORACLE** | Reads what NEMO already calculated — opens `.sqlite` scenario databases, decodes dimensions, returns named DataFrames for parameters and results. | `NemoDB`, `get_result`, `get_parameter`, `capacity_stack`, `energy_balance`, `print_overview`, `inspect_scenario` |
| 2 | **THE PROBE** | Reads live LEAP area state via COM — branch tree, variable expressions, input units, result values, scenarios, regions. Long-running probes loop scenarios in ONE warm COM session. | `CanonicalProber` (subclass + `.run()`), `safe_value`, `safe_expression`, `safe_data_unit_text` |
| 3 | **THE FORGE** | Pushes authored data UPSTREAM into LEAP via COM. Multi-phase warm-COM flow: dry-run → confirm → real inject → readback verify; multi-scenario in one COM session. | `CanonicalInjector` (subclass + `.run()`), `safe_set_expression` |
| 4 | **THE SCRIBE** | Adapter pattern: hand-authored sector CSVs → normalised canonical CSV ready for THE FORGE. Auto-normalises `Interp()` separators at write time. | Each sector's `build_canonical.py` + `normalize_interp` |
| 5 | **THE WARDEN** | Pre-flight static infeasibility detection on a NEMO scenario before the solver runs. General (region, fuel, year) fuel mass-balance audit names contributing techs. | `validate_scenario`, `find_infeasibilities`, `check_scenario` |
| 6 | **THE SEER** | Post-mortem forensics when the solver returned INFEASIBLE — decodes `xN` columns to (var, region, tech, year), classifies clusters bug/intent/unknown, proposes ranked placeholder patches. | `decode_lp_column`, `classify_parameter`, `forensics_for_pinned_variable`, `propose_placeholders`, `emit_probe_brief` |
| 7 | **THE HERALD** | Heartbeat broadcasting for long-running COM ops — structured stdout every 30s + parallel `_progress_*.json` updated every tick. Wired automatically into THE PROBE and THE FORGE. | `HeartbeatLogger`, `read_progress` |
| 8 | **THE SIGIL** | The sealed mark on every `Interp(...)` expression — only comma list-separator + period decimal is permitted on this engine. Enforced at three layers: adapter write-time, injector chokepoint, pre-flight CSV scan. | `normalize_interp`, `assert_interp_canonical`, `validate_canonical_csv_expressions`, `InterpSeparatorError` |
| 9 | **THE GATE** | The only sanctioned passage for writing `Variable.Expression` to LEAP. Sealed against override; subclass attempt raises `InjectorSealError` at class-definition time. Every sector's writes pass through here. | `safe_set_expression`, `compare_expressions` |
| 10 | **THE ATLAS** | Frozen map of the NEMO v11 schema — every dimension, parameter, result-variable, source mapping, branch type, unit. The reference the rest of the library reads from. | `DIMENSIONS`, `PARAMETERS`, `RESULT_VARIABLES`, `LEAP_SOURCE_MAP`, `LEAP_BRANCH_TYPES`, `LEAP_NEMO_UNITS` |
| 11 | **THE ALCHEMIST** | Transmutes between source-author units and LEAP-native units, with cited conversion factors and a 5★ confidence rubric. Audits canonical CSVs against the LEAP area's expected units. | `audit_canonical_units`, `apply_audit_conversions`, `propose_conversion`, `list_known_conversions`, `ConversionProposal` |
| 12 | **THE DIVINER** | Cost and result decomposition — given a result row, trace back which input parameters and bound constraints produced it. Reveals whether a value hit lower bound, upper bound, or sits free. | `trace_cost`, `trace_result`, `BoundCheck`, `CostBreakdown`, `ResultTrace` |
| 13 | **THE BLUEPRINT** | Scaffolds a new package skeleton following the established conventions (flat layout, `pyproject.toml`, GitHub Actions trusted publishing). The pattern reused across sibling repos. | `scaffold_package`, `nemo_read-scaffold` CLI |

All thirteen are top-level discoverable: `from nemo_read import <name>`. The tripwire `tests/test_public_api_completeness.py` guarantees no future capability ships without being re-exported.

## The silent layer — what enforces the rules

| Tripwire | What fails CI if violated |
|---|---|
| `tests/test_interp_separator.py` | THE SIGIL violations in any canonical CSV |
| `tests/test_inject_base.py` | THE GATE bypass (`var.Expression = expr` anywhere outside the chokepoint) + sealed-method override on `CanonicalInjector` |
| `tests/test_probe_base.py` | THE PROBE's sealed BT={3,50} unit-read guard bypass + sealed-method override on `CanonicalProber` |
| `tests/test_public_api_completeness.py` | Any public class/function in `nemo_read/` missing from `__all__` |
| `tests/test_claude_md_rules_enforced.py` | Version drift (`pyproject.toml` ↔ `__init__.py`) + `Unlimited` authored on lower-bound LEAP variables (the 1e12 export sentinel trap) |

Judgment-based rules (hypothesis discipline, cite-or-hedge, narrow scope, etc.) stay as prose — they can't be mechanically checked. Mechanical rules become tripwires.

## Architecture

```
Windows (LEAP installed, COM access)             Any OS (analysis side)
┌────────────────────────────────────────┐       ┌──────────────────────────────┐
│  THE FORGE / THE PROBE                 │  ──►  │  THE ORACLE                  │
│  (Python + pywin32 + LEAP COM)         │       │  NemoDB("scenario.sqlite")   │
│                                        │       │  LeapAreaContext.discover()  │
│  Author CSV → THE SCRIBE → canonical   │       │                              │
│        → THE GATE → THE FORGE → LEAP   │       │  THE WARDEN runs first:      │
│        ↓                               │       │  static infeasibility check  │
│  THE PROBE → results + units CSVs ────►│       │                              │
│        ↓                               │       │  THE SEER on failure:        │
│  THE HERALD broadcasts heartbeat       │       │  xN decode → forensics       │
└────────────────────────────────────────┘       │           → placeholders     │
                                                  │  THE DIVINER traces results  │
                                                  └──────────────────────────────┘
```

## Install

```bash
pip install nemo_read              # core (any OS, no LEAP)
pip install 'nemo_read[leap]'      # adds pywin32 for THE FORGE + THE PROBE (Windows)
```

## Quickstart — the three loops

```bash
# 1. ORACLE — read a calculated scenario (works anywhere, no LEAP)
python -c "
from nemo_read import NemoDB, get_result
db = NemoDB('NEMO_25.sqlite')
print(get_result(db, 'vtotalcapacityannual').head())
"

# 2. PROBE — harvest a full area in one COM session (Windows + LEAP open)
python my_probe.py --scenarios "BAS,ATS,RAS,CA" --expect-area "aeo9_v0.45"
# Writes results_<scenario>.csv per scenario, units.csv once, plus
# _progress_*.json updated every tick for at-rest monitoring.

# 3. FORGE — push authored data upstream into LEAP (Windows + LEAP open)
python inject/<domain>/inject_to_leap.py \
    --scenarios "BAS,ATS,RAS,CA" \
    --expect-area "aeo9_v0.45"
# Default flow: dry-run → confirm → real inject → readback verify,
# all in ONE warm COM session per scenario.
```

A new sector adds itself by writing a ~10-line `CanonicalInjector` subclass — see `inject/bioenergy/inject_to_leap.py` as the reference shape. The framework owns every LEAP-side concern; the subclass only declares scope.

## Status — v0.6.9

- **199 pytest tests passing** end-to-end (was 66 at v0.6.5)
- End-to-end validated against multiple AEO9 scenarios — `aeo9_v0.32`, `aeo9_v0.33_bak`, `aeo9_v0.36`, `aeo9_v0.38_yy`, and `aeo9_v0.42` RAS infeasibility resolution
- All thirteen capabilities re-exported at the top level (`from nemo_read import X`)
- Five CI tripwires now enforce every CLAUDE.md rule that has a mechanical violation criterion (see "The silent layer" above)
- Repository: https://github.com/yyuwonogit/nemo_read
- Wheel + sdist built (`dist/nemo_read-0.6.9-py3-none-any.whl`)

## Gotchas (real-session learnings — now mostly framework-handled)

- **Multi-area open** — setting `leap.ActiveScenario` over COM can jump to a different open area if it has a scenario with the same name. THE FORGE / THE PROBE auto-lock to ActiveArea at start and abort on drift. Best practice: keep only the target area open during a push.
- **`Variable.Expression` on result variables fires modal popups** — handled by THE PROBE's sealed `_read_unit_text` (BT={3,50} guard) and by never reading `.Expression` on result-side variables. If a dialog still appears, dismiss; the script logs `[OK]`.
- **`Interp(...)` separator** — must be comma list-separator + period decimal on this engine. THE SIGIL enforces; semicolon-form CSVs are refused by THE GATE's pre-flight scan before any COM write.
- **`Unlimited` on lower-bound LEAP variables** — converts to 1e12 in NEMO export and is a confirmed LP-infeasibility cause. `tests/test_claude_md_rules_enforced.py` scans every canonical CSV at CI time.
- **Long-running probes** — a probe that exceeds 60s MUST run in background with THE HERALD wired in. The framework does this automatically; the harness `Monitor` tool streams heartbeats as notifications.

## More

- **Cookbook**: `docs/cookbook.md` — 17 recipes, first-look inventory to demand-by-sector
- **Standardised flows**: `docs/FLOWS.md` — canonical step-by-step for inject / results-harvest / infeasibility triage
- **LEAP export reference**: `docs/leap_export.md`
- **Infeasibility methodology**: `docs/infeasibility_methodology.md` — full 11-stage walk-through
- **Unit conversions**: `docs/unit_conversions.md` — defensible factors with citations
- **Repository layout + routing**: `MAILBOX_ROUTING.md` — the inbox → inject/result routing ritual
- **Operator brief**: `CLAUDE.md` — full hard-rules + workflow contract for any agentic LLM working inside this repo
