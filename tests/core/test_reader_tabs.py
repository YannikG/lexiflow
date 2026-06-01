"""Tests for simplified variant level parsing."""

from __future__ import annotations

from lexiflow_core.languages.models import CEFRLevel
from lexiflow_core.library.reader_tabs import level_from_simplified_variant


def test_level_from_simplified_variant_parses_stem() -> None:
    assert level_from_simplified_variant("simplified-a2") == CEFRLevel.A2


def test_level_from_simplified_variant_returns_none_for_other_tabs() -> None:
    assert level_from_simplified_variant("translated") is None
