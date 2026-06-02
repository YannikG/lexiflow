"""Shared helpers for reader UI tests (no MainWindow/worker)."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.config.settings import Settings
from lexiflow_core.library.index import LibraryIndex
from lexiflow_core.library.reader_tabs import level_from_simplified_variant
from lexiflow_core.library.text_repository import TextRepository
from lexiflow_ui.widgets.reader_widget import ReaderWidget

from tests.ui.test_reader import _seed_reader_text


def reader_with_text(
    qtbot,
    data_root: Path,
    *,
    tab: str = "translated",
    body: str = "Texto con Cuerpo traducido.",
) -> ReaderWidget:
    """Reader wired for highlight-add tests without starting the worker."""
    _seed_reader_text(data_root)
    index = LibraryIndex(data_root)
    records = index.list_by_lang("es")
    assert records
    reader = ReaderWidget(data_root=data_root)
    qtbot.addWidget(reader)
    reader.resize(640, 480)
    reader._record = records[0]
    reader._repo = TextRepository(data_root, index)
    reader._settings = Settings(
        data_root=data_root,
        active_target_language="es",
        native_language="en",
    )
    reader._active_tab = tab
    reader._active_simplified_level = level_from_simplified_variant(tab)
    reader._read_pane.setPlainText(body)
    reader._update_reader_action_buttons()
    reader.show()
    qtbot.waitExposed(reader)
    return reader
