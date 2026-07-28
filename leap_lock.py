#!/usr/bin/env python
"""LEAP-lock toggle — the on/off switch for the COM interlock.

The lock is a single file (`.leap_lock`) at the repo root. While it exists,
`nemo_read.dispatch_leap()` refuses to attach to the LEAP COM server, so every
injector, prober, and exporter in the repo is gated by it (see
`nemo_read/_leap_com.py::assert_leap_access_allowed`).

Usage:
    python leap_lock.py status
    python leap_lock.py on   [--reason "..."]     # engage (default reason if omitted)
    python leap_lock.py off  --reason "..."       # release — REASON REQUIRED

The `off` command requires an explicit --reason so a release always leaves a
trace of who lifted it and why. `off` archives the note it removed to
`.leap_lock.released` rather than destroying it.

Programmatic guard for injects: `require_unlocked()` raises SystemExit(12) with
a clear message if the lock is engaged — call it at the top of an inject driver
so "ask for the lock to be lifted first" is enforced mechanically, not by memory.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from nemo_read._leap_com import LEAP_LOCK_FILENAME
except Exception:  # keep the toggle usable even if the package isn't importable
    LEAP_LOCK_FILENAME = ".leap_lock"

REPO = Path(__file__).resolve().parent
LOCK = REPO / LEAP_LOCK_FILENAME
ARCHIVE = REPO / (LEAP_LOCK_FILENAME + ".released")

_DEFAULT_NOTE = """LEAP IS IN USE — DO NOT ATTACH TO THE COM SERVER.

While this file exists, every LEAP COM path in this repo refuses to start
(nemo_read.dispatch_leap raises LeapAccessLocked; CanonicalInjector /
CanonicalProber / exports / probes are all covered by this one interlock).

Toggle with:  python leap_lock.py off --reason "..."
DELETE ONLY ON THE USER'S EXPLICIT SAY-SO. Ask first, every time.
An env var also engages it for a one-off shell: NEMO_READ_LEAP_LOCK=1
"""


def _stamp() -> str:
    return datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S %z")


def is_locked() -> bool:
    return LOCK.exists()


def require_unlocked(operation: str = "inject") -> None:
    """Abort (exit 12) if the lock is engaged. Call before any COM inject."""
    if is_locked():
        sys.stderr.write(
            f"[leap_lock] {operation} REFUSED — the LEAP lock is ENGAGED ({LOCK}).\n"
            f"            Ask the user to lift it, then: python leap_lock.py off --reason \"...\"\n"
        )
        raise SystemExit(12)


def cmd_status() -> int:
    if is_locked():
        print(f"LOCKED   {LOCK}")
        note = LOCK.read_text(encoding="utf-8").strip().splitlines()
        for ln in note[:3]:
            print(f"   | {ln}")
        return 0
    print(f"unlocked (no {LEAP_LOCK_FILENAME}) — LEAP COM access is ALLOWED")
    return 0


def cmd_on(reason: str | None) -> int:
    if is_locked():
        print(f"already LOCKED — {LOCK}")
        return 0
    body = _DEFAULT_NOTE
    if reason:
        body = f"{reason}\n\n{body}"
    body = f"# engaged {_stamp()}\n\n{body}"
    LOCK.write_text(body, encoding="utf-8")
    print(f"LOCKED   {LOCK}")
    return 0


def cmd_off(reason: str | None) -> int:
    if not reason:
        sys.stderr.write("[leap_lock] off REQUIRES --reason \"...\" (a release must be traceable)\n")
        return 2
    if not is_locked():
        print(f"already unlocked (no {LEAP_LOCK_FILENAME})")
        return 0
    prior = LOCK.read_text(encoding="utf-8")
    ARCHIVE.write_text(
        f"# released {_stamp()}\n# reason: {reason}\n\n--- prior lock note ---\n{prior}",
        encoding="utf-8",
    )
    LOCK.unlink()
    print(f"UNLOCKED — removed {LOCK}")
    print(f"   reason: {reason}")
    print(f"   prior note archived to {ARCHIVE.name}")
    return 0


def main(argv: list[str] | None = None) -> int:
    import argparse

    p = argparse.ArgumentParser(description="Toggle the LEAP COM interlock.")
    p.add_argument("action", choices=["status", "on", "off"])
    p.add_argument("--reason", default=None,
                   help="Why (required for off; stamped into the lock/archive).")
    a = p.parse_args(argv)
    return {"status": lambda: cmd_status(),
            "on": lambda: cmd_on(a.reason),
            "off": lambda: cmd_off(a.reason)}[a.action]()


if __name__ == "__main__":
    raise SystemExit(main())
