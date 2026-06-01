"""Tests for per-language vector storage."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

import pytest
from lexiflow_core.vectors.models import EMBEDDING_DIM
from lexiflow_core.vectors.setup import ensure_vocabulary_db
from lexiflow_core.vectors.store import VectorStore


def _sample_vector(seed: float) -> list[float]:
    return [seed + index * 0.001 for index in range(EMBEDDING_DIM)]


def test_upsert_text_vector_round_trips_by_id(tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    store = VectorStore(data_root, "es")
    text_id = UUID("11111111-1111-4111-8111-111111111111")
    vector = _sample_vector(0.5)

    store.upsert_text_vector(text_id, vector)

    loaded = store.get_text_vector(text_id)
    assert loaded is not None
    assert len(loaded) == EMBEDDING_DIM
    assert loaded == pytest.approx(vector)


def test_get_text_vector_returns_none_when_missing(tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    store = VectorStore(data_root, "es")

    assert store.get_text_vector(UUID("22222222-2222-4222-8222-222222222222")) is None


def test_ensure_vocabulary_db_uses_wal_mode(tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    db_path = ensure_vocabulary_db(data_root, "es")

    import sqlite3

    connection = sqlite3.connect(db_path)
    try:
        (journal_mode,) = connection.execute("PRAGMA journal_mode").fetchone()
    finally:
        connection.close()

    assert str(journal_mode).lower() == "wal"


def test_search_similar_words_returns_closest_lemma(tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    store = VectorStore(data_root, "es")
    query = _sample_vector(0.5)
    near = _sample_vector(0.51)
    far = _sample_vector(0.9)

    store.upsert_word_vector("cerca", near)
    store.upsert_word_vector("lejos", far)

    hits = store.search_similar_words(query, limit=1)

    assert len(hits) == 1
    assert hits[0].lemma == "cerca"
    assert hits[0].distance < 1.0
