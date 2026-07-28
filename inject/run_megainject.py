#!/usr/bin/env python
"""Single-session mega-inject driver (§A.10).

The problem this solves: running each sector injector as its own
`python inject_to_leap.py` invocation opens a *new* COM connection to LEAP
each time, and LEAP intermittently hands back a blank `ActiveArea` on a fresh
attach (§11.1). Six invocations = six attaches = six chances to hit the blank.

This driver dispatches LEAP **once** and runs every remaining payload against
that single held connection — one process, one session, zero disconnects
between payloads, so `ActiveArea` binds once and stays bound.

Mechanism: monkeypatch `nemo_read.inject_base.dispatch_leap` to return the one
shared handle, then call each sector injector's normal `.run(argv=...)`. Each
run still does its own area-lock, scenario loop, and readback — the gate
between payloads is preserved (a non-zero rc stops the sequence).

Usage:
    python inject/run_megainject.py --expect-area "aeo9_v0.81"
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import nemo_read.inject_base as ib
from nemo_read._leap_com import dispatch_leap as _real_dispatch, LeapAccessLocked

# (module_path, class_name, csv, scenarios) — payloads 3..6, in order.
# 1 & 2 (transport hist + audit) are already committed & verified EXACT.
FOUR = "Current Accounts,Baseline Simulation,AMS Target Scenario,Regional Aspiration Scenario"
PAYLOADS = [
    ("inject/transport/inject_to_leap.py",  "TransportInjector",
     "inject/transport/20260723/transport_delta_20260723.csv", FOUR),
    ("inject/commercial/inject_to_leap.py", "CommercialInjector",
     "inject/commercial/20260722/commercial_canonical_20260722.csv", FOUR),
    ("inject/bioenergy/inject_to_leap.py",  "BioenergyInjector",
     "inject/bioenergy/20260722b/bioenergy_delta_20260722b.csv", FOUR),
    ("inject/power/run_workflow.py",        "PowerInjector",
     "inject/power/20260722/batch2_ccs_retarget_20260722.csv", "Regional Aspiration Scenario"),
]


def _load_class(rel_path: str, cls_name: str):
    path = REPO / rel_path
    spec = importlib.util.spec_from_file_location(f"_mega_{cls_name}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, cls_name)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Single-session mega-inject driver.")
    p.add_argument("--expect-area", required=True,
                   help="Live LEAP area name; every payload is locked to it.")
    p.add_argument("--from", dest="from_", type=int, default=3,
                   help="Payload number to start at (3-6). Earlier ones already committed.")
    a = p.parse_args(argv)
    area = a.expect_area

    # ---- ONE dispatch for the whole run ----
    print(f"[mega] dispatching LEAP once (shared session) for area {area!r}")
    try:
        shared = _real_dispatch()
    except LeapAccessLocked as exc:
        print(f"[mega] {exc}", file=sys.stderr)
        return 12

    # ---- bind the area once ----
    name = shared.ActiveArea.Name
    if not name:
        print(f"[mega] ActiveArea blank on attach (§11.1); attempting to activate {area!r}")
        try:
            shared.ActiveArea = shared.Areas(area)
            name = shared.ActiveArea.Name
            print(f"[mega] after activate: ActiveArea={name!r}")
        except Exception as exc:  # noqa: BLE001 — best-effort; guard below is the safety net
            print(f"[mega] could not auto-activate ({exc!r})")
    if name != area:
        print(f"[mega] ABORT: ActiveArea is {name!r}, expected {area!r}. "
              f"Click into the {area} area in LEAP (make it the active area), "
              f"then re-run this driver. Nothing was written.", file=sys.stderr)
        return 3
    print(f"[mega] area bound: {name!r} — holding this ONE session for all payloads\n")

    # ---- every injector's dispatch now returns the shared handle ----
    ib.dispatch_leap = lambda: shared

    results = []
    for i, (mod_path, cls_name, csv, scenarios) in enumerate(PAYLOADS, start=3):
        if i < a.from_:
            print(f"[mega] PAYLOAD {i}/6 — {cls_name}: SKIPPED (--from {a.from_}, already committed)")
            continue
        print(f"\n{'='*70}\n[mega] PAYLOAD {i}/6 — {cls_name}  ({Path(csv).name})\n{'='*70}")
        Injector = _load_class(mod_path, cls_name)
        argv_i = [
            "--csv", str(REPO / csv),
            "--scenarios", scenarios,
            "--expect-area", area,
            "--exclude-timor-leste", "--fail-fast", "--skip-dry-run", "-y",
        ]
        rc = Injector().run(argv=argv_i)
        results.append((i, cls_name, rc))
        if rc != 0:
            print(f"\n[mega] PAYLOAD {i} ({cls_name}) returned rc={rc} — STOPPING. "
                  f"Remaining payloads NOT run.", file=sys.stderr)
            break

    print(f"\n{'='*70}\n[mega] SEQUENCE SUMMARY\n{'='*70}")
    for i, cls_name, rc in results:
        print(f"  payload {i}  {cls_name:20} rc={rc}  {'OK' if rc == 0 else 'FAILED — STOP'}")
    done = [r for r in results if r[2] == 0]
    attempted = [r for r in results]
    print(f"[mega] {len(done)}/{len(attempted)} attempted payloads clean this run "
          f"(payloads before --from {a.from_} already committed earlier).")
    return 0 if attempted and len(done) == len(attempted) else 1


if __name__ == "__main__":
    raise SystemExit(main())
