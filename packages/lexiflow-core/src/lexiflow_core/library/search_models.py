"""Models for library search results."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class SearchHit:
    """One library search result scoped to a text variant."""

    text_id: UUID
    title: str
    variant: str
    snippet: str
    match_offset: int | None = None
