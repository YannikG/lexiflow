"""Trash storage for deleted vocabulary entries."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

from lexiflow_core.config.paths import vocabulary_trash_dir
from lexiflow_core.vocabulary.store import DeletedVocabularyEntry


class VocabularyTrashItemNotFoundError(Exception):
    """Raised when a trashed vocabulary lemma does not exist."""


@dataclass(frozen=True)
class VocabularyTrashItem:
    lemma: str
    translation: str
    deleted_at: datetime | None = None


def archive_deleted_entry(
    data_root: Path,
    language_code: str,
    snapshot: DeletedVocabularyEntry,
) -> None:
    """Persist a deleted vocabulary snapshot to trash."""
    root = vocabulary_trash_dir(data_root, language_code)
    root.mkdir(parents=True, exist_ok=True)
    path = _trash_file_path(root, snapshot.lemma)
    payload = {
        "lemma": snapshot.lemma,
        "translation": snapshot.translation,
        "explanation": snapshot.explanation,
        "level_when_learned": snapshot.level_when_learned,
        "difficulty_rating": snapshot.difficulty_rating,
        "word_category": snapshot.word_category,
        "surface_form": snapshot.surface_form,
        "created_at": snapshot.created_at,
        "updated_at": snapshot.updated_at,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def remove_trash_item(data_root: Path, language_code: str, lemma: str) -> None:
    """Remove one trashed vocabulary snapshot if present."""
    path = _trash_file_path(vocabulary_trash_dir(data_root, language_code), lemma)
    if path.is_file():
        path.unlink()


def list_vocabulary_trash(
    data_root: Path, language_code: str
) -> list[VocabularyTrashItem]:
    """Return trashed vocabulary entries for one target language."""
    root = vocabulary_trash_dir(data_root, language_code)
    if not root.is_dir():
        return []
    items: list[VocabularyTrashItem] = []
    for path in sorted(root.glob("*.json")):
        try:
            snapshot = _load_snapshot(path)
        except (OSError, json.JSONDecodeError, KeyError, TypeError):
            continue
        deleted_at = datetime.fromtimestamp(path.stat().st_mtime)
        items.append(
            VocabularyTrashItem(
                lemma=snapshot.lemma,
                translation=snapshot.translation,
                deleted_at=deleted_at,
            )
        )
    items.sort(key=lambda item: item.lemma.casefold())
    return items


def load_trash_snapshot(
    data_root: Path,
    language_code: str,
    lemma: str,
) -> DeletedVocabularyEntry:
    """Load one trashed vocabulary snapshot."""
    path = _trash_file_path(vocabulary_trash_dir(data_root, language_code), lemma)
    if not path.is_file():
        raise VocabularyTrashItemNotFoundError(f"trashed lemma not found: {lemma}")
    return _load_snapshot(path)


def empty_vocabulary_trash(data_root: Path, language_code: str) -> int:
    """Permanently delete all trashed vocabulary for one language."""
    root = vocabulary_trash_dir(data_root, language_code)
    if not root.is_dir():
        return 0
    count = len(list(root.glob("*.json")))
    shutil.rmtree(root)
    return count


def _trash_file_path(root: Path, lemma: str) -> Path:
    return root / f"{quote(lemma, safe='')}.json"


def _load_snapshot(path: Path) -> DeletedVocabularyEntry:
    payload = json.loads(path.read_text(encoding="utf-8"))
    surface_form = payload.get("surface_form")
    return DeletedVocabularyEntry(
        lemma=str(payload["lemma"]),
        translation=str(payload["translation"]),
        explanation=str(payload["explanation"]),
        level_when_learned=str(payload["level_when_learned"]),
        difficulty_rating=str(payload["difficulty_rating"]),
        word_category=str(payload["word_category"]),
        surface_form=str(surface_form) if surface_form is not None else None,
        created_at=str(payload["created_at"]),
        updated_at=str(payload["updated_at"]),
    )
