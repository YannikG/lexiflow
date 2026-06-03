"""Reader simplify controls and new words panel tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from lexiflow_core.config.paths import variant_path
from lexiflow_core.jobs.models import JobStatus, JobType
from lexiflow_core.jobs.runner import run_worker_loop
from lexiflow_core.jobs.service import JobService
from lexiflow_core.languages.models import CEFRLevel
from lexiflow_core.library.index import LibraryIndex
from lexiflow_core.library.library_coordinator import LibraryCoordinator
from lexiflow_core.library.models import CreateTextRequest
from lexiflow_core.library.reader_tabs import TRANSLATED_TAB
from lexiflow_core.library.text_repository import TextRepository
from lexiflow_core.llm.fake import FakeLLM
from lexiflow_core.simplify.suggestions_store import save_suggestions, suggestions_path
from lexiflow_core.vocabulary.models import NewWordSuggestion, WordCategory
from lexiflow_core.vocabulary.store import VocabularyStore
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTextBrowser,
    QWidget,
)

from tests.ui.test_reader import (
    _click_sidebar_text,
    _open_reader_window,
    _seed_reader_text,
)


def _simplified_level_tab(window, level: str = "A2") -> QPushButton:
    object_name = f"reader_tab_simplified_{level.lower()}"
    button = window.reader.findChild(QPushButton, object_name)
    assert button is not None
    return button


def _patch_simplify_level(monkeypatch: pytest.MonkeyPatch, level: CEFRLevel) -> None:
    monkeypatch.setattr(
        "lexiflow_ui.widgets.reader_widget.open_simplify_level_dialog",
        lambda *_args, **_kwargs: level,
    )


def _open_reader_window_without_worker(qtbot, data_root: Path):
    import sys

    from tests.ui.fakes import FakeProcess

    FakeProcess.instances.clear()
    from lexiflow_core.config.settings import Settings
    from lexiflow_ui.main_window import MainWindow
    from lexiflow_ui.worker_supervisor import WorkerSupervisor

    supervisor = WorkerSupervisor(
        data_root=data_root,
        executable=sys.executable,
        process_factory=FakeProcess,
    )
    window = MainWindow(
        supervisor=supervisor,
        settings=Settings(
            data_root=data_root,
            active_target_language="es",
            native_language="en",
        ),
        data_root=data_root,
    )
    qtbot.addWidget(window)
    window.show()
    qtbot.waitExposed(window)
    return window


def _valid_simplify_json(
    *,
    title: str = "Simple",
    body: str = "Texto simple.",
    lemma: str = "nadar",
    gloss: str = "to swim",
) -> str:
    return json.dumps(
        {
            "title": title,
            "body": body,
            "new_words": [
                {
                    "lemma": lemma,
                    "gloss": gloss,
                    "explanation": "Move through water using limbs.",
                    "level": "A2",
                    "category": "verb",
                },
            ],
        }
    )


def _seed_text_without_translated(data_root: Path) -> None:
    coordinator, index = LibraryCoordinator.open(data_root)
    del coordinator
    repo = TextRepository(data_root, index)
    repo.create_text(
        CreateTextRequest(
            title="Untitled",
            group="News",
            target_language="es",
            native_language="en",
            body="hola",
        )
    )


def _seed_simplified_with_suggestions(data_root: Path) -> None:
    _seed_reader_text(data_root)
    index = LibraryIndex(data_root)
    record = index.list_by_lang("es")[0]
    folder = Path(record.folder)
    variant_path(folder, "simplified-a2").write_text(
        "# Simple\n\nTexto simple.",
        encoding="utf-8",
    )
    save_suggestions(
        folder,
        "simplified-a2",
        (
            NewWordSuggestion(
                lemma="nadar",
                gloss="to swim",
                suggested_level=CEFRLevel.A2,
                word_category=WordCategory.VERB,
            ),
        ),
    )


def test_word_panel_shows_new_words_on_simplified_tab(qtbot, tmp_path) -> None:
    data_root = tmp_path / "LexiFlow"
    _seed_simplified_with_suggestions(data_root)
    window = _open_reader_window(qtbot, data_root)
    _click_sidebar_text(qtbot, window)

    simplified_tab = _simplified_level_tab(window)
    assert simplified_tab is not None
    qtbot.mouseClick(simplified_tab, Qt.MouseButton.LeftButton)
    qtbot.wait(50)

    panel = window.reader.findChild(QWidget, "word_panel")
    assert panel is not None
    assert panel.isVisible()
    table = panel.findChild(QTableWidget, "word_panel_new_table")
    assert table is not None
    assert table.rowCount() == 1
    assert table.item(0, 0) is not None
    assert table.item(0, 0).text() == "nadar"
    assert table.item(0, 1) is not None
    assert table.item(0, 1).text() == "to swim"


def test_word_panel_learned_tab_shows_vocabulary_entries(qtbot, tmp_path) -> None:
    data_root = tmp_path / "LexiFlow"
    _seed_simplified_with_suggestions(data_root)
    VocabularyStore(data_root, "es").add_from_suggestion(
        NewWordSuggestion(
            lemma="nadar",
            gloss="to swim",
            suggested_level=CEFRLevel.A2,
            word_category=WordCategory.VERB,
        ),
    )
    window = _open_reader_window(qtbot, data_root)
    _click_sidebar_text(qtbot, window)

    simplified_tab = _simplified_level_tab(window)
    assert simplified_tab is not None
    qtbot.mouseClick(simplified_tab, Qt.MouseButton.LeftButton)
    qtbot.wait(50)

    panel = window.reader.findChild(QWidget, "word_panel")
    assert panel is not None
    assert panel.isVisible()
    new_table = panel.findChild(QTableWidget, "word_panel_new_table")
    learned_table = panel.findChild(QTableWidget, "word_panel_learned_table")
    assert new_table is not None
    assert learned_table is not None
    assert new_table.rowCount() == 0
    assert learned_table.rowCount() == 1
    assert learned_table.item(0, 0) is not None
    assert learned_table.item(0, 0).text() == "nadar"


def test_word_panel_learned_tab_shows_manually_added_word_in_text(
    qtbot, tmp_path
) -> None:
    data_root = tmp_path / "LexiFlow"
    _seed_simplified_with_suggestions(data_root)
    VocabularyStore(data_root, "es").add_entry(
        lemma="simple",
        translation="simple",
        explanation="",
        level_when_learned=CEFRLevel.A2,
        word_category=WordCategory.ADJECTIVE,
    )
    window = _open_reader_window(qtbot, data_root)
    _click_sidebar_text(qtbot, window)

    simplified_tab = _simplified_level_tab(window)
    assert simplified_tab is not None
    qtbot.mouseClick(simplified_tab, Qt.MouseButton.LeftButton)
    qtbot.wait(50)

    panel = window.reader.findChild(QWidget, "word_panel")
    assert panel is not None
    new_table = panel.findChild(QTableWidget, "word_panel_new_table")
    learned_table = panel.findChild(QTableWidget, "word_panel_learned_table")
    assert new_table is not None and learned_table is not None
    assert new_table.rowCount() == 1
    assert new_table.item(0, 0) is not None
    assert new_table.item(0, 0).text() == "nadar"
    assert learned_table.rowCount() == 1
    assert learned_table.item(0, 0) is not None
    assert learned_table.item(0, 0).text() == "simple"


def test_word_panel_learned_delete_removes_entry_from_store(
    qtbot, tmp_path: Path, monkeypatch
) -> None:
    from lexiflow_ui.widgets.word_panel import WordPanel

    data_root = tmp_path / "LexiFlow"
    _seed_simplified_with_suggestions(data_root)
    VocabularyStore(data_root, "es").add_entry(
        lemma="simple",
        translation="simple",
        explanation="",
        level_when_learned=CEFRLevel.A2,
        word_category=WordCategory.ADJECTIVE,
    )
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
    )
    window = _open_reader_window(qtbot, data_root)
    _click_sidebar_text(qtbot, window)

    simplified_tab = _simplified_level_tab(window)
    assert simplified_tab is not None
    qtbot.mouseClick(simplified_tab, Qt.MouseButton.LeftButton)
    qtbot.wait(50)

    panel = window.reader.findChild(WordPanel, "word_panel")
    assert panel is not None
    panel.request_delete_learned(0)

    store = VocabularyStore(data_root, "es")
    assert not store.has_lemma("simple")
    learned_table = panel.findChild(QTableWidget, "word_panel_learned_table")
    assert learned_table is not None
    assert learned_table.rowCount() == 0

    undo_button = window.reader.findChild(QPushButton, "vocabulary_delete_undo_button")
    assert undo_button is not None
    qtbot.mouseClick(undo_button, Qt.MouseButton.LeftButton)

    assert store.has_lemma("simple")
    assert learned_table.rowCount() == 1


def test_word_panel_learned_tab_refreshes_after_vocabulary_changed(
    qtbot, tmp_path
) -> None:
    data_root = tmp_path / "LexiFlow"
    _seed_simplified_with_suggestions(data_root)
    window = _open_reader_window(qtbot, data_root)
    _click_sidebar_text(qtbot, window)

    simplified_tab = _simplified_level_tab(window)
    assert simplified_tab is not None
    qtbot.mouseClick(simplified_tab, Qt.MouseButton.LeftButton)
    qtbot.wait(50)

    VocabularyStore(data_root, "es").add_entry(
        lemma="simple",
        translation="simple",
        explanation="",
        level_when_learned=CEFRLevel.A2,
        word_category=WordCategory.ADJECTIVE,
    )
    window.reader.vocabulary_changed.emit()
    qtbot.wait(50)

    learned_table = window.reader.findChild(QTableWidget, "word_panel_learned_table")
    assert learned_table is not None
    assert learned_table.rowCount() == 1
    assert learned_table.item(0, 0) is not None
    assert learned_table.item(0, 0).text() == "simple"


def test_simplify_button_enqueues_job(
    qtbot, tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data_root = tmp_path / "LexiFlow"
    _seed_reader_text(data_root)
    _patch_simplify_level(monkeypatch, CEFRLevel.A2)
    window = _open_reader_window_without_worker(qtbot, data_root)
    _click_sidebar_text(qtbot, window)

    simplify_button = window.reader.findChild(QPushButton, "reader_simplify_button")
    assert simplify_button is not None
    qtbot.mouseClick(simplify_button, Qt.MouseButton.LeftButton)
    qtbot.wait(50)

    jobs = [
        job
        for job in JobService(data_root).list_jobs()
        if job.job_type == JobType.SIMPLIFY
    ]
    assert len(jobs) == 1
    assert jobs[0].payload["level"] == "A2"


def test_simplify_second_level_uses_dialog_while_on_other_simplified_tab(
    qtbot, tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Choosing another level in the dialog creates that variant, not the active tab."""
    data_root = tmp_path / "LexiFlow"
    _seed_simplified_with_suggestions(data_root)
    _patch_simplify_level(monkeypatch, CEFRLevel.B1)
    window = _open_reader_window_without_worker(qtbot, data_root)
    _click_sidebar_text(qtbot, window)

    simplified_tab = _simplified_level_tab(window)
    simplify_button = window.reader.findChild(QPushButton, "reader_simplify_button")
    assert simplify_button is not None

    qtbot.mouseClick(simplified_tab, Qt.MouseButton.LeftButton)
    qtbot.wait(50)

    qtbot.mouseClick(simplify_button, Qt.MouseButton.LeftButton)
    qtbot.wait(50)

    jobs = [
        job
        for job in JobService(data_root).list_jobs()
        if job.job_type == JobType.SIMPLIFY
    ]
    assert len(jobs) == 1
    assert jobs[0].payload["level"] == "B1"
    assert window.reader.active_tab_id == "simplified-b1"

    b1_json = _valid_simplify_json(
        title="Simple B1",
        body="Corro cada dia.",
        lemma="correr",
        gloss="to run",
    )
    run_worker_loop(
        JobService(data_root),
        FakeLLM(response=b1_json),
        data_root=data_root,
    )
    window._reader.reload_from_disk(focus_simplified_level=CEFRLevel.B1)
    qtbot.wait(50)

    index = LibraryIndex(data_root)
    record = index.list_by_lang("es")[0]
    folder = Path(record.folder)
    assert variant_path(folder, "simplified-a2").is_file()
    assert variant_path(folder, "simplified-b1").is_file()
    assert suggestions_path(folder, "simplified-b1").is_file()
    assert window.reader.active_tab_id == "simplified-b1"

    assert _simplified_level_tab(window, "A2").isVisible()
    assert _simplified_level_tab(window, "B1").isVisible()

    panel = window.reader.findChild(QWidget, "word_panel")
    assert panel is not None and panel.isVisible()
    new_table = panel.findChild(QTableWidget, "word_panel_new_table")
    assert new_table is not None
    assert new_table.rowCount() == 1
    assert new_table.item(0, 0) is not None
    assert new_table.item(0, 0).text() == "correr"


