"""Tests for the unified LexiFlow launcher entrypoint."""

from __future__ import annotations

import lexiflow_core
from lexiflow_ui import launcher


def test_launcher_version_prints_core_version(capsys) -> None:
    exit_code = launcher.main(["--version"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.strip() == lexiflow_core.__version__
    assert captured.err == ""
