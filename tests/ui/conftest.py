"""pytest-qt hooks for UI tests."""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication


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
