"""Shared pytest hooks."""

from __future__ import annotations

import os
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]


def _vendored_vec0_loadable() -> Path | None:
    package_dir = _REPO_ROOT / "packaging" / "vendor" / "sqlite_vec" / "sqlite_vec"
    for name in ("vec0.dylib", "vec0.so", "vec0.dll", "vec0.arm64.dll"):
        candidate = package_dir / name
        if candidate.exists():
            return candidate
    return None


# Use fetched vec0 binaries when present (CI and local dev after fetch_sqlite_vec.py).
if not os.environ.get("LEXIFLOW_SQLITE_VEC_PATH", "").strip():
    _vec0 = _vendored_vec0_loadable()
    if _vec0 is not None:
        os.environ["LEXIFLOW_SQLITE_VEC_PATH"] = str(_vec0)

# Headless Qt for UI tests avoids macOS "Python quit unexpectedly" dialogs from
# native window teardown. Set LEXIFLOW_QT_HEADED=1 to run UI tests with real windows.
if os.environ.get("LEXIFLOW_QT_HEADED") != "1":
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import subprocess
import sys

import pytest
from _pytest.config import Config
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

PACKAGE_COVERAGE_FLOORS: list[tuple[str, int]] = [
    ("*/lexiflow_core/*", 80),
    ("*/lexiflow_ui/*", 60),
]


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session: Config, exitstatus: int) -> None:
    app = QApplication.instance()
    if app is not None:
        for timer in app.findChildren(QTimer):
            timer.stop()
        app.processEvents()

    if exitstatus != pytest.ExitCode.OK:
        return
    if session.config.pluginmanager.get_plugin("_cov") is None:
        return

    for include_pattern, floor in PACKAGE_COVERAGE_FLOORS:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "coverage",
                "report",
                f"--include={include_pattern}",
                f"--fail-under={floor}",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            sys.stderr.write(result.stdout)
            sys.stderr.write(result.stderr)
            session.exitstatus = pytest.ExitCode.TESTS_FAILED
