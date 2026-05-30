"""Duplicate detection by source URL."""

from __future__ import annotations

from uuid import UUID

from lexiflow_core.library.index import LibraryIndex


class DuplicateChecker:
    def __init__(self, index: LibraryIndex) -> None:
        self._index = index

    def find_duplicate(
        self,
        *,
        target_language: str,
        source_url: str | None,
    ) -> UUID | None:
        normalized_url = source_url.strip() if source_url is not None else None
        if not normalized_url:
            return None
        return self._index.find_by_source_url(target_language, normalized_url)
