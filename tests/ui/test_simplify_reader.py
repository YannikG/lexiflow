"""Reader simplify controls and new words panel tests."""

from __future__ import annotations

import json
from pathlib import Path

from lexiflow_core.config.paths import variant_path
from lexiflow_core.jobs.models import JobStatus, JobType
from lexiflow_core.jobs.runner import run_worker_loop
from lexiflow_core.jobs.service import JobService
from lexiflow_core.languages.models import CEFRLevel
from lexiflow_core.languages.store import LanguageStore
from lexiflow_core.library.index import LibraryIndex
from lexiflow_core.library.library_coordinator import LibraryCoordinator
from lexiflow_core.library.models import CreateTextRequest
from lexiflow_core.library.reader_tabs import TRANSLATED_TAB
from lexiflow_core.library.text_repository import TextRepository
from lexiflow_core.llm.fake import FakeLLM
from lexiflow_core.simplify.suggestions_store import save_suggestions
from lexiflow_core.vocabulary.models import NewWordSuggestion
from lexiflow_core.vocabulary.store import VocabularyStore
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QPushButton, QTextBrowser, QWidget

from tests.ui.test_reader import (
    _click_sidebar_text,
    _open_reader_window,
    _seed_reader_text,
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


def _valid_simplify_json(*, title: str = "Simple", body: str = "Texto simple.") -> str:
    return json.dumps(
        {
            "title": title,
            "body": body,
            "new_words": [
                {"lemma": "nadar", "gloss": "to swim", "level": "A2"},
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
            ),
        ),
    )


def test_new_words_panel_shows_suggestions_on_simplified_tab(qtbot, tmp_path) -> None:
    data_root = tmp_path / "LexiFlow"
    _seed_simplified_with_suggestions(data_root)
    window = _open_reader_window(qtbot, data_root)
    _click_sidebar_text(qtbot, window)

    simplified_tab = window.reader.findChild(QPushButton, "reader_tab_simplified")
    assert simplified_tab is not None
    qtbot.mouseClick(simplified_tab, Qt.MouseButton.LeftButton)
    qtbot.wait(50)

    panel = window.reader.findChild(QWidget, "new_words_panel")
    assert panel is not None
    assert panel.isVisible()
    label = panel.findChild(QWidget, "new_words_label")
    assert label is not None
    assert "nadar" in label.text()


def test_simplify_button_enqueues_job(qtbot, tmp_path) -> None:
    data_root = tmp_path / "LexiFlow"
    _seed_reader_text(data_root)
    window = _open_reader_window(qtbot, data_root)
    _click_sidebar_text(qtbot, window)

    level_combo = window.reader.findChild(QComboBox, "reader_simplify_level")
    simplify_button = window.reader.findChild(QPushButton, "reader_simplify_button")
    assert level_combo is not None and simplify_button is not None
    level_combo.setCurrentText("A2")
    qtbot.mouseClick(simplify_button, Qt.MouseButton.LeftButton)
    qtbot.wait(50)

    jobs = [
        job
        for job in JobService(data_root).list_jobs()
        if job.job_type == JobType.SIMPLIFY
    ]
    assert len(jobs) == 1
    assert jobs[0].payload["level"] == "A2"


def test_simplify_level_picker_defaults_to_user_language_level(
    qtbot, tmp_path
) -> None:
    data_root = tmp_path / "LexiFlow"
    LanguageStore(data_root).add_target("es", CEFRLevel.B1)
    _seed_reader_text(data_root)
    window = _open_reader_window(qtbot, data_root)
    _click_sidebar_text(qtbot, window)

    level_combo = window.reader.findChild(QComboBox, "reader_simplify_level")
    assert level_combo is not None
    assert level_combo.currentText() == "B1"


def test_simplified_tab_syncs_simplify_level_picker(qtbot, tmp_path) -> None:
    data_root = tmp_path / "LexiFlow"
    _seed_simplified_with_suggestions(data_root)
    window = _open_reader_window(qtbot, data_root)
    _click_sidebar_text(qtbot, window)

    level_combo = window.reader.findChild(QComboBox, "reader_simplify_level")
    simplified_tab = window.reader.findChild(QPushButton, "reader_tab_simplified")
    assert level_combo is not None and simplified_tab is not None

    level_combo.setCurrentText("B1")
    qtbot.mouseClick(simplified_tab, Qt.MouseButton.LeftButton)
    qtbot.wait(50)

    assert level_combo.currentText() == "A2"


def test_new_words_add_persists_vocabulary_entry(qtbot, tmp_path) -> None:
    data_root = tmp_path / "LexiFlow"
    _seed_simplified_with_suggestions(data_root)
    window = _open_reader_window(qtbot, data_root)
    _click_sidebar_text(qtbot, window)

    simplified_tab = window.reader.findChild(QPushButton, "reader_tab_simplified")
    assert simplified_tab is not None
    qtbot.mouseClick(simplified_tab, Qt.MouseButton.LeftButton)
    qtbot.wait(50)

    add_button = window.reader.findChild(QPushButton, "new_words_add_button")
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

    simplified_tab = window.reader.findChild(QPushButton, "reader_tab_simplified")
    assert simplified_tab is not None
    qtbot.mouseClick(simplified_tab, Qt.MouseButton.LeftButton)
    qtbot.wait(50)

    add_button = window.reader.findChild(QPushButton, "new_words_add_button")
    assert add_button is not None
    qtbot.mouseClick(add_button, Qt.MouseButton.LeftButton)
    qtbot.wait(50)

    embed_jobs = [
        job
        for job in JobService(data_root).list_jobs()
        if job.job_type == JobType.EMBED
        and job.payload.get("lemma") == "nadar"
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


def test_simplify_click_worker_completion_shows_simplified_tab(qtbot, tmp_path) -> None:
    data_root = tmp_path / "LexiFlow"
    _seed_reader_text(data_root)
    window = _open_reader_window_without_worker(qtbot, data_root)
    _click_sidebar_text(qtbot, window)

    simplify_button = window.reader.findChild(QPushButton, "reader_simplify_button")
    assert simplify_button is not None
    qtbot.mouseClick(simplify_button, Qt.MouseButton.LeftButton)
    qtbot.wait(50)

    jobs = JobService(data_root)
    run_worker_loop(jobs, FakeLLM(response=_valid_simplify_json()), data_root=data_root)

    qtbot.wait(700)

    assert window.reader.active_tab_id == "simplified-a2"
    read_pane = window.reader.findChild(QTextBrowser, "reader_read_pane")
    assert read_pane is not None
    assert "Texto simple" in read_pane.toPlainText()


def test_simplify_click_worker_failure_hides_simplified_tab(qtbot, tmp_path) -> None:
    data_root = tmp_path / "LexiFlow"
    _seed_reader_text(data_root)
    window = _open_reader_window_without_worker(qtbot, data_root)
    _click_sidebar_text(qtbot, window)

    simplify_button = window.reader.findChild(QPushButton, "reader_simplify_button")
    assert simplify_button is not None
    qtbot.mouseClick(simplify_button, Qt.MouseButton.LeftButton)
    qtbot.wait(50)

    jobs = JobService(data_root)
    run_worker_loop(jobs, FakeLLM(response="not json"), data_root=data_root)

    qtbot.wait(700)

    simplified_tab = window.reader.findChild(QPushButton, "reader_tab_simplified")
    assert simplified_tab is None or not simplified_tab.isVisible()
    failed = [
        job
        for job in jobs.list_jobs()
        if job.job_type == JobType.SIMPLIFY and job.status == JobStatus.FAILED
    ]
    assert len(failed) == 1
