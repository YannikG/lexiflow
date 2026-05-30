"""Domain models for library texts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class CreateTextRequest:
    title: str
    group: str
    target_language: str
    native_language: str
    body: str = ""
    source_url: str | None = None


@dataclass(frozen=True)
class TextRecord:
    id: UUID
    title: str
    group: str
    group_folder_slug: str
    text_slug: str
    target_language: str
    native_language: str
    variants: tuple[str, ...]
    created_at: datetime
    updated_at: datetime
    source_url: str | None = None
    content_fingerprint: str | None = None
    folder: str = field(default="", compare=False)
