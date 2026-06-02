"""Tests for vocabulary export and import bundles."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

from lexiflow_core.languages.models import CEFRLevel
from lexiflow_core.vocabulary.export import export_vocabulary_zip
from lexiflow_core.vocabulary.import_bundle import import_vocabulary_zip
from lexiflow_core.vocabulary.models import WordCategory
from lexiflow_core.vocabulary.store import VocabularyStore


def test_export_zip_contains_manifest_and_sqlite(tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    store = VocabularyStore(data_root, "es")
    store.add_entry(
        lemma="correr", translation="to run", level_when_learned=CEFRLevel.A2
    )

    archive_path = export_vocabulary_zip(
        tmp_path / "vocab.zip",
        data_root=data_root,
        language_code="es",
    )

    with zipfile.ZipFile(archive_path, "r") as archive:
        names = set(archive.namelist())
        assert "manifest.json" in names
        assert "vocabulary.sqlite" in names
        manifest = json.loads(archive.read("manifest.json"))
        assert manifest["format"] == "lexiflow-vocabulary"
        assert manifest["language_code"] == "es"
        assert manifest["version"] == 1


def test_import_skips_duplicate_lemma(tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    store = VocabularyStore(data_root, "es")
    store.add_entry(
        lemma="correr", translation="to run", level_when_learned=CEFRLevel.A2
    )
    bundle = export_vocabulary_zip(
        tmp_path / "bundle.zip",
        data_root=data_root,
        language_code="es",
    )

    store.update_entry("correr", translation="jog")
    result = import_vocabulary_zip(
        bundle,
        data_root=data_root,
        language_code="es",
        overwrite=False,
    )

    assert result.skipped == 1
    assert store.get("correr") is not None
    assert store.get("correr").translation == "jog"


def test_import_overwrite_replaces_translation(tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    store = VocabularyStore(data_root, "es")
    store.add_entry(
        lemma="correr", translation="to run", level_when_learned=CEFRLevel.A2
    )
    bundle = export_vocabulary_zip(
        tmp_path / "bundle.zip",
        data_root=data_root,
        language_code="es",
    )

    store.update_entry("correr", translation="jog")
    result = import_vocabulary_zip(
        bundle,
        data_root=data_root,
        language_code="es",
        overwrite=True,
    )

    assert result.overwritten == 1
    assert store.get("correr") is not None
    assert store.get("correr").translation == "to run"


def test_export_import_preserves_word_category(tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    store = VocabularyStore(data_root, "es")
    store.add_entry(
        lemma="correr",
        translation="to run",
        explanation="Fast movement.",
        level_when_learned=CEFRLevel.A2,
        word_category=WordCategory.VERB,
    )
    bundle = export_vocabulary_zip(
        tmp_path / "bundle.zip",
        data_root=data_root,
        language_code="es",
    )

    store.update_entry("correr", word_category=WordCategory.OTHER)
    import_vocabulary_zip(
        bundle,
        data_root=data_root,
        language_code="es",
        overwrite=True,
    )

    entry = store.get("correr")
    assert entry is not None
    assert entry.word_category == WordCategory.VERB
