"""Tests for worker spawn argv in dev and frozen bundles."""

from __future__ import annotations

import sys
from pathlib import Path

from lexiflow_ui.worker_command import build_worker_command


def test_build_worker_command_uses_module_in_dev(tmp_path: Path) -> None:
    command = build_worker_command("/usr/bin/python3", tmp_path)

    assert command == [
        "/usr/bin/python3",
        "-m",
        "lexiflow_worker",
        "--data-root",
        str(tmp_path),
    ]


def test_build_worker_command_uses_worker_flag_when_frozen(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(sys, "frozen", True, raising=False)

    command = build_worker_command("/opt/LexiFlow/LexiFlow", tmp_path)

    assert command == [
        "/opt/LexiFlow/LexiFlow",
        "--worker",
        "--data-root",
        str(tmp_path),
    ]
