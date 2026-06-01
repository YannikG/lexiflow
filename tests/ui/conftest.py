"""pytest-qt hooks for UI tests."""

from __future__ import annotations

from collections.abc import Callable, Iterator

import pytest
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