def _seed_simplified_a2_with_b2_suggestion(data_root: Path) -> None:
    _seed_reader_text(data_root)
    index = LibraryIndex(data_root)
    record = index.list_by_lang("es")[0]
    folder = Path(record.folder)
    variant_path(folder, "simplified-a2").write_text(
        "# Simple\n\nTexto simple.",
        encoding="utf-8",
    )
    save_suggestions(
        folder,
        "simplified-a2",
        (
            NewWordSuggestion(
                lemma="sofisticado",
                gloss="sophisticated",
                suggested_level=CEFRLevel.B2,
                word_category=WordCategory.ADJECTIVE,
            ),
        ),
    )


def test_word_panel_add_uses_suggestion_level_not_active_tab(qtbot, tmp_path) -> None:
    """New-word Add stores the suggestion level, not the simplified tab level."""
    data_root = tmp_path / "LexiFlow"
    _seed_simplified_a2_with_b2_suggestion(data_root)
    window = _open_reader_window(qtbot, data_root)
    _click_sidebar_text(qtbot, window)

    simplified_tab = _simplified_level_tab(window)
    assert simplified_tab is not None
    qtbot.mouseClick(simplified_tab, Qt.MouseButton.LeftButton)
    qtbot.wait(50)

    panel = window.reader.findChild(QWidget, "word_panel")
    assert panel is not None
    table = panel.findChild(QTableWidget, "word_panel_new_table")
    assert table is not None
    assert table.item(0, 3) is not None
    assert table.item(0, 3).text() == "B2"

    add_button = window.reader.findChild(QPushButton, "word_panel_add_button")
    assert add_button is not None
    qtbot.mouseClick(add_button, Qt.MouseButton.LeftButton)
    qtbot.wait(50)

    store = VocabularyStore(data_root, "es")
    entry = store.get("sofisticado")
    assert entry is not None
    assert entry.level_when_learned == CEFRLevel.B2


