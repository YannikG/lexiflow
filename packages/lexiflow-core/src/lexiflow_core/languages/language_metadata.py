"""Load and persist per-target-language metadata."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from lexiflow_core.languages.models import CEFRLevel


class LanguageMetadataError(Exception):
    """Raised when language metadata is invalid or cannot be read."""


@dataclass(frozen=True)
class LanguageMetadata:
    user_level: CEFRLevel

    def to_dict(self) -> dict[str, Any]:
        return {"user_level": self.user_level.value}


def save_language_metadata(path: Path, metadata: LanguageMetadata) -> None:
    if not path.parent.is_dir():
        raise LanguageMetadataError(
            f"language metadata directory does not exist: {path.parent}"
        )
    path.write_text(
        json.dumps(metadata.to_dict(), indent=2) + "\n",
        encoding="utf-8",
    )


def load_language_metadata(path: Path) -> LanguageMetadata:
    if not path.is_file():
        raise LanguageMetadataError(f"missing language metadata: {path}")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise LanguageMetadataError(f"invalid language metadata: {path}") from exc
    if not isinstance(raw, dict):
        raise LanguageMetadataError(f"invalid language metadata: {path}")
    level_value = raw.get("user_level")
    if not isinstance(level_value, str):
        raise LanguageMetadataError("missing user_level in language metadata")
    try:
        user_level = CEFRLevel(level_value)
    except ValueError as exc:
        raise LanguageMetadataError(f"invalid user_level: {level_value}") from exc
    return LanguageMetadata(user_level=user_level)
