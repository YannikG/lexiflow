"""Tests for add-text duplicate detection by source URL."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from lexiflow_core.library.index import LibraryIndex, ensure_library_index
from lexiflow_core.library.models import TextRecord
from lexiflow_core.text_pipeline.duplicate_checker import DuplicateChecker


def _indexed_record(
    data_root: Path,
    *,
    title: str,
    source_url: str | None,
    fingerprint: str | None = None,
) -> TextRecord:
    now = __import__("datetime").datetime.now(__import__("datetime").UTC)
    return TextRecord(
        id=uuid4(),
        title=title,
        group="News",
        group_folder_slug="news",
        text_slug="text-abc",
        target_language="es",
        native_language="en",
        variants=("native",),
        created_at=now,
        updated_at=now,
        source_url=source_url,
        content_fingerprint=fingerprint,
        folder=str(data_root / "library" / "es" / "news" / "text-abc"),
    )


def test_find_duplicate_returns_none_without_source_url(tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    ensure_library_index(data_root)
    index = LibraryIndex(data_root)
    checker = DuplicateChecker(index)

    match = checker.find_duplicate(
        target_language="es",
        source_url=None,
    )

    assert match is None


def test_find_duplicate_returns_none_for_blank_source_url(tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    ensure_library_index(data_root)
    index = LibraryIndex(data_root)
    checker = DuplicateChecker(index)

    match = checker.find_duplicate(
        target_language="es",
        source_url="   ",
    )

    assert match is None


def test_find_duplicate_matches_existing_source_url(tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    ensure_library_index(data_root)
    index = LibraryIndex(data_root)
    record = _indexed_record(
        data_root,
        title="Existing",
        source_url="https://example.com/article",
    )
    index.upsert_text(record)
    checker = DuplicateChecker(index)

    match = checker.find_duplicate(
        target_language="es",
        source_url="https://example.com/article",
    )

    assert match == record.id


def test_find_duplicate_ignores_content_fingerprint_without_source_url(
    tmp_path: Path,
) -> None:
    data_root = tmp_path / "LexiFlow"
    ensure_library_index(data_root)
    index = LibraryIndex(data_root)
    fingerprint = "deadbeef"
    record = _indexed_record(
        data_root,
        title="Existing",
        source_url=None,
        fingerprint=fingerprint,
    )
    index.upsert_text(record)
    checker = DuplicateChecker(index)

    match = checker.find_duplicate(
        target_language="es",
        source_url=None,
    )

    assert match is None
