"""Tests for lexiflow_core.config.paths and platform_dirs."""

from __future__ import annotations

from pathlib import Path

import pytest
from lexiflow_core.config.paths import default_data_root, language_data_root
from lexiflow_core.config.platform_dirs import app_config_dir


def test_default_data_root_is_lexiflow_home(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("USERPROFILE", raising=False)

    assert default_data_root() == (tmp_path / "LexiFlow").resolve()


def test_app_config_dir_is_absolute() -> None:
    config_dir = app_config_dir()

    assert config_dir.is_absolute()


def test_app_config_dir_uses_app_data_name_on_linux(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr("lexiflow_core.config.platform_dirs.sys.platform", "linux")
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)

    assert app_config_dir() == (tmp_path / ".config" / "LexiFlow").resolve()


def test_language_data_root_returns_language_folder(tmp_path: Path) -> None:
    assert language_data_root(tmp_path, "de") == tmp_path / "de"


def test_queue_db_path_under_app_folder(tmp_path: Path) -> None:
    from lexiflow_core.config.paths import queue_db_path

    assert queue_db_path(tmp_path) == tmp_path / ".app" / "queue.sqlite"
