"""Tests for the unified LexiFlow launcher entrypoint."""

from __future__ import annotations

from pathlib import Path

import lexiflow_core
import pytest
from lexiflow_ui import launcher


def test_launcher_version_prints_core_version(capsys) -> None:
    exit_code = launcher.main(["--version"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.strip() == lexiflow_core.__version__
    assert captured.err == ""


def test_launcher_sqlite_vec_smoke_prints_version(capsys) -> None:
    import sqlite_vec

    package_dir = Path(sqlite_vec.loadable_path()).parent
    has_loadable = any(
        (package_dir / name).is_file()
        for name in ("vec0.dylib", "vec0.so", "vec0.dll", "vec0.arm64.dll")
    )
    if not has_loadable:
        pytest.skip("installed sqlite-vec loadable not present")

    exit_code = launcher.main(["--sqlite-vec-smoke"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.strip()
    assert captured.err == ""
