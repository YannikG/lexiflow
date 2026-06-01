"""UI polish tests for background job feedback and reader refresh."""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import UUID

import pytest
from lexiflow_core.jobs.handlers.cleanup import TRANSLATE_PHASE_PLAIN
from lexiflow_core.jobs.models import JobRequest, JobStatus, JobType
from lexiflow_core.jobs.runner import run_worker_loop
from lexiflow_core.jobs.service import JobService
from lexiflow_core.library.index import LibraryIndex
from lexiflow_core.library.reader_tabs import NATIVE_TAB, SIMPLIFIED_PREFIX
from lexiflow_core.llm.fake import FakeLLM
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton, QTextBrowser, QWidget

from tests.ui.staged_generation_helpers import seed_staged_text
from tests.ui.test_reader import (
    _click_sidebar_text,
    _open_reader_window,
    _seed_reader_text,
)
from tests.ui.test_simplify_reader import (
    _open_reader_window_without_worker,
    _seed_text_without_translated,
    _valid_simplify_json,
)


def _text_id(data_root) -> UUID:
    return LibraryIndex(data_root).list_by_lang("es")[0].id


def _valid_translate_json() -> str:
    return "# Traducción\n\nCuerpo traducido."


def test_reader_shows_pending_message_for_queued_translate(qtbot, tmp_path) -> None:
    data_root = tmp_path / "LexiFlow"
    _seed_text_without_translated(data_root)
    text_id = _text_id(data_root)
    JobService(data_root).enqueue(
        JobRequest(
            job_type=JobType.TRANSLATE,
            payload={"text_id": str(text_id), "phase": TRANSLATE_PHASE_PLAIN},
        )
    )
    window = _open_reader_window(qtbot, data_root)
    _click_sidebar_text(qtbot, window)

    read_pane = window.reader.findChild(QTextBrowser, "reader_read_pane")
    assert read_pane is not None
    assert "still being generated" in read_pane.toPlainText().lower()


def test_reader_shows_failed_message_for_failed_translate(qtbot, tmp_path) -> None:
    data_root = tmp_path / "LexiFlow"
    _seed_text_without_translated(data_root)
    text_id = _text_id(data_root)
    jobs = JobService(data_root)
    jobs.enqueue(
        JobRequest(
            job_type=JobType.TRANSLATE,
            payload={"text_id": str(text_id), "phase": TRANSLATE_PHASE_PLAIN},
        )
    )
    run_worker_loop(
        jobs,
        FakeLLM(response="plain body without heading"),
        data_root=data_root,
    )
    window = _open_reader_window(qtbot, data_root)
    _click_sidebar_text(qtbot, window)

    read_pane = window.reader.findChild(QTextBrowser, "reader_read_pane")
    assert read_pane is not None
    assert "generation failed" in read_pane.toPlainText().lower()


def test_poll_reloads_translated_when_translate_completes(qtbot, tmp_path) -> None:
    data_root = tmp_path / "LexiFlow"
    _seed_text_without_translated(data_root)
    text_id = _text_id(data_root)
    jobs = JobService(data_root)
    jobs.enqueue(
        JobRequest(
            job_type=JobType.TRANSLATE,
            payload={"text_id": str(text_id), "phase": TRANSLATE_PHASE_PLAIN},
        )
    )
    window = _open_reader_window_without_worker(qtbot, data_root)
    _click_sidebar_text(qtbot, window)

    read_pane = window.reader.findChild(QTextBrowser, "reader_read_pane")
    assert read_pane is not None
    assert "still being generated" in read_pane.toPlainText().lower()

    run_worker_loop(
        jobs,
        FakeLLM(response=_valid_translate_json()),
        data_root=data_root,
    )
    window._poll_background_jobs()

    assert "Cuerpo traducido" in read_pane.toPlainText()


def test_poll_shows_status_bar_error_when_cleanup_fails(qtbot, tmp_path) -> None:
    data_root = tmp_path / "LexiFlow"
    _repo, text_id, _folder = seed_staged_text(data_root)
    jobs = JobService(data_root)
    window = _open_reader_window_without_worker(qtbot, data_root)
    _click_sidebar_text(qtbot, window)
    window.reader.select_tab(NATIVE_TAB)
    run_worker_loop(
        jobs,
        FakeLLM(response="plain body without heading"),
        data_root=data_root,
    )
    window._poll_background_jobs()

    assert "cleanup failed" in window.statusBar().currentMessage().lower()
    cleanup_jobs = [
        job
        for job in jobs.list_jobs()
        if (
            job.job_type == JobType.CLEANUP
            and job.payload.get("text_id") == str(text_id)
        )
    ]
    assert cleanup_jobs[0].status == JobStatus.FAILED


def test_poll_shows_status_bar_error_when_simplify_fails(qtbot, tmp_path) -> None:
    data_root = tmp_path / "LexiFlow"
    _seed_reader_text(data_root)
    text_id = _text_id(data_root)
    jobs = JobService(data_root)
    jobs.enqueue(
        JobRequest(
            job_type=JobType.SIMPLIFY,
            payload={"text_id": str(text_id), "level": "A2"},
        )
    )
    run_worker_loop(jobs, FakeLLM(response="not json"), data_root=data_root)

    window = _open_reader_window(qtbot, data_root)
    _click_sidebar_text(qtbot, window)
    window._poll_background_jobs()

    assert "simplify failed" in window.statusBar().currentMessage().lower()


def test_poll_switches_to_simplified_tab_on_success(qtbot, tmp_path) -> None:
    data_root = tmp_path / "LexiFlow"
    _seed_reader_text(data_root)
    text_id = _text_id(data_root)
    jobs = JobService(data_root)
    jobs.enqueue(
        JobRequest(
            job_type=JobType.SIMPLIFY,
            payload={"text_id": str(text_id), "level": "A2"},
        )
    )
    run_worker_loop(
        jobs,
        FakeLLM(response=_valid_simplify_json()),
        data_root=data_root,
    )

    window = _open_reader_window(qtbot, data_root)
    _click_sidebar_text(qtbot, window)
    window._poll_background_jobs()

    assert window.reader.active_tab_id == f"{SIMPLIFIED_PREFIX}a2"
    read_pane = window.reader.findChild(QTextBrowser, "reader_read_pane")
    assert read_pane is not None
    assert "Texto simple" in read_pane.toPlainText()


def test_new_words_panel_hidden_on_translated_tab(qtbot, tmp_path) -> None:
    data_root = tmp_path / "LexiFlow"
    _seed_reader_text(data_root)
    window = _open_reader_window(qtbot, data_root)
    _click_sidebar_text(qtbot, window)

    panel = window.reader.findChild(QWidget, "new_words_panel")
    assert panel is not None
    assert not panel.isVisible()


def test_simplify_without_translated_shows_dialog_and_skips_enqueue(
    qtbot, tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data_root = tmp_path / "LexiFlow"
    _seed_text_without_translated(data_root)
    window = _open_reader_window_without_worker(qtbot, data_root)
    _click_sidebar_text(qtbot, window)

    information = MagicMock()
    monkeypatch.setattr(
        "lexiflow_ui.widgets.reader_widget.confirm_simplify_without_translated",
        information,
    )

    simplify_button = window.reader.findChild(QPushButton, "reader_simplify_button")
    assert simplify_button is not None
    qtbot.mouseClick(simplify_button, Qt.MouseButton.LeftButton)
    qtbot.wait(50)

    information.assert_called_once()
    jobs = [
        job
        for job in JobService(data_root).list_jobs()
        if job.job_type == JobType.SIMPLIFY
    ]
    assert jobs == []
