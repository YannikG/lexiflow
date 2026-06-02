"""Vocabulary export to a portable zip bundle."""

from __future__ import annotations

import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from lexiflow_core.config.paths import vocabulary_db_path
from lexiflow_core.vectors.setup import ensure_vocabulary_db

EXPORT_FORMAT = "lexiflow-vocabulary"
EXPORT_VERSION = 1


def export_vocabulary_zip(
    destination: Path,
    *,
    data_root: Path,
    language_code: str,
) -> Path:
    """Write a vocabulary handoff zip and return the path written."""
    ensure_vocabulary_db(data_root, language_code)
    db_path = vocabulary_db_path(data_root, language_code)
    if not db_path.is_file():
        raise FileNotFoundError(f"vocabulary database not found for {language_code}")

    destination = destination.expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "format": EXPORT_FORMAT,
        "version": EXPORT_VERSION,
        "language_code": language_code,
        "exported_at": datetime.now(UTC).isoformat(),
    }
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "manifest.json",
            json.dumps(manifest, indent=2) + "\n",
        )
        archive.write(db_path, arcname="vocabulary.sqlite")
    return destination
