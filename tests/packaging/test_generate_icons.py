"""Tests for placeholder icon generation."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

pytest.importorskip("PIL")


def _load_generate_icons():
    script = (
        Path(__file__).resolve().parents[2]
        / "packaging"
        / "scripts"
        / "generate_icons.py"
    )
    spec = importlib.util.spec_from_file_location("lexiflow_generate_icons", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_generate_icons_writes_assets(tmp_path: Path, monkeypatch) -> None:
    icons = _load_generate_icons()
    monkeypatch.setattr(icons, "_repo_assets", lambda: tmp_path)

    icons.generate_icons()

    for name in ("icon.png", "icon.ico", "icon.icns"):
        path = tmp_path / name
        assert path.is_file()
        assert path.stat().st_size > 512
