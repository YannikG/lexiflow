"""Duplicate detection by source URL or content fingerprint."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

from lexiflow_core.config.paths import meta_path
from lexiflow_core.library.content_fingerprint import content_fingerprint
from lexiflow_core.library.index import LibraryIndex
from lexiflow_core.library.text_metadata import load_text_metadata


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
        for record in self._index.list_by_lang(target_language):
            folder = Path(record.folder)
            meta_file = meta_path(folder)
            if not meta_file.is_file():
                continue
            metadata = load_text_metadata(meta_file)
            if metadata.content_fingerprint == candidate:
                return record.id
        return None