def test_new_words_add_persists_vocabulary_entry(qtbot, tmp_path) -> None:
    data_root = tmp_path / "LexiFlow"
    _seed_simplified_with_suggestions(data_root)
    window = _open_reader_window(qtbot, data_root)
    _click_sidebar_text(qtbot, window)

    simplified_tab = _simplified_level_tab(window)
    assert simplified_tab is not None
    qtbot.mouseClick(simplified_tab, Qt.MouseButton.LeftButton)
    qtbot.wait(50)

    add_button = window.reader.findChild(QPushButton, "word_panel_add_button")
    assert add_button is not None
    qtbot.mouseClick(add_button, Qt.MouseButton.LeftButton)
    qtbot.wait(50)

    store = VocabularyStore(data_root, "es")
    assert store.has_lemma("nadar")
    entries = store.list_for_simplify()
    assert len(entries) == 1
    assert entries[0].level_when_learned == CEFRLevel.A2


def test_new_words_add_enqueues_vocabulary_embed_job(qtbot, tmp_path) -> None:
    data_root = tmp_path / "LexiFlow"
    _seed_simplified_with_suggestions(data_root)
    window = _open_reader_window(qtbot, data_root)
    _click_sidebar_text(qtbot, window)

    simplified_tab = _simplified_level_tab(window)
    assert simplified_tab is not None
    qtbot.mouseClick(simplified_tab, Qt.MouseButton.LeftButton)
    qtbot.wait(50)

    add_button = window.reader.findChild(QPushButton, "word_panel_add_button")
    assert add_button is not None
    qtbot.mouseClick(add_button, Qt.MouseButton.LeftButton)
    qtbot.wait(50)

    embed_jobs = [
        job
        for job in JobService(data_root).list_jobs()
        if job.job_type == JobType.EMBED and job.payload.get("lemma") == "nadar"
    ]
    assert len(embed_jobs) == 1
    assert embed_jobs[0].payload["language_code"] == "es"


