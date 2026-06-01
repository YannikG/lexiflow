"""Shared helpers for staged-generation UI tests."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

from lexiflow_core.config.paths import variant_path
from lexiflow_core.config.settings import Settings
from lexiflow_core.jobs.models import JobRequest, JobStatus, JobType
from lexiflow_core.jobs.service import JobService
from lexiflow_core.library.index import LibraryIndex
from lexiflow_core.library.library_coordinator import LibraryCoordinator
from lexiflow_core.library.models import CreateTextRequest
from lexiflow_core.library.text_repository import TextRepository
from lexiflow_ui.main_window import MainWindow
from lexiflow_ui.worker_supervisor import WorkerSupervisor
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QListWidget, QTextBrowser

MESSY_PASTE = "Skip to content\nHome\nAbout\nLine one\n\nLine two"
CLEANED_NATIVE = "# Article\n\nLine one\n\nLine two"
VALID_TRANSLATED = "# Traducción\n\nCuerpo traducido."


def seed_staged_text(
    data_root: Path,
    *,
    paste: str = MESSY_PASTE,
    enqueue_cleanup: bool = True,
) -> tuple[TextRepository, UUID, Path]:
    coordinator, index = LibraryCoordinator.open(data_root)
    del coordinator
    repo = TextRepository(data_root, index)
    record = repo.create_text(
        CreateTextRequest(
            title="Article",
            group="News",
            target_language="es",
            native_language="en",
            body=paste,
        )
    )
    if enqueue_cleanup:
        JobService(data_root).enqueue(
            JobRequest(
                job_type=JobType.CLEANUP,
                payload={
                    "text_id": str(record.id),
                    "raw_paste": paste,
                    "source_route": "native",
                },
            )
        )
    return repo, record.id, Path(record.folder)


def read_pane(window: MainWindow) -> QTextBrowser:
    pane = window.reader.findChild(QTextBrowser, "reader_read_pane")
    assert pane is not None
    return pane


def assert_reader_ui(
    window: MainWindow,
    *,
    contains: str | None = None,
    excludes: str | None = None,
    tab: str | None = None,
    edit_enabled: bool | None = None,
) -> None:
    if tab is not None:
        assert window.reader.active_tab_id == tab
    text = read_pane(window).toPlainText()
    if contains is not None:
        assert contains in text
    if excludes is not None:
        assert excludes not in text
    if edit_enabled is not None:
        assert window.reader._edit_button.isEnabled() is edit_enabled


def assert_native_on_disk(
    folder: Path,
    *,
    equals: str | None = None,
    starts_with: str | None = None,
    unchanged_from: str | None = None,
) -> None:
    content = variant_path(folder, "native").read_text(encoding="utf-8")
    if equals is not None:
        assert content == equals
    if starts_with is not None:
        assert content.startswith(starts_with)
    if unchanged_from is not None:
        assert content == unchanged_from


def assert_cleanup_job(
    data_root: Path,
    text_id: UUID,
    *,
    status: JobStatus,
    error_contains: str | None = None,
) -> None:
    jobs = [
        job
        for job in JobService(data_root).list_jobs()
        if job.job_type == JobType.CLEANUP
        and job.payload.get("text_id") == str(text_id)
    ]
    assert len(jobs) == 1
    assert jobs[0].status == status
    if error_contains is not None:
        assert jobs[0].error_message is not None
        assert error_contains.lower() in jobs[0].error_message.lower()


def open_main_window(qtbot, data_root: Path, *, with_worker: bool = True) -> MainWindow:
    if with_worker:
        supervisor = WorkerSupervisor(data_root=data_root)
    else:
        import sys

        from tests.ui.fakes import FakeProcess

        FakeProcess.instances.clear()
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
            onboarding_complete=True,
        ),
        data_root=data_root,
    )
    qtbot.addWidget(window)
    window.show()
    qtbot.waitExposed(window)
    return window


def open_text_in_reader(qtbot, window: MainWindow, text_id: UUID) -> None:
    index = LibraryIndex(window.data_root)
    row = next(
        i for i, record in enumerate(index.list_by_lang("es")) if record.id == text_id
    )
    sidebar_list = window.sidebar.findChild(QListWidget, "sidebar_text_list")
    assert sidebar_list is not None
    item = sidebar_list.item(row)
    assert item is not None
    rect = sidebar_list.visualItemRect(item)
    qtbot.mouseClick(
        sidebar_list.viewport(),
        Qt.MouseButton.LeftButton,
        pos=rect.center(),
    )
    qtbot.wait(50)


def run_worker_and_poll(window: MainWindow, jobs: JobService, llm) -> None:
    from lexiflow_core.jobs.runner import run_worker_loop

    run_worker_loop(jobs, llm, data_root=window.data_root)
    window._poll_background_jobs()
