"""Tests for lexiflow_core.languages.catalog."""

from __future__ import annotations

import pytest
from lexiflow_core.languages.catalog import get_language, list_languages
from lexiflow_core.languages.models import LanguageInfo


def test_get_language_uk_returns_info() -> None:
    info = get_language("uk")

    assert info == LanguageInfo(iso="uk", name="Ukrainian", flag="🇺🇦")


def test_list_languages_excludes_russian() -> None:
    isos = {lang.iso for lang in list_languages()}

    assert "uk" in isos
    assert "ru" not in isos


def test_get_language_unknown_raises() -> None:
    with pytest.raises(KeyError, match="ru"):
        get_language("ru")
