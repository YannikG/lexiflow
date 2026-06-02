"""Tests for lexiflow_core.languages.store."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from lexiflow_core.config.paths import language_json_path
from lexiflow_core.languages.store import LanguageStore, LanguageStoreError


def test_add_target_writes_minimal_language_json(tmp_path: Path) -> None:
    store = LanguageStore(tmp_path)

    store.add_target("es")

    path = language_json_path(tmp_path, "es")
    assert path.is_file()
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload == {"version": 1}
    assert store.list_targets() == ["es"]
    assert store.has_target("es")


def test_add_target_rejects_unknown_language(tmp_path: Path) -> None:
    store = LanguageStore(tmp_path)

    with pytest.raises(LanguageStoreError, match="unknown language"):
        store.add_target("ru")


def test_add_target_rejects_duplicate(tmp_path: Path) -> None:
    store = LanguageStore(tmp_path)
    store.add_target("es")

    with pytest.raises(LanguageStoreError, match="already exists"):
        store.add_target("es")


def test_list_targets_ignores_legacy_user_level_metadata(tmp_path: Path) -> None:
    store = LanguageStore(tmp_path)
    lang_dir = tmp_path / "es"
    lang_dir.mkdir()
    path = language_json_path(tmp_path, "es")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('{"user_level": "B1"}\n', encoding="utf-8")

    assert store.list_targets() == ["es"]
