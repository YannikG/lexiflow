"""Vocabulary import from a portable zip bundle."""

from __future__ import annotations

import json
import sqlite3
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path

from lexiflow_core.config.paths import vocabulary_db_path
from lexiflow_core.db.connection import connect_sqlite
from lexiflow_core.vectors.setup import ensure_vocabulary_db
from lexiflow_core.vocabulary.export import EXPORT_FORMAT, EXPORT_VERSION


class VocabularyImportError(Exception):
    """Raised when a vocabulary import bundle is invalid."""


@dataclass(frozen=True)
class VocabularyImportResult:
    imported: int
    skipped: int
    overwritten: int


def _read_manifest(archive: zipfile.ZipFile) -> dict[str, object]:
    try:
        raw = archive.read("manifest.json")
    except KeyError as exc:
        raise VocabularyImportError("bundle is missing manifest.json") from exc
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise VocabularyImportError("manifest.json is invalid") from exc
    if not isinstance(parsed, dict):
        raise VocabularyImportError("manifest.json must be an object")
    return parsed


def _validate_manifest(manifest: dict[str, object], *, language_code: str) -> None:
    if manifest.get("format") != EXPORT_FORMAT:
        raise VocabularyImportError("unsupported vocabulary export format")
    if manifest.get("version") != EXPORT_VERSION:
        raise VocabularyImportError("unsupported vocabulary export version")
    bundle_lang = manifest.get("language_code")
    if bundle_lang != language_code:
        raise VocabularyImportError(
            f"bundle language {bundle_lang!r} does not match target {language_code!r}"
        )


def import_vocabulary_zip(
    source: Path,
    *,
    data_root: Path,
    language_code: str,
    overwrite: bool = False,
) -> VocabularyImportResult:
    """Merge entries from an export zip into the active target language database."""
    source = source.expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(f"import bundle not found: {source}")

    ensure_vocabulary_db(data_root, language_code)
    target_path = vocabulary_db_path(data_root, language_code)

    with zipfile.ZipFile(source, "r") as archive:
        manifest = _read_manifest(archive)
        _validate_manifest(manifest, language_code=language_code)
        try:
            bundle_db_bytes = archive.read("vocabulary.sqlite")
        except KeyError as exc:
            raise VocabularyImportError("bundle is missing vocabulary.sqlite") from exc

    with tempfile.TemporaryDirectory() as temp_dir:
        bundle_db = Path(temp_dir) / "vocabulary.sqlite"
        bundle_db.write_bytes(bundle_db_bytes)
        return _merge_databases(
            bundle_db,
            target_path,
            overwrite=overwrite,
        )


def _delete_word_embedding(connection: sqlite3.Connection, lemma: str) -> None:
    try:
        connection.execute(
            "DELETE FROM word_embeddings WHERE lemma = ?",
            (lemma,),
        )
    except sqlite3.OperationalError:
        return


def _copy_word_embedding(
    source: sqlite3.Connection,
    target: sqlite3.Connection,
    lemma: str,
) -> None:
    try:
        embedding = source.execute(
            "SELECT embedding FROM word_embeddings WHERE lemma = ?",
            (lemma,),
        ).fetchone()
    except sqlite3.OperationalError:
        return
    if embedding is None:
        return
    try:
        _delete_word_embedding(target, lemma)
        target.execute(
            "INSERT INTO word_embeddings(lemma, embedding) VALUES (?, ?)",
            (lemma, embedding[0]),
        )
    except sqlite3.OperationalError:
        return


def _merge_databases(
    source_db: Path,
    target_db: Path,
    *,
    overwrite: bool,
) -> VocabularyImportResult:
    source = connect_sqlite(source_db)
    target = connect_sqlite(target_db)
    imported = 0
    skipped = 0
    overwritten = 0
    try:
        rows = source.execute(
            """
            SELECT lemma, translation, explanation, level_when_learned,
                   difficulty_rating, surface_form, created_at, updated_at
            FROM vocabulary_entries
            ORDER BY lemma
            """
        ).fetchall()
        for row in rows:
            lemma = str(row[0])
            existing = target.execute(
                "SELECT 1 FROM vocabulary_entries WHERE lemma = ?",
                (lemma,),
            ).fetchone()
            if existing is not None and not overwrite:
                skipped += 1
                continue
            with target:
                if existing is not None:
                    target.execute(
                        "DELETE FROM vocabulary_entries WHERE lemma = ?",
                        (lemma,),
                    )
                    _delete_word_embedding(target, lemma)
                    overwritten += 1
                else:
                    imported += 1
                target.execute(
                    """
                    INSERT INTO vocabulary_entries(
                        lemma, translation, explanation, level_when_learned,
                        difficulty_rating, surface_form, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    row,
                )
                _copy_word_embedding(source, target, lemma)
    finally:
        source.close()
        target.close()
    return VocabularyImportResult(
        imported=imported,
        skipped=skipped,
        overwritten=overwritten,
    )
