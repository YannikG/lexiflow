"""Navigate from vocabulary to matching library texts."""

from __future__ import annotations

from collections.abc import Callable

from lexiflow_core.library.index import LibraryIndex
from lexiflow_core.library.search import search_texts
from lexiflow_core.library.search_models import SearchHit
from PySide6.QtWidgets import QMessageBox, QWidget


def find_in_texts(
    parent: QWidget,
    *,
    index: LibraryIndex,
    language_code: str,
    query: str,
    on_hit_selected: Callable[[SearchHit], None],
) -> None:
    """Search the library for *query* and open the first hit when found."""
    hits = search_texts(index, lang=language_code, query=query)
    if not hits:
        QMessageBox.information(
            parent,
            "Find in texts",
            f'No texts contain "{query}" in {language_code}.',
        )
        return
    on_hit_selected(hits[0])
