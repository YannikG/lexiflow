"""Vocabulary persistence for study, browse, and simplify."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from lexiflow_core.config.paths import vocabulary_db_path
from lexiflow_core.db.connection import connect_sqlite
from lexiflow_core.languages.models import CEFRLevel
from lexiflow_core.vectors.setup import ensure_vocabulary_db
from lexiflow_core.vectors.sqlite_vec import load_sqlite_vec
from lexiflow_core.vocabulary.fluency import next_difficulty
from lexiflow_core.vocabulary.lemma_form import normalize_lemma, parse_word_category
from lexiflow_core.vocabulary.models import (
    DifficultyRating,
    NewWordSuggestion,
    VocabularyEntry,
    VocabularySort,
    WordCategory,
)


class VocabularyStoreError(Exception):
    """Raised when a vocabulary operation is not allowed."""


@dataclass(frozen=True)
class DeletedVocabularyEntry:
    """Snapshot of a row removed for delete-undo."""

    lemma: str
    translation: str
    explanation: str
    level_when_learned: str
    difficulty_rating: str
    word_category: str
    surface_form: str | None
    created_at: str
    updated_at: str


_SORT_ORDER: dict[VocabularySort, str] = {
    VocabularySort.RECENT: "created_at DESC, lemma ASC",
    VocabularySort.ALPHABETICAL: "lemma COLLATE NOCASE ASC",
    VocabularySort.LEVEL: f"""
        CASE level_when_learned
            {
        " ".join(
            f"WHEN '{level.value}' THEN {index}"
            for index, level in enumerate(CEFRLevel)
        )
    }
            ELSE 99
        END ASC, lemma COLLATE NOCASE ASC
    """,
    VocabularySort.DIFFICULTY: """
        CASE difficulty_rating
            WHEN 'hard' THEN 0
            WHEN 'well' THEN 1
            WHEN 'fluent' THEN 2
            WHEN 'easy' THEN 3
            ELSE 4
        END ASC, lemma COLLATE NOCASE ASC
    """,
}

_SELECT_COLUMNS = """
    lemma, translation, explanation, level_when_learned,
    difficulty_rating, word_category, surface_form
