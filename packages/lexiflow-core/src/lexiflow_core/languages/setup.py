"""Orchestrate target-language setup commands."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.config.paths import (
    language_data_dir,
    language_data_root,
    language_json_path,
)
from lexiflow_core.config.settings import Settings
from lexiflow_core.config.settings_store import SettingsStore
from lexiflow_core.jobs.models import JobRequest, JobType
from lexiflow_core.jobs.service import JobService
from lexiflow_core.languages.models import CEFRLevel
from lexiflow_core.languages.store import LanguageStore


class LanguageSetupError(Exception):
    """Raised when target-language setup cannot complete."""


def _discard_new_target(data_root: Path, iso: str) -> None:
    """Remove on-disk artifacts from a failed first-time target add."""
    metadata_path = language_json_path(data_root, iso)
    if metadata_path.is_file():
        metadata_path.unlink()
    data_dir = language_data_dir(data_root, iso)
    if data_dir.is_dir() and not any(data_dir.iterdir()):
        data_dir.rmdir()
    lang_root = language_data_root(data_root, iso)
    if lang_root.is_dir() and not any(lang_root.iterdir()):
        lang_root.rmdir()


def add_target_with_spacy_download(data_root: Path, iso: str, level: CEFRLevel) -> None:
    """Add a target language and enqueue its spaCy pack download."""
    store = LanguageStore(data_root)
    store.add_target(iso, level)
    try:
        JobService(data_root).enqueue(
            JobRequest(
                job_type=JobType.DOWNLOAD_SPACY,
                payload={"iso": iso},
            )
        )
    except Exception as exc:
        _discard_new_target(data_root, iso)
        raise LanguageSetupError(f"failed to enqueue spaCy download for {iso}") from exc


def complete_language_onboarding(
    *,
    data_root: Path,
    settings_store: SettingsStore,
    settings: Settings,
    native_language: str,
    target_language: str,
    level: CEFRLevel,
) -> Settings:
    """Apply first-run language setup and persist global settings."""
    add_target_with_spacy_download(data_root, target_language, level)
    updated = Settings(
        data_root=settings.data_root,
        native_language=native_language,
        active_target_language=target_language,
        onboarding_complete=True,
        ollama_url=settings.ollama_url,
        llm_enabled=settings.llm_enabled,
        theme=settings.theme,
    )
    try:
        settings_store.save(updated)
    except Exception as exc:
        _discard_new_target(data_root, target_language)
        raise LanguageSetupError("failed to save onboarding settings") from exc
    return updated
