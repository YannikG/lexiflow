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


def test_launcher_worker_delegates_to_worker_main(monkeypatch) -> None:
    calls: list[list[str] | None] = []

    def fake_worker_main(argv: list[str] | None = None) -> int:
        calls.append(argv)
        return 0

    monkeypatch.setattr(launcher, "_worker_main", fake_worker_main)

    exit_code = launcher.main(["--worker", "--data-root", "/tmp/lf"])

    assert exit_code == 0
    assert calls == [["--data-root", "/tmp/lf"]]


def test_launcher_default_delegates_to_ui_run(monkeypatch) -> None:
    calls: list[list[str] | None] = []

    def fake_ui_run(argv: list[str] | None = None) -> int:
        calls.append(argv)
        return 0

    monkeypatch.setattr(launcher, "_ui_run", fake_ui_run)

    exit_code = launcher.main(["--some-ui-flag"])

    assert exit_code == 0
    assert calls == [["--some-ui-flag"]]
