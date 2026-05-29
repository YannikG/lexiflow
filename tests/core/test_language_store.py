"""Tests for lexiflow_core.languages.store."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from lexiflow_core.config.paths import language_json_path
from lexiflow_core.languages.models import CEFRLevel
from lexiflow_core.languages.store import LanguageStore, LanguageStoreError


def test_add_target_writes_language_json(tmp_path: Path) -> None:
    store = LanguageStore(tmp_path)

    store.add_target("es", CEFRLevel.A2)

    path = language_json_path(tmp_path, "es")
    assert path.is_file()
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["user_level"] == "A2"
    assert store.get_user_level("es") == CEFRLevel.A2
    assert store.list_targets() == ["es"]


def test_add_target_rejects_unknown_language(tmp_path: Path) -> None:
    store = LanguageStore(tmp_path)

    with pytest.raises(LanguageStoreError, match="unknown language"):
        store.add_target("ru", CEFRLevel.A1)


def test_add_target_rejects_duplicate(tmp_path: Path) -> None:
    store = LanguageStore(tmp_path)
    store.add_target("es", CEFRLevel.A2)

    with pytest.raises(LanguageStoreError, match="already exists"):
        store.add_target("es", CEFRLevel.B1)
