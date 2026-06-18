"""Shared pytest hooks."""

from __future__ import annotations

import os

# Headless Qt for UI tests avoids macOS "Python quit unexpectedly" dialogs from
# native window teardown. Set LEXIFLOW_QT_HEADED=1 to run UI tests with real windows.
if os.environ.get("LEXIFLOW_QT_HEADED") != "1":
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import subprocess
import sys

import PySide6
import pytest
from _pytest.config import Config
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

if not hasattr(PySide6, "__version__"):
    from importlib.metadata import PackageNotFoundError, version

    try:
        PySide6.__version__ = version("pyside6-essentials")
    except PackageNotFoundError:
        PySide6.__version__ = "0.0.0"

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
