"""Tail the inject progress JSON every N seconds.

Usage:
    python inject/transport/_watch_progress.py [--interval 30] [--out _watch.log]

Reads the newest _progress_inject_transport_*.json in this dir,
prints a one-line status, appends to log, and sleeps. Exits when
the JSON's `finished` field becomes non-null.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path


HERE = Path(__file__).parent


def fmt(d: dict) -> str:
    c = d.get("current", {})
    return (
        f"[{datetime.now().strftime('%H:%M:%S')}] "
        f"stage={c.get('stage','?')} | "
        f"scen={c.get('scenario','?')} {c.get('scenario_idx','?')} | "
        f"region={c.get('region','?')} {c.get('region_idx','?')} | "
        f"row={c.get('row_in_region','?')}/{c.get('rows_in_region','?')} | "
        f"rows_written={d.get('rows_total',0)} | "
        f"last_hb={d.get('last_heartbeat','?')} | "
        f"finished={d.get('finished')}"
    )


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--interval", type=float, default=30.0)
    p.add_argument("--out", type=Path, default=HERE / "_watch.log")
    args = p.parse_args()

    print(f"[watcher] writing to {args.out}, interval={args.interval}s",
          flush=True)
    while True:
        candidates = sorted(HERE.glob("_progress_inject_transport_*.json"))
        if not candidates:
            line = f"[{datetime.now():%H:%M:%S}] no progress JSON yet"
        else:
            try:
                d = json.loads(candidates[-1].read_text(encoding="utf-8"))
                line = fmt(d)
            except Exception as exc:
                line = f"[{datetime.now():%H:%M:%S}] read err: {exc}"

        print(line, flush=True)
        with args.out.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

        if candidates:
            try:
                d = json.loads(candidates[-1].read_text(encoding="utf-8"))
                if d.get("finished"):
                    print("[watcher] finished detected; exiting.", flush=True)
                    return 0
            except Exception:
                pass

        time.sleep(args.interval)


if __name__ == "__main__":
    sys.exit(main())
