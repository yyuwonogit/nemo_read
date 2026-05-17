"""Background-process heartbeat + progress-file convention.

Every long-running LEAP COM operation (inject, probe, anything > 60s)
SHOULD report progress via this utility. The convention has two
parallel channels:

1. **Heartbeat stdout** — structured line printed every `interval`
   seconds. Format:
       [HB t=HH:MM:SS scenario=X region=Y rows=N elapsed=Mm:Ss]
   Used to stream progress to a foreground monitor (the harness
   `Monitor` tool streams stdout lines as notifications). Always
   line-buffered + flushed so background runs surface progress in
   real time.

2. **Progress JSON file** — `_progress_<op>_<ts>.json` written
   alongside the heartbeat. Contains structured state the user (or
   another script) can read on demand:
       {
         "op": "probe_full",
         "started": "2026-05-17T14:32:01",
         "current": {"scenario": "BAS", "region": "Indonesia", "rows_written": 4523},
         "rows_total": 4523,
         "last_heartbeat": "14:54:27"
       }
   On `finish()`: adds "finished", "elapsed_seconds", "summary"
   keys.

The two channels are redundant by design — stdout for real-time
streaming, JSON for at-rest inspection. CSV row count
(`wc -l <output.csv>`) remains the most reliable progress signal
when in doubt (per RESULTS_HARVEST_SOP.md pitfall #8).
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any


def _fmt_elapsed(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    if m >= 60:
        h, m = divmod(m, 60)
        return f"{h}h{m:02d}m{s:02d}s"
    return f"{m}m{s:02d}s"


class HeartbeatLogger:
    """Heartbeat + progress JSON logger for long-running LEAP COM ops.

    Construct once at the top of a long-running operation. Call
    `tick(**context)` whenever progress changes (every region, every
    N rows, etc.) — the logger throttles actual stdout/disk writes to
    `interval` seconds. Call `finish(summary)` when done.
    """

    def __init__(
        self,
        op_name: str,
        progress_dir: Path | str | None = None,
        interval_seconds: float = 30.0,
    ):
        self.op_name = op_name
        self.interval = interval_seconds
        self.start_time = time.time()
        self.last_heartbeat = 0.0

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        progress_dir = Path(progress_dir) if progress_dir else Path.cwd()
        progress_dir.mkdir(parents=True, exist_ok=True)
        self.progress_path = progress_dir / f"_progress_{op_name}_{ts}.json"

        self.state: dict[str, Any] = {
            "op": op_name,
            "started": datetime.now().isoformat(timespec="seconds"),
            "progress_file": str(self.progress_path),
            "current": {},
            "rows_total": 0,
            "last_heartbeat": None,
            "finished": None,
        }
        # Ensure line buffering so progress reaches stdout in background runs
        try:
            sys.stdout.reconfigure(line_buffering=True)  # type: ignore[attr-defined]
        except Exception:
            pass
        os.environ.setdefault("PYTHONUNBUFFERED", "1")

        # Write initial state so the progress file exists immediately
        self._write_progress()
        self._announce(f"[HB-START op={op_name} progress={self.progress_path}]")

    def tick(self, **context) -> None:
        """Update state with the given context kwargs.

        Common keys: scenario, region, rows_written, branches_done,
        total_branches. Anything passed is merged into self.state["current"].

        Stdout heartbeat is emitted only if `interval` seconds have
        passed since the last one (throttled). JSON file is written
        every tick (cheap).
        """
        now = time.time()
        self.state["current"].update(context)
        if "rows_written" in context:
            self.state["rows_total"] = max(
                self.state["rows_total"], int(context["rows_written"])
            )
        self._write_progress()
        if now - self.last_heartbeat >= self.interval:
            self._emit_heartbeat(now)
            self.last_heartbeat = now

    def force_heartbeat(self) -> None:
        """Emit a heartbeat now, regardless of interval throttling."""
        self._emit_heartbeat(time.time())
        self.last_heartbeat = time.time()

    def finish(self, summary: dict[str, Any] | None = None) -> None:
        """Mark the operation as complete. Writes a final progress JSON
        with finished + elapsed + summary fields, and prints a DONE line."""
        elapsed = time.time() - self.start_time
        self.state["finished"] = datetime.now().isoformat(timespec="seconds")
        self.state["elapsed_seconds"] = round(elapsed, 1)
        self.state["elapsed_human"] = _fmt_elapsed(elapsed)
        if summary:
            self.state["summary"] = summary
        self._write_progress()
        self._announce(
            f"[HB-DONE op={self.op_name} "
            f"elapsed={_fmt_elapsed(elapsed)} "
            f"rows={self.state['rows_total']} "
            f"progress={self.progress_path}]"
        )

    # ----- internals -----

    def _emit_heartbeat(self, now: float) -> None:
        elapsed = now - self.start_time
        ts = datetime.now().strftime("%H:%M:%S")
        ctx_str = " ".join(f"{k}={v}" for k, v in self.state["current"].items())
        line = f"[HB t={ts} {ctx_str} elapsed={_fmt_elapsed(elapsed)}]"
        self.state["last_heartbeat"] = ts
        self._announce(line)

    def _announce(self, line: str) -> None:
        print(line, flush=True)

    def _write_progress(self) -> None:
        try:
            with self.progress_path.open("w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=2)
        except OSError:
            # Progress file is best-effort; don't crash the long op
            # because we couldn't write a state file.
            pass


def read_progress(progress_path: Path | str) -> dict[str, Any] | None:
    """Read a progress JSON file. Returns None if the file is missing
    or malformed. Useful for on-demand status checks from a separate
    process."""
    try:
        with Path(progress_path).open("r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None
