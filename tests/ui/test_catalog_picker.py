"""Tests for searchable language catalog picker."""

from __future__ import annotations

from lexiflow_ui.widgets.catalog_picker import CatalogPickerWidget


def test_catalog_picker_filters_by_language_name(qtbot) -> None:
    picker = CatalogPickerWidget()
    qtbot.addWidget(picker)

    picker.set_filter_text("span")

    assert picker.visible_isos() == ["es"]


def test_catalog_picker_filters_by_iso_code(qtbot) -> None:
    picker = CatalogPickerWidget()
    qtbot.addWidget(picker)

    picker.set_filter_text("uk")

    assert picker.visible_isos() == ["uk"]


def test_catalog_picker_clear_filter_shows_all_languages(qtbot) -> None:
    picker = CatalogPickerWidget()
    qtbot.addWidget(picker)
    total = len(picker.visible_isos())

    picker.set_filter_text("span")
    picker.set_filter_text("")

    assert len(picker.visible_isos()) == total
