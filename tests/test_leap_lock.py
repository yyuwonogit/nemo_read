"""Tripwire for the LEAP access interlock (CLAUDE.md §A.24).

The user works in the LEAP UI while agents run offline analysis in this repo.
A stray COM dispatch attaches to the *same* LEAP instance and can disrupt or
corrupt that session. The interlock is a lock file (``.leap_lock`` at the repo
root) or ``$NEMO_READ_LEAP_LOCK``; while it is present every COM entry point
must refuse to start.

These tests pin two things:
  1. the guard itself behaves (env var, lock file, parent-directory walk);
  2. *every* site in the repo that dispatches ``LEAP.LEAPApplication`` is
     guarded — so a new script cannot silently bypass the interlock.
"""
from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path

import pytest

import nemo_read
from nemo_read._leap_com import (
    LEAP_LOCK_ENV,
    LEAP_LOCK_FILENAME,
    LeapAccessLocked,
    assert_leap_access_allowed,
    find_leap_lock,
)

REPO = Path(__file__).resolve().parent.parent
DISPATCH_TARGET = "LEAP.LEAPApplication"
SKIP_DIRS = {".git", ".venv", "__pycache__", "node_modules", "build", "dist"}


@pytest.fixture
def no_lock(monkeypatch, tmp_path):
    """Neutralise the real repo lock so guard behaviour can be tested."""
    monkeypatch.delenv(LEAP_LOCK_ENV, raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "nemo_read._leap_com.find_leap_lock", lambda start=None: None, raising=True
    )
    return tmp_path


# --------------------------------------------------------------- guard logic