"""


class VocabularyStore:
    """Read and write vocabulary entries for one target language."""

    def __init__(self, data_root: Path, language_code: str) -> None:
        self._data_root = data_root
        self._language_code = language_code

    @property
    def language_code(self) -> str:
        return self._language_code

    def has_lemma(self, lemma: str) -> bool:
        """Return whether a lemma already exists in vocabulary."""
        return self._resolve_lemma(lemma) is not None

    def get(self, lemma: str) -> VocabularyEntry | None:
        """Return one vocabulary entry by lemma."""
        resolved = self._resolve_lemma(lemma)
        if resolved is None:
            return None
        connection = self._connect_read()
        if connection is None:
            return None
        try:
            row = self._fetch_one(
                connection,
                f"SELECT {_SELECT_COLUMNS} FROM vocabulary_entries WHERE lemma = ?",
                (resolved,),
            )
        finally:
            connection.close()
        if row is None:
            return None
        return self._row_to_entry(row)

    def list_entries(
        self, *, sort: VocabularySort = VocabularySort.RECENT
    ) -> tuple[VocabularyEntry, ...]:
        """Return vocabulary entries in the requested sort order."""
        connection = self._connect_read()
        if connection is None:
            return ()
        order = _SORT_ORDER[sort]
        try:
            rows = self._fetch_all(
                connection,
                f"""
                SELECT {_SELECT_COLUMNS}
                FROM vocabulary_entries
                ORDER BY {order}
                """,
            )
        finally:
            connection.close()
        if rows is None:
            return ()
        return tuple(self._row_to_entry(row) for row in rows)

    def list_for_simplify(self) -> tuple[VocabularyEntry, ...]:
        """Return all vocabulary entries for simplify word-mix selection."""
        return self.list_entries(sort=VocabularySort.ALPHABETICAL)

    def add_from_suggestion(
        self,
        suggestion: NewWordSuggestion,
        *,
        level_when_learned: CEFRLevel | None = None,
    ) -> VocabularyEntry:
        """Add a vocabulary entry from a new-word suggestion."""
        lemma = normalize_lemma(
            suggestion.lemma,
            language_code=self._language_code,
            category=suggestion.word_category,
        )
        if not lemma:
            raise VocabularyStoreError("lemma must not be empty")
        learned_level = (
            level_when_learned
            if level_when_learned is not None
            else suggestion.suggested_level
        )
        return self.add_entry(
            lemma=lemma,
            translation=suggestion.gloss.strip(),
            explanation=suggestion.explanation.strip(),
            level_when_learned=learned_level,
            word_category=suggestion.word_category,
            surface_form=None,
        )

    def add_entry(
        self,
        *,
        lemma: str,
        translation: str,
        explanation: str = "",
        level_when_learned: CEFRLevel,
        difficulty_rating: DifficultyRating = DifficultyRating.HARD,
        word_category: WordCategory = WordCategory.OTHER,
        surface_form: str | None = None,
    ) -> VocabularyEntry:
        """Insert a new vocabulary entry."""
        normalized = normalize_lemma(
            lemma,
            language_code=self._language_code,
            category=word_category,
        )
        if not normalized:
            raise VocabularyStoreError("lemma must not be empty")
        if not translation.strip():
            raise VocabularyStoreError("translation must not be empty")
        ensure_vocabulary_db(self._data_root, self._language_code)
        if self.has_lemma(normalized):
            raise VocabularyStoreError(f"duplicate lemma: {normalized}")
        now = datetime.now(UTC).isoformat()
        entry = VocabularyEntry(
            lemma=normalized,
            translation=translation.strip(),
            explanation=explanation.strip(),
            level_when_learned=level_when_learned,
            difficulty_rating=difficulty_rating,
            word_category=word_category,
            surface_form=surface_form.strip() if surface_form else None,
        )
        connection = connect_sqlite(self._db_path())
        try:
            with connection:
                connection.execute(
                    """
                    INSERT INTO vocabulary_entries(
                        lemma, translation, explanation, level_when_learned,
                        difficulty_rating, word_category, surface_form,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        entry.lemma,
                        entry.translation,
                        entry.explanation,
                        entry.level_when_learned.value,
                        entry.difficulty_rating.value,
                        entry.word_category.value,
                        entry.surface_form,
                        now,
                        now,
                    ),
                )
        finally:
            connection.close()
        return entry

    def update_entry(
        self,
        lemma: str,
        *,
        new_lemma: str | None = None,
        translation: str | None = None,
        explanation: str | None = None,
        level_when_learned: CEFRLevel | None = None,
        difficulty_rating: DifficultyRating | None = None,
        word_category: WordCategory | None = None,
        surface_form: str | None = None,
        clear_surface_form: bool = False,
    ) -> VocabularyEntry:
        """Update fields on an existing vocabulary entry."""
        existing = self.get(lemma)
        if existing is None:
            raise VocabularyStoreError(f"lemma not found: {lemma}")
        category = (
            word_category if word_category is not None else existing.word_category
        )
        resolved_lemma = existing.lemma
        if new_lemma is not None:
            normalized = normalize_lemma(
                new_lemma,
                language_code=self._language_code,
                category=category,
            )
            if not normalized:
                raise VocabularyStoreError("lemma must not be empty")
            if normalized != existing.lemma and self.has_lemma(normalized):
                raise VocabularyStoreError(f"duplicate lemma: {normalized}")
            resolved_lemma = normalized
        updated = VocabularyEntry(
            lemma=resolved_lemma,
            translation=(
                translation.strip() if translation is not None else existing.translation
            ),
            explanation=(
                explanation.strip() if explanation is not None else existing.explanation
            ),
            level_when_learned=(
                level_when_learned
                if level_when_learned is not None
                else existing.level_when_learned
            ),
            difficulty_rating=(
                difficulty_rating
                if difficulty_rating is not None
                else existing.difficulty_rating
            ),
            word_category=(
                word_category if word_category is not None else existing.word_category
            ),
            surface_form=(
                None
                if clear_surface_form
                else (
                    surface_form.strip()
                    if surface_form is not None
                    else existing.surface_form
                )
            ),
            entry_id=existing.entry_id,
        )
        if not updated.translation:
            raise VocabularyStoreError("translation must not be empty")
        now = datetime.now(UTC).isoformat()
        connection = connect_sqlite(self._db_path())
        try:
            with connection:
                if resolved_lemma != existing.lemma:
                    self._delete_word_embedding(connection, existing.lemma)
                connection.execute(
                    """
                    UPDATE vocabulary_entries
                    SET lemma = ?, translation = ?, explanation = ?,
                        level_when_learned = ?,
                        difficulty_rating = ?, word_category = ?, surface_form = ?,
                        updated_at = ?
                    WHERE lemma = ?
                    """,
                    (
                        updated.lemma,
                        updated.translation,
                        updated.explanation,
                        updated.level_when_learned.value,
                        updated.difficulty_rating.value,
                        updated.word_category.value,
                        updated.surface_form,
                        now,
                        existing.lemma,
                    ),
                )
        finally:
            connection.close()
        return updated

    def set_difficulty(self, lemma: str, rating: DifficultyRating) -> VocabularyEntry:
        """Set the difficulty rating for an entry."""
        return self.update_entry(lemma, difficulty_rating=rating)

    def promote_fluency(self, lemma: str) -> VocabularyEntry:
        """Promote difficulty one step after study reveal."""
        existing = self.get(lemma)
        if existing is None:
            raise VocabularyStoreError(f"lemma not found: {lemma}")
        promoted = next_difficulty(existing.difficulty_rating)
        if promoted is None:
            raise VocabularyStoreError("lemma is already mastered")
        return self.set_difficulty(lemma, promoted)

    def delete_entry(self, lemma: str) -> DeletedVocabularyEntry:
        """Remove a vocabulary entry and return a snapshot for undo."""
        resolved = self._resolve_lemma(lemma)
        if resolved is None:
            raise VocabularyStoreError(f"lemma not found: {lemma}")
        connection = self._connect_read()
        if connection is None:
            raise VocabularyStoreError(f"lemma not found: {lemma}")
        try:
            row = self._fetch_one(
                connection,
                """
                SELECT lemma, translation, explanation, level_when_learned,
                       difficulty_rating, word_category, surface_form,
                       created_at, updated_at
                FROM vocabulary_entries WHERE lemma = ?
                """,
                (resolved,),
            )
        finally:
            connection.close()
        if row is None:
            raise VocabularyStoreError(f"lemma not found: {lemma}")
        snapshot = DeletedVocabularyEntry(
            lemma=str(row[0]),
            translation=str(row[1]),
            explanation=str(row[2]),
            level_when_learned=str(row[3]),
            difficulty_rating=str(row[4]),
            word_category=str(row[5]),
            surface_form=str(row[6]) if row[6] is not None else None,
            created_at=str(row[7]),
            updated_at=str(row[8]),
        )
        connection = connect_sqlite(self._db_path())
        try:
            with connection:
                connection.execute(
                    "DELETE FROM vocabulary_entries WHERE lemma = ?",
                    (resolved,),
                )
                self._delete_word_embedding(connection, resolved)
        finally:
            connection.close()
        from lexiflow_core.vocabulary.trash import archive_deleted_entry

        archive_deleted_entry(self._data_root, self._language_code, snapshot)
        return snapshot

    @staticmethod
    def _delete_word_embedding(connection: sqlite3.Connection, lemma: str) -> None:
        try:
            load_sqlite_vec(connection)
            connection.execute(
                "DELETE FROM word_embeddings WHERE lemma = ?",
                (lemma,),
            )
        except sqlite3.OperationalError:
            return

    def restore_entry(self, snapshot: DeletedVocabularyEntry) -> VocabularyEntry:
        """Restore a previously deleted entry from a snapshot."""
        if self.has_lemma(snapshot.lemma):
            raise VocabularyStoreError(f"duplicate lemma: {snapshot.lemma}")
        connection = connect_sqlite(self._db_path())
        try:
            with connection:
                connection.execute(
                    """
                    INSERT INTO vocabulary_entries(
                        lemma, translation, explanation, level_when_learned,
                        difficulty_rating, word_category, surface_form,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        snapshot.lemma,
                        snapshot.translation,
                        snapshot.explanation,
                        snapshot.level_when_learned,
                        snapshot.difficulty_rating,
                        snapshot.word_category,
                        snapshot.surface_form,
                        snapshot.created_at,
                        snapshot.updated_at,
                    ),
                )
        finally:
            connection.close()
        entry = self.get(snapshot.lemma)
        if entry is None:
            raise VocabularyStoreError(f"failed to restore lemma: {snapshot.lemma}")
        from lexiflow_core.vocabulary.trash import remove_trash_item

        remove_trash_item(self._data_root, self._language_code, snapshot.lemma)
        return entry

    def _resolve_lemma(self, lemma: str) -> str | None:
        candidate = lemma.strip()
        if not candidate:
            return None
        connection = self._connect_read()
        if connection is None:
            return None
        try:
            row = self._fetch_one(
                connection,
                "SELECT lemma FROM vocabulary_entries WHERE lemma = ?",
                (candidate,),
            )
            if row is not None:
                return str(row[0])
            row = self._fetch_one(
                connection,
                "SELECT lemma FROM vocabulary_entries WHERE lemma COLLATE NOCASE = ?",
                (candidate,),
            )
        finally:
            connection.close()
        if row is None:
            return None
        return str(row[0])

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
            word_category,
            surface_form,
        ) = row
        return VocabularyEntry(
            lemma=str(lemma),
            translation=str(translation),
            explanation=str(explanation),
            level_when_learned=CEFRLevel(str(level_when_learned)),
            difficulty_rating=DifficultyRating(str(difficulty_rating)),
            word_category=parse_word_category(word_category),
            surface_form=str(surface_form) if surface_form is not None else None,
        )
