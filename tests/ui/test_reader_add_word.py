"""Reader highlight-add vocabulary tests."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from lexiflow_core.config.paths import variant_path
from lexiflow_core.languages.models import CEFRLevel
from lexiflow_core.library.index import LibraryIndex
from lexiflow_core.library.reader_tabs import TRANSLATED_TAB, simplified_variant_name
from PySide6.QtWidgets import QTextBrowser

from tests.ui.reader_test_helpers import reader_with_text
from tests.ui.test_reader import _seed_reader_text
from tests.ui.vocabulary_helpers import select_word_in_reader


def test_highlight_add_passes_selection_to_add_word_flow(qtbot, tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    reader = reader_with_text(qtbot, data_root, tab=TRANSLATED_TAB)
    selected = select_word_in_reader(reader)

    with patch(
        "lexiflow_ui.reader_add_word.prompt_add_word_with_lemma_resolution",
        return_value=None,
    ) as prompt:
        reader.request_add_word_from_selection()

    prompt.assert_called_once()
    assert prompt.call_args.kwargs["surface_form"] == selected


def test_highlight_add_on_simplified_tab_passes_selection(
    qtbot, tmp_path: Path
) -> None:
    data_root = tmp_path / "LexiFlow"
    repo = _seed_reader_text(data_root)
    index = LibraryIndex(data_root)
    titles = index.list_by_lang("es")
    assert titles
    record = repo.get_text(titles[0].id)
    variant = simplified_variant_name(CEFRLevel.B1)
    variant_path(Path(record.folder), variant).write_text(
        "# Simple\n\nTexto simple con Cuerpo.",
        encoding="utf-8",
    )
    reader = reader_with_text(
        qtbot,
        data_root,
        tab=variant,
        body="Texto simple con Cuerpo.",
    )
    selected = select_word_in_reader(reader, text="Cuerpo")

    with patch(
        "lexiflow_ui.reader_add_word.prompt_add_word_with_lemma_resolution",
        return_value=None,
    ) as prompt:
        reader.request_add_word_from_selection()

    prompt.assert_called_once()
    assert prompt.call_args.kwargs["surface_form"] == selected


def test_request_add_word_without_selection_shows_select_first_message(
    qtbot,
    tmp_path: Path,
) -> None:
    data_root = tmp_path / "LexiFlow"
    reader = reader_with_text(qtbot, data_root, tab=TRANSLATED_TAB)
    pane = reader.findChild(QTextBrowser, "reader_read_pane")
    assert pane is not None
    cursor = pane.textCursor()
    cursor.clearSelection()
    pane.setTextCursor(cursor)

    with patch(
        "lexiflow_ui.reader_add_word.QMessageBox.information",
    ) as inform:
        saved = reader.request_add_word_from_selection()

    assert saved is False
    inform.assert_called_once()
    assert "Select a word" in inform.call_args[0][2]
