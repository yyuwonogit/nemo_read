"""
Smoke test for the scaffolder.

Generates a package into a temp directory, verifies the file layout,
imports the generated code, and runs its own smoke tests via pytest.
"""
from __future__ import annotations

import subprocess
import sys
import sqlite3
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))                            # add scripts/

from nemo_read.scaffold import scaffold_package                  # noqa: E402


# Reuse the tiny DB builder from the main smoke test so we can point
# ``--reference-db`` at a real file.
from tests.test_nemo_read import _build_synthetic_db             # noqa: E402


def _expected_files(pkg_root: Path, pkg: str) -> list[Path]:
    src = pkg_root / "src" / pkg
    return [
        pkg_root / "pyproject.toml",
        pkg_root / "README.md",
        pkg_root / ".gitignore",
        src / "__init__.py",
        src / "registry.py",
        src / "loaders.py",
        src / "cache.py",
        src / "cli.py",
        src / "scenarios.toml",
        src / "dimensions.py",
        src / "nemo_read" / "__init__.py",
        src / "nemo_read" / "db.py",
        src / "nemo_read" / "schema.py",
        pkg_root / "tests" / "test_smoke.py",
        pkg_root / "notebooks" / "explore.py",
    ]


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        workspace = Path(tmp)                                   # sandbox
        ref_db = workspace / "ref.sqlite"                       # reference DB
        _build_synthetic_db(ref_db)                             # populate v11 DB

        pkg_root = workspace / "demo_pkg"                       # where to scaffold

        # Run scaffolder with a reference DB so dimensions.py is generated.
        scaffold_package(
            name="demo-pkg",
            dest=pkg_root,
            author="Test Author",
            scenarios={"REF": str(ref_db)},
            reference_db=ref_db,
            description="Test package scaffolded from smoke test.",
        )

        # File-layout assertions.
        for p in _expected_files(pkg_root, "demo_pkg"):
            assert p.exists(), f"missing: {p}"

        # Install the generated package and run its tests with pytest.
        # Use the current Python executable so we stay inside the same env.
        env_pkg = pkg_root                                      # work dir
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-e", ".",
             "--break-system-packages", "--quiet"],
            cwd=env_pkg,
        )
        # Run its smoke tests.
        subprocess.check_call(
            [sys.executable, "-m", "pytest", "-q", "--no-header"],
            cwd=env_pkg,
        )

        # Verify the generated CLI works end-to-end.
        out = subprocess.check_output(
            ["demo-pkg", "list"],
            env={"PATH": __import__("os").environ["PATH"]},
        )
        assert b"REF" in out, f"CLI did not list REF: {out!r}"

        # Verify dimension Literal types were emitted.
        dim_src = (pkg_root / "src" / "demo_pkg" / "dimensions.py").read_text()
        assert "Region = Literal[" in dim_src
        assert "'IDN'" in dim_src

        # Clean up the installed test package.
        subprocess.check_call(
            [sys.executable, "-m", "pip", "uninstall", "-y",
             "demo-pkg", "--break-system-packages", "--quiet"],
        )

        print("Scaffolder smoke test passed.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
