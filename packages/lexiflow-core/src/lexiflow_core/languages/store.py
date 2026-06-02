"""Persist target languages on disk."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.config.paths import language_data_dir, language_json_path
from lexiflow_core.languages.catalog import get_language
from lexiflow_core.languages.language_metadata import (
    LanguageMetadata,
    LanguageMetadataError,
    load_language_metadata,
    save_language_metadata,
)


class LanguageStoreError(Exception):
    """Raised when a language store operation is not allowed."""


class LanguageStore:
    def __init__(self, data_root: Path) -> None:
        self._data_root = data_root

    def add_target(self, iso: str) -> None:
        """Register a target language folder and metadata marker."""
        try:
            get_language(iso)
        except KeyError as exc:
            raise LanguageStoreError(f"unknown language: {iso}") from exc
        metadata_path = language_json_path(self._data_root, iso)
        if metadata_path.is_file():
            raise LanguageStoreError(f"target language already exists: {iso}")
        language_data_dir(self._data_root, iso).mkdir(parents=True, exist_ok=True)
        save_language_metadata(metadata_path, LanguageMetadata())

    def has_target(self, iso: str) -> bool:
        return iso in self.list_targets()

    def list_targets(self) -> list[str]:
        if not self._data_root.is_dir():
            return []
        targets: list[str] = []
        for entry in sorted(self._data_root.iterdir()):
            if not entry.is_dir() or entry.name.startswith("."):
                continue
            metadata_path = language_json_path(self._data_root, entry.name)
            if metadata_path.is_file():
                try:
                    load_language_metadata(metadata_path)
                except LanguageMetadataError:
                    continue
                targets.append(entry.name)
        return targets