def test_translated_tab_shows_placeholder_when_variant_missing(qtbot, tmp_path) -> None:
    data_root = tmp_path / "LexiFlow"
    _seed_text_without_translated(data_root)
    window = _open_reader_window(qtbot, data_root)
    _click_sidebar_text(qtbot, window)

    read_pane = window.reader.findChild(QTextBrowser, "reader_read_pane")
    assert read_pane is not None
    assert window.reader.active_tab_id == TRANSLATED_TAB
    assert "not available yet" in read_pane.toPlainText().lower()


def test_simplify_click_shows_pending_tab_before_worker_runs(
    qtbot, tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data_root = tmp_path / "LexiFlow"
    _seed_reader_text(data_root)
    _patch_simplify_level(monkeypatch, CEFRLevel.A2)
    window = _open_reader_window_without_worker(qtbot, data_root)
    _click_sidebar_text(qtbot, window)

    simplify_button = window.reader.findChild(QPushButton, "reader_simplify_button")
    assert simplify_button is not None
    qtbot.mouseClick(simplify_button, Qt.MouseButton.LeftButton)
    qtbot.wait(50)

    simplified_tab = _simplified_level_tab(window)
    assert simplified_tab.isVisible()
    assert window.reader.active_tab_id == "simplified-a2"
    read_pane = window.reader.findChild(QTextBrowser, "reader_read_pane")
    assert read_pane is not None
    pane_text = read_pane.toPlainText().lower()
    assert (
        "still being generated" in pane_text
        or "generating a simplified variant" in pane_text
    )


def test_simplify_click_worker_completion_shows_simplified_tab(
    qtbot, tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data_root = tmp_path / "LexiFlow"
    _seed_reader_text(data_root)
    _patch_simplify_level(monkeypatch, CEFRLevel.A2)
    window = _open_reader_window_without_worker(qtbot, data_root)
    _click_sidebar_text(qtbot, window)

    simplify_button = window.reader.findChild(QPushButton, "reader_simplify_button")
    assert simplify_button is not None
    qtbot.mouseClick(simplify_button, Qt.MouseButton.LeftButton)
    qtbot.wait(50)

    jobs = JobService(data_root)
    run_worker_loop(jobs, FakeLLM(response=_valid_simplify_json()), data_root=data_root)

    window._reader.reload_from_disk(focus_simplified_level=CEFRLevel.A2)
    qtbot.wait(50)

    assert window.reader.active_tab_id == "simplified-a2"
    read_pane = window.reader.findChild(QTextBrowser, "reader_read_pane")
    assert read_pane is not None
    assert "Texto simple" in read_pane.toPlainText()


def test_simplify_click_worker_failure_hides_simplified_tab(
    qtbot, tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data_root = tmp_path / "LexiFlow"
    _seed_reader_text(data_root)
    _patch_simplify_level(monkeypatch, CEFRLevel.A2)
    window = _open_reader_window_without_worker(qtbot, data_root)
    _click_sidebar_text(qtbot, window)

    simplify_button = window.reader.findChild(QPushButton, "reader_simplify_button")
    assert simplify_button is not None
    qtbot.mouseClick(simplify_button, Qt.MouseButton.LeftButton)
    qtbot.wait(50)

    jobs = JobService(data_root)
    run_worker_loop(jobs, FakeLLM(response="not json"), data_root=data_root)

    window._reader.reload_from_disk()
    qtbot.wait(50)

    simplified_tab = window.reader.findChild(QPushButton, "reader_tab_simplified_a2")
    assert simplified_tab is None or not simplified_tab.isVisible()
    failed = [
        job
        for job in jobs.list_jobs()
        if job.job_type == JobType.SIMPLIFY and job.status == JobStatus.FAILED
    ]
    assert len(failed) == 1
