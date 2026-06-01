"""Minimal vocabulary persistence for simplify and new-word add."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import cast
from uuid import uuid4

from lexiflow_core.config.paths import vocabulary_db_path
from lexiflow_core.db.connection import connect_sqlite
from lexiflow_core.languages.models import CEFRLevel
from lexiflow_core.vectors.setup import ensure_vocabulary_db
from lexiflow_core.vocabulary.models import (
    DifficultyRating,
    NewWordSuggestion,
    VocabularyEntry,
)


class VocabularyStoreError(Exception):
    """Raised when a vocabulary operation is not allowed."""


class VocabularyStore:
    """Read and write vocabulary entries for one target language."""

    def __init__(self, data_root: Path, language_code: str) -> None:
        self._data_root = data_root
        self._language_code = language_code

    def has_lemma(self, lemma: str) -> bool:
        """Return whether a lemma already exists in vocabulary."""
        normalized = lemma.strip().lower()
        if not normalized:
            return False
        connection = self._connect_read()
        if connection is None:
            return False
        try:
            row = self._fetch_one(
                connection,
                "SELECT 1 FROM vocabulary_entries WHERE lemma = ?",
                (normalized,),
            )
        finally:
            connection.close()
        return row is not None

    def list_for_simplify(self) -> tuple[VocabularyEntry, ...]:
        """Return all vocabulary entries for simplify word-mix selection."""
        connection = self._connect_read()
        if connection is None:
            return ()
        try:
            rows = self._fetch_all(
                connection,
                """
                SELECT lemma, translation, explanation, level_when_learned,
                       difficulty_rating, surface_form
                FROM vocabulary_entries
                ORDER BY lemma
                """,
            )
        finally:
            connection.close()
        if rows is None:
            return ()
        return tuple(self._row_to_entry(row) for row in rows)

    def add_from_suggestion(
        self,
        suggestion: NewWordSuggestion,
        *,
        level_when_learned: CEFRLevel | None = None,
    ) -> VocabularyEntry:
        """Add a vocabulary entry from a new-word suggestion."""
        lemma = suggestion.lemma.strip().lower()
        if not lemma:
            raise VocabularyStoreError("lemma must not be empty")
        learned_level = (
            level_when_learned
            if level_when_learned is not None
            else suggestion.suggested_level
        )
        ensure_vocabulary_db(self._data_root, self._language_code)
        if self.has_lemma(lemma):
            raise VocabularyStoreError(f"duplicate lemma: {lemma}")
        now = datetime.now(UTC).isoformat()
        entry = VocabularyEntry(
            lemma=lemma,
            translation=suggestion.gloss.strip(),
            explanation="",
            level_when_learned=learned_level,
            difficulty_rating=DifficultyRating.HARD,
            surface_form=None,
            entry_id=uuid4(),
        )
        connection = connect_sqlite(self._db_path())
        try:
            with connection:
                connection.execute(
                    """
                    INSERT INTO vocabulary_entries(
                        lemma, translation, explanation, level_when_learned,
                        difficulty_rating, surface_form, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        entry.lemma,
                        entry.translation,
                        entry.explanation,
                        entry.level_when_learned.value,
                        entry.difficulty_rating.value,
                        entry.surface_form,
                        now,
                        now,
                    ),
                )
        finally:
            connection.close()
        return entry

    def _db_path(self) -> Path:
        return vocabulary_db_path(self._data_root, self._language_code)

    def _connect_read(self) -> sqlite3.Connection | None:
        path = self._db_path()
        if not path.is_file():
            return None
        return connect_sqlite(path)

    @staticmethod
    def _fetch_one(
        connection: sqlite3.Connection,
        sql: str,
        params: tuple[object, ...],
    ) -> sqlite3.Row | tuple[object, ...] | None:
        try:
            row = cast(
                sqlite3.Row | tuple[object, ...] | None,
                connection.execute(sql, params).fetchone(),
            )
        except sqlite3.OperationalError:
            return None
        if row is None:
            return None
        return row

    @staticmethod
    def _fetch_all(
        connection: sqlite3.Connection,
        sql: str,
        params: tuple[object, ...] = (),
    ) -> list[sqlite3.Row | tuple[object, ...]] | None:
        try:
            return cast(
                list[sqlite3.Row | tuple[object, ...]],
                connection.execute(sql, params).fetchall(),
            )
        except sqlite3.OperationalError:
            return None

    @staticmethod
    def _row_to_entry(row: sqlite3.Row | tuple[object, ...]) -> VocabularyEntry:
        (
            lemma,
            translation,
            explanation,
            level_when_learned,
            difficulty_rating,
            surface_form,
        ) = row
        return VocabularyEntry(
            lemma=str(lemma),
            translation=str(translation),
            explanation=str(explanation),
            level_when_learned=CEFRLevel(str(level_when_learned)),
            difficulty_rating=DifficultyRating(str(difficulty_rating)),
            surface_form=str(surface_form) if surface_form is not None else None,
        )
