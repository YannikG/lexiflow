"""pytest-qt hooks for UI tests."""

from __future__ import annotations

from collections.abc import Callable, Iterator

import pytest
from lexiflow_ui.main_window import MainWindow
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QMessageBox


@pytest.fixture
def restore_app_stylesheet() -> Iterator[None]:
    """Clear QApplication stylesheet after tests that apply global UI theme."""
    yield
    app = QApplication.instance()
    if app is not None:
        app.setStyleSheet("")


@pytest.fixture(autouse=True)
def _native_runtime_ready(monkeypatch: pytest.MonkeyPatch) -> None:
    def operational(settings):  # noqa: ANN001
        return True, None

    monkeypatch.setattr(
        "lexiflow_core.llm.llama_server.native_llm_operational",
        operational,
    )
    monkeypatch.setattr(
        "lexiflow_ui.onboarding.llm_config_page.native_llm_operational",
        operational,
    )


@pytest.fixture(autouse=True)
def _suppress_worker_crash_dialog(monkeypatch: pytest.MonkeyPatch) -> None:
    """Avoid modal worker-restart prompts during test teardown."""
    monkeypatch.setattr(
        "lexiflow_ui.main_window.window.MainWindow._on_worker_crashed",
        lambda _self, _exit_code: None,
    )


@pytest.fixture(autouse=True)
def _allow_quit_without_modal(monkeypatch: pytest.MonkeyPatch) -> None:
    """Close MainWindow in tests without blocking on the quit confirmation dialog."""

    def _confirm(
        _parent,
        *,
        job_service,
        worker_supervisor,
        llama_supervisor,
        embed_supervisor=None,
    ) -> bool:  # noqa: ANN001
        del job_service, _parent
        if embed_supervisor is not None:
            embed_supervisor.shutdown(wait=False)
        if llama_supervisor is not None:
            llama_supervisor.shutdown(wait=False)
        worker_supervisor.shutdown(wait=False)
        return True

    for target in (
        "lexiflow_ui.shutdown_flow.confirm_application_quit",
        "lexiflow_ui.main_window.window.confirm_application_quit",
        "lexiflow_ui.dialogs.settings_dialog.confirm_application_quit",
    ):
        monkeypatch.setattr(target, _confirm)


@pytest.fixture(autouse=True)
def _allow_leave_dirty_editors(monkeypatch: pytest.MonkeyPatch) -> None:
    """Let MainWindow.close() proceed without blocking on unsaved reader edits."""
    monkeypatch.setattr(
        "lexiflow_ui.unsaved_changes.confirm_leave_dirty_editors",
        lambda *_args, **_kwargs: True,
    )


@pytest.fixture(autouse=True)
def _stop_ui_timers_after_test() -> Iterator[None]:
    """Prevent background QTimers from keeping pytest alive after UI tests."""
    yield
    app = QApplication.instance()
    if app is None:
        return
    for widget in list(app.topLevelWidgets()):
        if isinstance(widget, MainWindow):
            widget._job_poll_timer.stop()
            widget._supervisor.shutdown(wait=False)
            if widget._llama_supervisor is not None:
                widget._llama_supervisor.shutdown(wait=False)
            if widget._embed_supervisor is not None:
                widget._embed_supervisor.shutdown(wait=False)
        widget.close()
    for timer in app.findChildren(QTimer):
        timer.stop()
    app.processEvents()


@pytest.fixture(autouse=True)
def _non_blocking_unsaved_prompt(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prevent modal unsaved-changes dialogs from blocking unattended test runs."""
    monkeypatch.setattr(
        "lexiflow_ui.unsaved_changes.prompt_discard_unsaved_changes",
        lambda *_args, **_kwargs: QMessageBox.StandardButton.Cancel,
    )


@pytest.fixture
def stub_discard_unsaved_prompt(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "lexiflow_ui.unsaved_changes.prompt_discard_unsaved_changes",
        lambda *_args, **_kwargs: QMessageBox.StandardButton.Discard,
    )


@pytest.fixture
def track_unsaved_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> Callable[[], int]:
    calls = 0

    def _prompt(*_args, **_kwargs) -> QMessageBox.StandardButton:
        nonlocal calls
        calls += 1
        return QMessageBox.StandardButton.Cancel

    monkeypatch.setattr(
        "lexiflow_ui.unsaved_changes.prompt_discard_unsaved_changes",
        _prompt,
    )
    return lambda: calls
