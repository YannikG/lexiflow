"""Tests for the unified LexiFlow launcher entrypoint."""

from __future__ import annotations

import lexiflow_core
import pytest
from lexiflow_ui import launcher
from tests.packaging.sqlite_vec_test_support import (
    resolve_installed_sqlite_vec_loadable,
)


def test_launcher_version_prints_core_version(capsys) -> None:
    exit_code = launcher.main(["--version"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.strip() == lexiflow_core.__version__
    assert captured.err == ""


def test_launcher_sqlite_vec_smoke_prints_version(capsys) -> None:
    if resolve_installed_sqlite_vec_loadable() is None:
        pytest.skip("installed sqlite-vec loadable not present")

    exit_code = launcher.main(["--sqlite-vec-smoke"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.strip()
    assert captured.err == ""
