"""Per-language vector storage and similarity search."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from uuid import UUID

from lexiflow_core.config.paths import text_vectors_db_path, vocabulary_db_path
from lexiflow_core.db.connection import connect_sqlite
from lexiflow_core.vectors.models import EMBEDDING_DIM, WordHit
from lexiflow_core.vectors.serialization import serialize_float32, vector_from_json
from lexiflow_core.vectors.setup import ensure_text_vectors_db, ensure_vocabulary_db
from lexiflow_core.vectors.sqlite_vec import load_sqlite_vec


class VectorStore:
    """Store and query text and word embeddings for one target language."""

    def __init__(self, data_root: Path, language_code: str) -> None:
        self._data_root = data_root
        self._language_code = language_code
        ensure_text_vectors_db(data_root, language_code)
        ensure_vocabulary_db(data_root, language_code)

    def upsert_text_vector(self, text_id: UUID, vec: list[float]) -> None:
        self._validate_dimensions(vec)
        connection = self._open_text_vectors_db()
        try:
            text_id_text = str(text_id)
            with connection:
                connection.execute(
                    "DELETE FROM text_embeddings WHERE text_id = ?",
                    (text_id_text,),
                )
                connection.execute(
                    "INSERT INTO text_embeddings(text_id, embedding) VALUES (?, ?)",
                    (text_id_text, serialize_float32(vec)),
                )
        finally:
            connection.close()

    def get_text_vector(self, text_id: UUID) -> list[float] | None:
        connection = self._open_text_vectors_db()
        try:
            row = connection.execute(
                """
                SELECT vec_to_json(embedding)
                FROM text_embeddings
                WHERE text_id = ?
                """,
                (str(text_id),),
            ).fetchone()
        finally:
            connection.close()
        if row is None:
            return None
        json_text = row[0]
        if not isinstance(json_text, str):
            return None
        return vector_from_json(json_text)

    def upsert_word_vector(self, lemma: str, vec: list[float]) -> None:
        self._validate_dimensions(vec)
        connection = self._open_vocabulary_db()
        try:
            with connection:
                connection.execute(
                    "DELETE FROM word_embeddings WHERE lemma = ?",
                    (lemma,),
                )
                connection.execute(
                    "INSERT INTO word_embeddings(lemma, embedding) VALUES (?, ?)",
                    (lemma, serialize_float32(vec)),
                )
        finally:
            connection.close()

    def search_similar_words(self, vec: list[float], *, limit: int) -> list[WordHit]:
        self._validate_dimensions(vec)
        connection = self._open_vocabulary_db()
        try:
            rows = connection.execute(
                """
                SELECT lemma, distance
                FROM word_embeddings
                WHERE embedding MATCH ?
                ORDER BY distance
                LIMIT ?
                """,
                (serialize_float32(vec), limit),
            ).fetchall()
        finally:
            connection.close()
        return [
            WordHit(lemma=str(lemma), distance=float(distance))
            for lemma, distance in rows
        ]

    def _open_text_vectors_db(self) -> sqlite3.Connection:
        db_path = text_vectors_db_path(self._data_root, self._language_code)
        connection = connect_sqlite(db_path)
        load_sqlite_vec(connection)
        return connection

    def _open_vocabulary_db(self) -> sqlite3.Connection:
        db_path = vocabulary_db_path(self._data_root, self._language_code)
        connection = connect_sqlite(db_path)
        load_sqlite_vec(connection)
        return connection

    @staticmethod
    def _validate_dimensions(vec: list[float]) -> None:
        if len(vec) != EMBEDDING_DIM:
            msg = f"expected {EMBEDDING_DIM} dimensions, got {len(vec)}"
            raise ValueError(msg)