def test_env_var_truthy_locks(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    for val in ("1", "true", "YES", "on"):
        monkeypatch.setenv(LEAP_LOCK_ENV, val)
        assert find_leap_lock(tmp_path) is not None, val


def test_env_var_empty_does_not_lock(monkeypatch, tmp_path):
    """An empty env var must not itself lock.

    Asserted via the sentinel rather than ``is None``: the repo's own
    ``.leap_lock`` is discovered from the package root regardless of CWD
    (deliberate — see test_lock_found_from_package_root_regardless_of_cwd),
    so None is not available while the real lock is in place.
    """
    monkeypatch.setenv(LEAP_LOCK_ENV, "")
    monkeypatch.chdir(tmp_path)
    found = find_leap_lock(tmp_path)
    assert found != Path(LEAP_LOCK_ENV), "empty env var must not act as a lock"
    if found is not None:
        assert found.name == LEAP_LOCK_FILENAME and found.exists()


def test_lock_found_from_package_root_regardless_of_cwd(monkeypatch, tmp_path):
    """The repo lock protects even a script run from an unrelated directory."""
    monkeypatch.delenv(LEAP_LOCK_ENV, raising=False)
    monkeypatch.chdir(tmp_path)
    if not (REPO / LEAP_LOCK_FILENAME).exists():
        pytest.skip("repo .leap_lock released — nothing to assert")
    assert find_leap_lock(tmp_path) == REPO / LEAP_LOCK_FILENAME


def test_lock_file_in_parent_directory_is_found(monkeypatch, tmp_path):
    monkeypatch.delenv(LEAP_LOCK_ENV, raising=False)
    (tmp_path / LEAP_LOCK_FILENAME).write_text("in use", encoding="utf-8")
    deep = tmp_path / "a" / "b" / "c"
    deep.mkdir(parents=True)
    assert find_leap_lock(deep) == tmp_path / LEAP_LOCK_FILENAME


def test_assert_raises_when_locked(monkeypatch, tmp_path):
    monkeypatch.setenv(LEAP_LOCK_ENV, "1")
    monkeypatch.chdir(tmp_path)
    with pytest.raises(LeapAccessLocked) as exc:
        assert_leap_access_allowed("unit test")
    assert "BLOCKED" in str(exc.value)


def test_assert_passes_when_unlocked(no_lock):
    assert_leap_access_allowed("unit test") is None


def test_dispatch_leap_refuses_while_locked(monkeypatch, tmp_path):
    """The whole point: dispatch must die before touching win32com."""
    monkeypatch.setenv(LEAP_LOCK_ENV, "1")
    monkeypatch.chdir(tmp_path)
    with pytest.raises(LeapAccessLocked):
        nemo_read.dispatch_leap() if hasattr(nemo_read, "dispatch_leap") else None
        from nemo_read._leap_com import dispatch_leap
        dispatch_leap()


def test_guard_runs_before_pywin32_check(monkeypatch, tmp_path):
    """Lock beats the 'pywin32 missing' error — so it works on any platform."""
    monkeypatch.setenv(LEAP_LOCK_ENV, "1")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("nemo_read._leap_com._HAS_PYWIN32", False, raising=False)
    from nemo_read._leap_com import dispatch_leap
    with pytest.raises(LeapAccessLocked):
        dispatch_leap()


def test_public_api_exports_the_guard():
    for name in ("LeapAccessLocked", "find_leap_lock", "assert_leap_access_allowed"):
        assert name in nemo_read.__all__, f"{name} missing from nemo_read.__all__"
        assert hasattr(nemo_read, name)


# ------------------------------------------------------- repo-wide coverage


def _dispatch_sites() -> list[Path]:
    hits = []
    for p in REPO.rglob("*.py"):
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if DISPATCH_TARGET in text and "test_leap_lock" not in p.name:
            hits.append(p)
    return sorted(hits)


def test_every_dispatch_site_is_guarded():
    """Any file dispatching LEAP COM must consult the interlock.

    Either it routes through nemo_read's chokepoint, or it carries an inlined
    check that reads .leap_lock / $NEMO_READ_LEAP_LOCK.
    """
    unguarded = []
    for p in _dispatch_sites():
        text = p.read_text(encoding="utf-8", errors="replace")
        guarded = (
            "assert_leap_access_allowed" in text
            or "_assert_leap_unlocked" in text
            or LEAP_LOCK_FILENAME in text
        )
        if not guarded:
            unguarded.append(str(p.relative_to(REPO)))
    assert not unguarded, (
        "These files dispatch LEAP COM without consulting the lock:\n  "
        + "\n  ".join(unguarded)
        + "\nAdd assert_leap_access_allowed() (or the inlined _assert_leap_unlocked)"
        " before the Dispatch call."
    )


def test_guard_is_called_before_dispatch_in_package():
    """AST check: dispatch_leap()'s first statement is the interlock."""
    src = (REPO / "nemo_read" / "_leap_com.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    fn = next(
        n for n in tree.body
        if isinstance(n, ast.FunctionDef) and n.name == "dispatch_leap"
    )
    body = [s for s in fn.body if not isinstance(s, ast.Expr) or
            not isinstance(getattr(s, "value", None), ast.Constant)]
    first = body[0]
    assert isinstance(first, ast.Expr) and isinstance(first.value, ast.Call), (
        "dispatch_leap() must call the interlock first"
    )
    assert getattr(first.value.func, "id", None) == "assert_leap_access_allowed"


def test_injector_returns_12_when_locked(monkeypatch, tmp_path):
    """CanonicalInjector reports a locked LEAP as exit 12, not a traceback."""
    import csv as _csv
    from nemo_read.inject_base import CanonicalInjector

    monkeypatch.setenv(LEAP_LOCK_ENV, "1")

    class Probe(CanonicalInjector):
        SECTOR_NAME = "lock_test"
        DEFAULT_CSV = tmp_path / "main.csv"
        TIMOR_LESTE_SUPPLEMENT_NOT_APPLICABLE = True

    p = tmp_path / "main.csv"
    with p.open("w", encoding="utf-8", newline="") as f:
        w = _csv.writer(f)
        w.writerow(["ams", "branch", "variable", "expression"])
        w.writerow(["Brunei", "X", "Y", "Interp(2025, 1.0)"])

    assert Probe().run(argv=[]) == 12


def test_offline_gates_still_win_over_the_lock(monkeypatch, tmp_path):
    """The lock sits after the free offline gates, so §A.18 keeps exit 8.

    Ordering matters: an operator running a mis-specified inject while LEAP is
    locked should still be told what is wrong with their arguments.
    """
    import csv as _csv
    from nemo_read.inject_base import CanonicalInjector

    monkeypatch.setenv(LEAP_LOCK_ENV, "1")

    class Probe(CanonicalInjector):
        SECTOR_NAME = "order_test"
        DEFAULT_CSV = tmp_path / "main.csv"

    p = tmp_path / "main.csv"
    with p.open("w", encoding="utf-8", newline="") as f:
        w = _csv.writer(f)
        w.writerow(["ams", "branch", "variable", "expression"])
        w.writerow(["Brunei", "X", "Y", "Interp(2025, 1.0)"])
    (tmp_path / "timor_leste_supplement.csv").write_text(
        "ams,branch,variable,expression\n", encoding="utf-8"
    )

    # No --include/--exclude-timor-leste => §A.18 gate, exit 8, not 12.
    assert Probe().run(argv=[]) == 8


def test_repo_lock_currently_blocks(tmp_path):
    """End-to-end: with the repo's real .leap_lock present, dispatch refuses.

    Skips if the lock has been (deliberately) released.
    """
    if not (REPO / LEAP_LOCK_FILENAME).exists():
        pytest.skip("repo .leap_lock released — nothing to assert")
    env = dict(os.environ)
    env.pop(LEAP_LOCK_ENV, None)
    code = (
        "from nemo_read._leap_com import dispatch_leap, LeapAccessLocked\n"
        "try:\n"
        "    dispatch_leap()\n"
        "except LeapAccessLocked:\n"
        "    print('BLOCKED')\n"
    )
    out = subprocess.run(
        [sys.executable, "-c", code], cwd=REPO, env=env,
        capture_output=True, text=True, timeout=120,
    )
    assert "BLOCKED" in out.stdout, f"lock did not block: {out.stdout!r} {out.stderr!r}"
