"""Load and persist per-target-language metadata."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

LANGUAGE_METADATA_VERSION = 1


class LanguageMetadataError(Exception):
    """Raised when language metadata is invalid or cannot be read."""


@dataclass(frozen=True)
class LanguageMetadata:
    """Marker that a target language folder is registered."""

    version: int = LANGUAGE_METADATA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {"version": self.version}


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
    # Legacy files may contain only user_level; treat as registered target.
    version = raw.get("version", LANGUAGE_METADATA_VERSION)
    if not isinstance(version, int):
        if "user_level" in raw:
            return LanguageMetadata(version=LANGUAGE_METADATA_VERSION)
        raise LanguageMetadataError("invalid version in language metadata")
    return LanguageMetadata(version=version)
