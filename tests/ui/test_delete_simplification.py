"""Tests for deleting simplified variants from the reader."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from lexiflow_core.config.paths import variant_path
from lexiflow_core.languages.models import CEFRLevel
from lexiflow_core.library.index import LibraryIndex
from lexiflow_core.library.reader_tabs import TRANSLATED_TAB, simplified_variant_name

from tests.ui.reader_test_helpers import reader_with_text
from tests.ui.test_reader import _seed_reader_text


def test_delete_simplification_enabled_on_simplified_tab(qtbot, tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    repo = _seed_reader_text(data_root)
    record = repo.get_text(LibraryIndex(data_root).list_by_lang("es")[0].id)
    variant = simplified_variant_name(CEFRLevel.A2)
    repo.apply_simplified_variant(
        record.id,
        level="a2",
        markdown="# Simple\n\nCuerpo simple.",
    )
    reader = reader_with_text(qtbot, data_root, tab=variant)
    reader._record = repo.get_text(record.id)
    reader._repo = repo
    reader._refresh_simplified_variants()
    reader._configure_simplified_tabs()
    reader.select_tab(variant)

    assert not reader._delete_simplification_button.isHidden()
    assert reader._delete_simplification_button.isEnabled()
    assert reader._retranslate_button.isHidden()
    assert not reader._resimplify_button.isHidden()


def test_delete_simplification_runs_removal(qtbot, tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    repo = _seed_reader_text(data_root)
    record = repo.get_text(LibraryIndex(data_root).list_by_lang("es")[0].id)
    variant = simplified_variant_name(CEFRLevel.A2)
    repo.apply_simplified_variant(
        record.id,
        level="a2",
        markdown="# Simple\n\nCuerpo simple.",
    )
    reader = reader_with_text(qtbot, data_root, tab=variant)
    reader._record = repo.get_text(record.id)
    reader._repo = repo
    reader._refresh_simplified_variants()
    reader._configure_simplified_tabs()
    reader.select_tab(variant)

    with patch(
        "lexiflow_ui.widgets.reader_widget.confirm_delete_simplification",
        return_value=True,
    ):
        reader._run_delete_simplification()

    assert not variant_path(Path(record.folder), variant).exists()
    assert reader._active_tab == TRANSLATED_TAB
    assert variant not in reader._tab_buttons
