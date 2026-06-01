"""UI tests for staged generation and native cleanup overlay."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.jobs.models import JobStatus
from lexiflow_core.jobs.runner import run_worker_loop
from lexiflow_core.jobs.service import JobService
from lexiflow_core.library.reader_tabs import NATIVE_TAB, TRANSLATED_TAB
from lexiflow_core.llm.fake import FakeLLM
from lexiflow_core.llm.unavailable import UnavailableLLM

from tests.ui.staged_generation_helpers import (
    CLEANED_NATIVE,
    MESSY_PASTE,
    VALID_TRANSLATED,
    assert_cleanup_job,
    assert_native_on_disk,
    assert_reader_ui,
    open_main_window,
    open_text_in_reader,
    read_pane,
    run_worker_and_poll,
    seed_staged_text,
)


def test_native_tab_shows_pending_overlay_not_raw_paste(qtbot, tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    _repo, text_id, folder = seed_staged_text(data_root)
    provisional = folder / "native.md"
    provisional_content = provisional.read_text(encoding="utf-8")
    window = open_main_window(qtbot, data_root, with_worker=False)
    open_text_in_reader(qtbot, window, text_id)
    window.reader.select_tab(NATIVE_TAB)

    assert_reader_ui(
        window,
        tab=NATIVE_TAB,
        contains="still being generated",
        excludes="Skip to content",
        edit_enabled=False,
    )
    assert_native_on_disk(folder, unchanged_from=provisional_content)
    assert_cleanup_job(data_root, text_id, status=JobStatus.PENDING)


def test_poll_shows_cleaned_native_after_cleanup_completes(
    qtbot, tmp_path: Path
) -> None:
    data_root = tmp_path / "LexiFlow"
    _repo, text_id, folder = seed_staged_text(data_root)
    jobs = JobService(data_root)
    window = open_main_window(qtbot, data_root, with_worker=False)
    open_text_in_reader(qtbot, window, text_id)
    window.reader.select_tab(NATIVE_TAB)

    run_worker_and_poll(
        window,
        jobs,
        FakeLLM(responses=[CLEANED_NATIVE, VALID_TRANSLATED]),
    )

    assert_reader_ui(window, tab=NATIVE_TAB, contains="Line one", edit_enabled=True)
    assert_native_on_disk(folder, starts_with="# Article")
    assert_cleanup_job(data_root, text_id, status=JobStatus.COMPLETED)


def test_native_tab_shows_failed_cleanup_and_keeps_provisional_file(
    qtbot, tmp_path: Path
) -> None:
    data_root = tmp_path / "LexiFlow"
    _repo, text_id, folder = seed_staged_text(data_root)
    provisional_content = (folder / "native.md").read_text(encoding="utf-8")
    jobs = JobService(data_root)
    window = open_main_window(qtbot, data_root, with_worker=False)
    open_text_in_reader(qtbot, window, text_id)
    window.reader.select_tab(NATIVE_TAB)

    run_worker_loop(
        jobs,
        FakeLLM(response="plain body without heading"),
        data_root=data_root,
    )
    window._poll_background_jobs()

    assert_reader_ui(
        window,
        contains="Generation failed",
        excludes=MESSY_PASTE.splitlines()[0],
        edit_enabled=False,
    )
    assert_native_on_disk(folder, unchanged_from=provisional_content)
    assert_cleanup_job(data_root, text_id, status=JobStatus.FAILED)


def test_status_bar_shows_sanitized_cleanup_failure(qtbot, tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    _repo, text_id, _folder = seed_staged_text(data_root)
    jobs = JobService(data_root)
    window = open_main_window(qtbot, data_root, with_worker=False)
    open_text_in_reader(qtbot, window, text_id)

    run_worker_loop(
        jobs,
        UnavailableLLM("Install llama-server from llama.cpp"),
        data_root=data_root,
    )
    window._poll_background_jobs()

    assert "cleanup failed" in window.statusBar().currentMessage().lower()
    assert "llama-server" in window.statusBar().currentMessage().lower()
    assert_cleanup_job(data_root, text_id, status=JobStatus.FAILED)


def test_translated_tab_pending_while_cleanup_runs(qtbot, tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    _repo, text_id, _folder = seed_staged_text(data_root)
    window = open_main_window(qtbot, data_root, with_worker=False)
    open_text_in_reader(qtbot, window, text_id)
    window.reader.select_tab(TRANSLATED_TAB)

    assert_reader_ui(window, tab=TRANSLATED_TAB, contains="still being generated")


def test_reload_from_disk_keeps_pending_overlay(qtbot, tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    _repo, text_id, _folder = seed_staged_text(data_root)
    window = open_main_window(qtbot, data_root, with_worker=False)
    open_text_in_reader(qtbot, window, text_id)
    window.reader.select_tab(NATIVE_TAB)
    window.reader.reload_from_disk()

    assert "still being generated" in read_pane(window).toPlainText().lower()
    assert "Skip to content" not in read_pane(window).toPlainText()
