"""Tests for target language setup orchestration."""

from __future__ import annotations

from pathlib import Path

import pytest
from lexiflow_core.config.paths import language_json_path
from lexiflow_core.config.settings import Settings
from lexiflow_core.config.settings_store import SettingsStore
from lexiflow_core.jobs.models import JobType
from lexiflow_core.jobs.service import JobService
from lexiflow_core.languages.models import CEFRLevel
from lexiflow_core.languages.setup import (
    LanguageSetupError,
    add_target_with_spacy_download,
    complete_language_onboarding,
    finalize_onboarding,
)
from lexiflow_core.languages.store import LanguageStore


def test_add_target_with_spacy_download_enqueues_job(tmp_path: Path) -> None:
    data_root = tmp_path / "library"

    add_target_with_spacy_download(data_root, "es", CEFRLevel.A2)

    jobs = JobService(data_root).list_jobs()
    assert len(jobs) == 1
    assert jobs[0].job_type == JobType.DOWNLOAD_SPACY
    assert jobs[0].payload == {"iso": "es"}
    assert LanguageStore(data_root).list_targets() == ["es"]


def test_add_target_with_spacy_download_rolls_back_on_enqueue_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    data_root = tmp_path / "library"

    def fail_enqueue(self: JobService, request: object) -> object:
        raise RuntimeError("queue unavailable")

    monkeypatch.setattr(JobService, "enqueue", fail_enqueue)

    with pytest.raises(LanguageSetupError, match="failed to enqueue"):
        add_target_with_spacy_download(data_root, "es", CEFRLevel.A2)

    assert LanguageStore(data_root).list_targets() == []
    assert not language_json_path(data_root, "es").exists()


def test_complete_language_onboarding_persists_settings(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    data_root = tmp_path / "library"
    store = SettingsStore(config_dir=config_dir)
    settings = Settings(data_root=data_root, onboarding_complete=False)

    updated = complete_language_onboarding(
        data_root=data_root,
        settings_store=store,
        settings=settings,
        native_language="en",
        target_language="es",
        level=CEFRLevel.A2,
    )

    loaded = store.load()
    assert loaded == updated
    assert loaded.onboarding_complete is False
    assert loaded.native_language == "en"
    assert loaded.active_target_language == "es"
    assert JobService(data_root).list_jobs()[0].job_type == JobType.DOWNLOAD_SPACY


def test_finalize_onboarding_sets_complete_flag(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    store = SettingsStore(config_dir=config_dir)
    settings = Settings(
        native_language="en",
        active_target_language="es",
        onboarding_complete=False,
    )

    final = finalize_onboarding(settings_store=store, settings=settings)

    assert final.onboarding_complete is True
    assert store.load().onboarding_complete is True


def test_onboarding_rerun_with_existing_target(tmp_path: Path) -> None:
    """Re-run after resetting onboarding_complete must not fail on duplicate."""
    config_dir = tmp_path / "config"
    data_root = tmp_path / "library"
    store = SettingsStore(config_dir=config_dir)
    settings = Settings(data_root=data_root, onboarding_complete=False)

    complete_language_onboarding(
        data_root=data_root,
        settings_store=store,
        settings=settings,
        native_language="en",
        target_language="uk",
        level=CEFRLevel.A2,
    )
    finalize_onboarding(settings_store=store, settings=store.load())
    assert store.load().onboarding_complete is True
    assert len(JobService(data_root).list_jobs()) == 1

    reset = Settings(
        data_root=data_root,
        native_language="en",
        active_target_language="uk",
        onboarding_complete=False,
        huggingface_token=store.load().huggingface_token,
        ollama_url=store.load().ollama_url,
    )
    store.save(reset)

    updated = complete_language_onboarding(
        data_root=data_root,
        settings_store=store,
        settings=reset,
        native_language="en",
        target_language="uk",
        level=CEFRLevel.B1,
    )
    final = finalize_onboarding(settings_store=store, settings=updated)

    loaded = store.load()
    assert final.onboarding_complete is True
    assert loaded.onboarding_complete is True
    assert loaded.native_language == "en"
    assert loaded.active_target_language == "uk"
    assert LanguageStore(data_root).get_user_level("uk") == CEFRLevel.B1
    assert len(JobService(data_root).list_jobs()) == 1


def test_complete_language_onboarding_rolls_back_on_settings_save_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    config_dir = tmp_path / "config"
    data_root = tmp_path / "library"
    store = SettingsStore(config_dir=config_dir)
    settings = Settings(data_root=data_root)

    def fail_save(self: SettingsStore, _settings: Settings) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(SettingsStore, "save", fail_save)

    with pytest.raises(LanguageSetupError, match="failed to save onboarding settings"):
        complete_language_onboarding(
            data_root=data_root,
            settings_store=store,
            settings=settings,
            native_language="en",
            target_language="es",
            level=CEFRLevel.A2,
        )

    assert LanguageStore(data_root).list_targets() == []
    assert store.load().onboarding_complete is False
