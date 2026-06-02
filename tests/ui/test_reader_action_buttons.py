"""Tests for reader tab-specific action button visibility."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from lexiflow_core.languages.models import CEFRLevel
from lexiflow_core.library.index import LibraryIndex
from lexiflow_core.library.reader_tabs import (
    NATIVE_TAB,
    TRANSLATED_TAB,
    simplified_variant_name,
)

from tests.ui.reader_test_helpers import reader_with_text
from tests.ui.test_reader import _seed_reader_text


def test_retranslate_visible_only_on_translated_tab(qtbot, tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    reader = reader_with_text(qtbot, data_root)

    reader.select_tab(TRANSLATED_TAB)
    assert reader._active_tab == TRANSLATED_TAB
    assert not reader._retranslate_button.isHidden()
    assert reader._resimplify_button.isHidden()

    reader.select_tab(NATIVE_TAB)
    assert reader._active_tab == NATIVE_TAB
    assert reader._retranslate_button.isHidden()
    assert reader._resimplify_button.isHidden()


def test_resimplify_visible_only_on_simplified_tab(qtbot, tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    repo = _seed_reader_text(data_root)
    record = repo.get_text(LibraryIndex(data_root).list_by_lang("es")[0].id)
    variant = simplified_variant_name(CEFRLevel.B1)
    repo.apply_simplified_variant(
        record.id,
        level="b1",
        markdown="# B1\n\nTexto simple.",
    )
    reader = reader_with_text(qtbot, data_root)
    reader._record = repo.get_text(record.id)
    reader._repo = repo
    reader._refresh_simplified_variants()
    reader._configure_simplified_tabs()

    reader.select_tab(TRANSLATED_TAB)
    assert reader._resimplify_button.isHidden()
    assert reader._delete_simplification_button.isHidden()

    reader.select_tab(variant)
    assert reader._active_simplified_level == CEFRLevel.B1
    assert reader._retranslate_button.isHidden()
    assert not reader._resimplify_button.isHidden()


def test_resimplify_uses_level_of_active_simplified_tab(
    qtbot, tmp_path: Path, monkeypatch
) -> None:
    data_root = tmp_path / "LexiFlow"
    repo = _seed_reader_text(data_root)
    record = repo.get_text(LibraryIndex(data_root).list_by_lang("es")[0].id)
    for level in (CEFRLevel.A2, CEFRLevel.B1):
        repo.apply_simplified_variant(
            record.id,
            level=level.value.lower(),
            markdown=f"# {level.value}\n\nBody.",
        )
    reader = reader_with_text(qtbot, data_root)
    reader._record = repo.get_text(record.id)
    reader._repo = repo
    reader._data_root = data_root
    reader._refresh_simplified_variants()
    reader._configure_simplified_tabs()
    reader.select_tab(simplified_variant_name(CEFRLevel.B1))

    enqueued: list[CEFRLevel] = []
    reader._supervisor = MagicMock()

    def capture_enqueue(level: CEFRLevel) -> None:
        enqueued.append(level)

    with patch.object(reader, "_enqueue_simplify", side_effect=capture_enqueue):
        reader._run_resimplify()

    assert enqueued == [CEFRLevel.B1]
