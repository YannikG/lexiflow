"""Level when learned defaults for reader add word."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.config.paths import variant_path
from lexiflow_core.languages.models import CEFRLevel
from lexiflow_core.languages.store import LanguageStore
from lexiflow_core.library.index import LibraryIndex
from lexiflow_core.library.reader_tabs import TRANSLATED_TAB, simplified_variant_name
from lexiflow_core.vocabulary.store import VocabularyStore
from lexiflow_ui.dialogs.add_word_dialog import AddWordForm
from lexiflow_ui.reader_add_word import persist_reader_add

from tests.ui.test_reader import (
    _click_sidebar_text,
    _open_reader_window,
    _seed_reader_text,
)


def test_add_from_simplified_tab_uses_form_level_not_active_tab(
    qtbot, tmp_path: Path
) -> None:
    """Level when learned follows the dialog choice, not the simplified tab."""
    data_root = tmp_path / "LexiFlow"
    repo = _seed_reader_text(data_root)
    try:
        LanguageStore(data_root).add_target("es", CEFRLevel.A2)
    except Exception:
        pass
    index = LibraryIndex(data_root)
    titles = index.list_by_lang("es")
    assert titles
    record = repo.get_text(titles[0].id)
    variant = simplified_variant_name(CEFRLevel.A2)
    variant_path(Path(record.folder), variant).write_text(
        "# Simple\n\nTexto simple.",
        encoding="utf-8",
    )
    window = _open_reader_window(qtbot, data_root)
    _click_sidebar_text(qtbot, window)
    window.reader.select_tab(variant)

    form = AddWordForm(
        lemma="sofisticado",
        translation="sophisticated",
        explanation="",
        level_when_learned=CEFRLevel.B2,
        surface_form="sofisticado",
    )
    assert (
        persist_reader_add(
            window,
            data_root=data_root,
            record=record,
            tab_id=variant,
            form=form,
            supervisor=window._supervisor,
        )
        is True
    )

    store = VocabularyStore(data_root, "es")
    entry = store.get("sofisticado")
    assert entry is not None
    assert entry.level_when_learned == CEFRLevel.B2


def test_add_from_simplified_tab_sets_level_when_learned(qtbot, tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    repo = _seed_reader_text(data_root)
    try:
        LanguageStore(data_root).add_target("es", CEFRLevel.A2)
    except Exception:
        pass
    index = LibraryIndex(data_root)
    titles = index.list_by_lang("es")
    assert titles
    record = repo.get_text(titles[0].id)
    variant = simplified_variant_name(CEFRLevel.B1)
    variant_path(Path(record.folder), variant).write_text(
        "# Simple\n\nTexto simple.",
        encoding="utf-8",
    )
    window = _open_reader_window(qtbot, data_root)
    _click_sidebar_text(qtbot, window)
    window.reader.select_tab(variant)

    form = AddWordForm(
        lemma="nadar",
        translation="to swim",
        explanation="",
        level_when_learned=CEFRLevel.B1,
        surface_form="nadar",
    )
    assert (
        persist_reader_add(
            window,
            data_root=data_root,
            record=record,
            tab_id=variant,
            form=form,
            supervisor=window._supervisor,
        )
        is True
    )

    store = VocabularyStore(data_root, "es")
    entry = store.get("nadar")
    assert entry is not None
    assert entry.level_when_learned == CEFRLevel.B1


def test_add_from_translated_tab_uses_user_level(qtbot, tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    repo = _seed_reader_text(data_root)
    LanguageStore(data_root).add_target("es", CEFRLevel.A2)
    index = LibraryIndex(data_root)
    titles = index.list_by_lang("es")
    assert titles
    record = repo.get_text(titles[0].id)
    window = _open_reader_window(qtbot, data_root)
    _click_sidebar_text(qtbot, window)
    window.reader.select_tab(TRANSLATED_TAB)

    form = AddWordForm(
        lemma="nadar",
        translation="to swim",
        explanation="",
        level_when_learned=CEFRLevel.A2,
        surface_form="nadar",
    )
    assert (
        persist_reader_add(
            window,
            data_root=data_root,
            record=record,
            tab_id=TRANSLATED_TAB,
            form=form,
            supervisor=window._supervisor,
        )
        is True
    )

    store = VocabularyStore(data_root, "es")
    entry = store.get("nadar")
    assert entry is not None
    assert entry.level_when_learned == CEFRLevel.A2
