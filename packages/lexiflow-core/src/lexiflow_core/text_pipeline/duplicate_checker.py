"""Duplicate detection by source URL or content fingerprint."""

from __future__ import annotations

from uuid import UUID

from lexiflow_core.library.content_fingerprint import content_fingerprint
from lexiflow_core.library.index import LibraryIndex


class DuplicateChecker:
    def __init__(self, index: LibraryIndex) -> None:
        self._index = index

    def find_duplicate(
        self,
        *,
        target_language: str,
        pasted_content: str,
        source_url: str | None,
    ) -> UUID | None:
        if source_url:
            match = self._index.find_by_source_url(target_language, source_url)
            if match is not None:
                return match

        candidate = content_fingerprint(pasted_content)
        return self._index.find_by_content_fingerprint(target_language, candidate)
