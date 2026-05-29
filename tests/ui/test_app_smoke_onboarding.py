"""Regression: app smoke must not break later onboarding Qt tests."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.config.settings import Settings
from lexiflow_core.config.settings_store import SettingsStore
from lexiflow_core.models.download import FakeModelDownloader
from lexiflow_ui.onboarding.wizard import OnboardingWizard

from tests.ui import test_app_smoke
from tests.ui.test_onboarding import (
    FakeSystemInfo,
    _advance_wizard_to_finish,
    _make_model_store,
)


def test_app_smoke_then_onboarding_rerun(qtbot, monkeypatch, tmp_path: Path) -> None:
    """app.quit() in smoke used to stall bootstrap threads in following tests."""
    test_app_smoke.test_app_smoke(qtbot, monkeypatch, tmp_path)

    config_dir = tmp_path / "config"
    data_root = tmp_path / "library"
    store = SettingsStore(config_dir=config_dir)
    settings = Settings(data_root=data_root, onboarding_complete=False)
    model_store = _make_model_store(data_root, downloader=FakeModelDownloader())

    wizard = OnboardingWizard(
        data_root=data_root,
        settings_store=store,
        settings=settings,
        system_info=FakeSystemInfo(16 * 1024**3),
        model_store=model_store,
    )
    qtbot.addWidget(wizard)
    wizard.show()
    _advance_wizard_to_finish(wizard, qtbot)
    assert store.load().onboarding_complete is True

    wizard.bootstrap_page._stop_worker()
    wizard.close()
    qtbot.wait(50)
    store.save(
        Settings(
            data_root=data_root,
            native_language="en",
            active_target_language="es",
            onboarding_complete=False,
        )
    )

    wizard_again = OnboardingWizard(
        data_root=data_root,
        settings_store=store,
        settings=store.load(),
        system_info=FakeSystemInfo(16 * 1024**3),
        model_store=model_store,
    )
    qtbot.addWidget(wizard_again)
    wizard_again.show()
    _advance_wizard_to_finish(wizard_again, qtbot)

    assert store.load().onboarding_complete is True
