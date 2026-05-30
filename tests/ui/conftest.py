"""pytest-qt hooks for UI tests."""

from __future__ import annotations

from collections.abc import Callable

import pytest
from PySide6.QtWidgets import QApplication, QMessageBox


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


@pytest.fixture(autouse=True)
def _cleanup_onboarding_bootstrap_threads() -> None:
    """Stop bootstrap worker threads so later tests can use the Qt event loop."""
    yield
    from lexiflow_ui.onboarding.wizard import OnboardingWizard

    app = QApplication.instance()
    if app is None:
        return
    for widget in QApplication.topLevelWidgets():
        if isinstance(widget, OnboardingWizard):
            widget.bootstrap_page._stop_worker()
    app.processEvents()
