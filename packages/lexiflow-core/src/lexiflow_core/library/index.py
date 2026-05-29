"""SQLite-backed library index for sidebar listing."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from lexiflow_core.config.paths import index_db_path, meta_path, text_dir
from lexiflow_core.db.database_path import ensure_database_parent
from lexiflow_core.db.migration_loader import bundled_migrations_dir
from lexiflow_core.db.migrations import MigrationRunner
from lexiflow_core.library.group_registry import GroupNotFoundError, GroupRegistry
from lexiflow_core.library.models import TextRecord
from lexiflow_core.library.text_metadata import (
    TextMetadataError,
    load_text_metadata,
    metadata_to_record,
)


class IndexOutOfSyncError(Exception):
    """Raised when an indexed row cannot be materialized into a record."""


def ensure_library_index(data_root: Path) -> Path:
    """Apply index migrations and return the database path."""
    db_path = index_db_path(data_root)
    ensure_database_parent(db_path)
    MigrationRunner().migrate(db_path, bundled_migrations_dir())
    return db_path


class LibraryIndex:
    def __init__(self, data_root: Path) -> None:
        self._data_root = data_root
        self._db_path = index_db_path(data_root)

    def upsert_text(self, record: TextRecord) -> None:
        """Insert or update a text entry in the index."""
        connection = self._connect()
        try:
            self._upsert_on_connection(connection, record)
            connection.commit()
        finally:
            connection.close()

    def remove_from_index(self, text_id: UUID) -> None:
        """Remove a text from the index."""
        connection = self._connect()
        try:
            connection.execute("DELETE FROM texts WHERE id = ?", (str(text_id),))
            connection.commit()
        finally:
            connection.close()

    def get_by_id(self, text_id: UUID) -> TextRecord | None:
        """Return an indexed text by id."""
        connection = self._connect()
        try:
            row = connection.execute(
                """
                SELECT id, lang, group_display_name, group_folder_slug,
                       title, text_slug, native_language, source_url,
                       variants, created_at, updated_at
                FROM texts
                WHERE id = ?
                """,
                (str(text_id),),
            ).fetchone()
        finally:
            connection.close()
        if row is None:
            return None
        return self._record_from_index_row(row)

    def list_by_lang(self, lang: str) -> list[TextRecord]:
        """Return all indexed texts for a target language."""
        connection = self._connect()
        try:
            rows = connection.execute(
                """
                SELECT id, lang, group_display_name, group_folder_slug,
                       title, text_slug, native_language, source_url,
                       variants, created_at, updated_at
                FROM texts
                WHERE lang = ?
                ORDER BY group_display_name COLLATE NOCASE, title COLLATE NOCASE
                """,
                (lang,),
            ).fetchall()
        finally:
            connection.close()

        return [self._record_from_index_row(row) for row in rows]

    def find_by_source_url(self, lang: str, source_url: str) -> UUID | None:
        """Return a text id with the same source URL in a target language, if any."""
        connection = self._connect()
        try:
            row = connection.execute(
                """
                SELECT id
                FROM texts
                WHERE lang = ? AND source_url = ?
                LIMIT 1
                """,
                (lang, source_url),
            ).fetchone()
        finally:
            connection.close()
        if row is None:
            return None
        return UUID(str(row[0]))

    def rebuild_from_disk(self, data_root: Path | None = None) -> int:
        """Rescan disk and rebuild the index. Read-only on text metadata."""
        root = data_root if data_root is not None else self._data_root
        connection = self._connect()
        try:
            connection.execute("DELETE FROM texts")
            count = 0
            for lang_dir in sorted(root.iterdir()):
                if not lang_dir.is_dir() or lang_dir.name.startswith("."):
                    continue
                lang = lang_dir.name
                registry = GroupRegistry(root, lang)
                for group_folder in sorted(lang_dir.iterdir()):
                    if not group_folder.is_dir() or group_folder.name == ".data":
                        continue
                    folder_slug = group_folder.name
                    for text_folder in sorted(group_folder.iterdir()):
                        if not text_folder.is_dir():
                            continue
                        meta_file = meta_path(text_folder)
                        if not meta_file.is_file():
                            continue
                        try:
                            metadata = load_text_metadata(meta_file)
                        except TextMetadataError:
                            continue
                        group_display = self._index_group_display(
                            registry, folder_slug, metadata.group
                        )
                        record = metadata_to_record(
                            metadata,
                            group_folder_slug=folder_slug,
                            text_slug=text_folder.name,
                            folder=str(text_folder),
                        )
                        if record.group != group_display:
                            record = TextRecord(
                                id=record.id,
                                title=record.title,
                                group=group_display,
                                group_folder_slug=record.group_folder_slug,
                                text_slug=record.text_slug,
                                target_language=record.target_language,
                                native_language=record.native_language,
                                variants=record.variants,
                                source_url=record.source_url,
                                created_at=record.created_at,
                                updated_at=record.updated_at,
                                folder=record.folder,
                            )
                        self._upsert_on_connection(connection, record)
                        count += 1
            connection.commit()
            return count
        finally:
            connection.close()

    def _index_group_display(
        self, registry: GroupRegistry, folder_slug: str, metadata_group: str
    ) -> str:
        try:
            return registry.display_name_for_folder(folder_slug)
        except GroupNotFoundError:
            registry.ensure_for_folder(folder_slug, metadata_group)
            return metadata_group

    def _upsert_on_connection(
        self, connection: sqlite3.Connection, record: TextRecord
    ) -> None:
        connection.execute(
            """
            INSERT INTO texts (
                id, lang, group_display_name, group_folder_slug,
                title, text_slug, native_language, source_url,
                variants, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                lang = excluded.lang,
                group_display_name = excluded.group_display_name,
                group_folder_slug = excluded.group_folder_slug,
                title = excluded.title,
                text_slug = excluded.text_slug,
                native_language = excluded.native_language,
                source_url = excluded.source_url,
                variants = excluded.variants,
                created_at = excluded.created_at,
                updated_at = excluded.updated_at
            """,
            self._row_from_record(record),
        )

    def _row_from_record(self, record: TextRecord) -> tuple[Any, ...]:
        return (
            str(record.id),
            record.target_language,
            record.group,
            record.group_folder_slug,
            record.title,
            record.text_slug,
            record.native_language,
            record.source_url,
            json.dumps(list(record.variants)),
            record.created_at.isoformat(),
            record.updated_at.isoformat(),
        )

    def _connect(self) -> sqlite3.Connection:
        from lexiflow_core.db.connection import connect_sqlite

        return connect_sqlite(self._db_path)

    def _record_from_index_row(
        self, row: sqlite3.Row | tuple[object, ...]
    ) -> TextRecord:
        (
            text_id,
            lang,
            group_display,
            group_slug,
            title,
            text_slug,
            native_language,
            source_url,
            variants_json,
            created_at,
            updated_at,
        ) = row
        folder = text_dir(self._data_root, str(lang), str(group_slug), str(text_slug))
        try:
            variants_list = json.loads(str(variants_json))
        except json.JSONDecodeError as exc:
            raise IndexOutOfSyncError(
                f"invalid variants JSON for text {text_id}"
            ) from exc
        if not isinstance(variants_list, list):
            raise IndexOutOfSyncError(f"invalid variants for text {text_id}")
        return TextRecord(
            id=UUID(str(text_id)),
            title=str(title),
            group=str(group_display),
            group_folder_slug=str(group_slug),
            text_slug=str(text_slug),
            target_language=str(lang),
            native_language=str(native_language),
            variants=tuple(str(item) for item in variants_list),
            source_url=str(source_url) if source_url is not None else None,
            created_at=datetime.fromisoformat(str(created_at)),
            updated_at=datetime.fromisoformat(str(updated_at)),
            folder=str(folder),
        )
