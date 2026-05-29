"""Shared pytest hooks."""

from __future__ import annotations

import subprocess
import sys

import pytest
from _pytest.config import Config

PACKAGE_COVERAGE_FLOORS: list[tuple[str, int]] = [
    ("*/lexiflow_core/*", 80),
    ("*/lexiflow_ui/*", 60),
]


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session: Config, exitstatus: int) -> None:
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
