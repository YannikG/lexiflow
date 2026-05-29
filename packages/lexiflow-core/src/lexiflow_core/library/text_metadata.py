"""Load, validate, and persist text metadata on disk."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from lexiflow_core.library.models import TextRecord


class TextMetadataError(Exception):
    """Raised when text metadata is invalid or cannot be read."""


_FORBIDDEN_KEYS = frozenset({"level"})


@dataclass(frozen=True)
class TextMetadata:
    id: UUID
    title: str
    group: str
    native_language: str
    target_language: str
    variants: tuple[str, ...]
    source_url: str | None
    content_fingerprint: str | None
    created_at: datetime
    updated_at: datetime

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "id": str(self.id),
            "title": self.title,
            "group": self.group,
            "native_language": self.native_language,
            "target_language": self.target_language,
            "variants": list(self.variants),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        if self.source_url is not None:
            payload["source_url"] = self.source_url
        if self.content_fingerprint is not None:
            payload["content_fingerprint"] = self.content_fingerprint
        return payload


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


def _validate_no_forbidden_keys(raw: dict[str, Any]) -> None:
    forbidden = _FORBIDDEN_KEYS.intersection(raw)
    if forbidden:
        names = ", ".join(sorted(forbidden))
        raise TextMetadataError(f"forbidden metadata keys: {names}")


def parse_text_metadata(raw: dict[str, Any]) -> TextMetadata:
    """Validate and parse a metadata mapping."""
    _validate_no_forbidden_keys(raw)
    required = (
        "id",
        "title",
        "group",
        "native_language",
        "target_language",
        "variants",
        "created_at",
        "updated_at",
    )
    missing = [key for key in required if key not in raw]
    if missing:
        names = ", ".join(missing)
        raise TextMetadataError(f"missing metadata keys: {names}")

    variants_raw = raw["variants"]
    if not isinstance(variants_raw, list) or not all(
        isinstance(item, str) for item in variants_raw
    ):
        raise TextMetadataError("variants must be a list of strings")

    source_url = raw.get("source_url")
    if source_url is not None and not isinstance(source_url, str):
        raise TextMetadataError("source_url must be a string")

    content_fingerprint = raw.get("content_fingerprint")
    if content_fingerprint is not None and not isinstance(content_fingerprint, str):
        raise TextMetadataError("content_fingerprint must be a string")

    try:
        return TextMetadata(
            id=UUID(str(raw["id"])),
            title=str(raw["title"]),
            group=str(raw["group"]),
            native_language=str(raw["native_language"]),
            target_language=str(raw["target_language"]),
            variants=tuple(variants_raw),
            source_url=source_url,
            content_fingerprint=content_fingerprint,
            created_at=_parse_datetime(str(raw["created_at"])),
            updated_at=_parse_datetime(str(raw["updated_at"])),
        )
    except (TypeError, ValueError) as exc:
        raise TextMetadataError("invalid metadata values") from exc


def load_text_metadata(path: Path) -> TextMetadata:
    """Load metadata from a ``meta.json`` file."""
    raw = _read_metadata_mapping(path)
    return parse_text_metadata(raw)


def read_text_id(path: Path) -> UUID | None:
    """Read only the text id from metadata for discovery scans."""
    try:
        raw = _read_metadata_mapping(path)
    except TextMetadataError:
        return None
    text_id = raw.get("id")
    if text_id is None:
        return None
    try:
        return UUID(str(text_id))
    except (TypeError, ValueError):
        return None


def _read_metadata_mapping(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise TextMetadataError(f"metadata file not found: {path}")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TextMetadataError(f"failed to read metadata: {path}") from exc
    if not isinstance(raw, dict):
        raise TextMetadataError(f"invalid metadata format: {path}")
    return raw


def save_text_metadata(path: Path, metadata: TextMetadata) -> None:
    """Write metadata to a ``meta.json`` file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(
            json.dumps(metadata.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        raise TextMetadataError(f"failed to write metadata: {path}") from exc


def metadata_to_record(
    metadata: TextMetadata,
    *,
    group_folder_slug: str,
    text_slug: str,
    folder: str,
) -> TextRecord:
    """Convert parsed metadata into a public text record."""
    return TextRecord(
        id=metadata.id,
        title=metadata.title,
        group=metadata.group,
        group_folder_slug=group_folder_slug,
        text_slug=text_slug,
        target_language=metadata.target_language,
        native_language=metadata.native_language,
        variants=metadata.variants,
        source_url=metadata.source_url,
        created_at=metadata.created_at,
        updated_at=metadata.updated_at,
        folder=folder,
    )
