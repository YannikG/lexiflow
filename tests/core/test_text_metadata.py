"""Tests for text metadata validation and persistence."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import pytest
from lexiflow_core.library.text_metadata import (
    TextMetadata,
    TextMetadataError,
    load_text_metadata,
    parse_text_metadata,
    read_text_id,
    save_text_metadata,
)


def _sample_metadata() -> TextMetadata:
    now = datetime(2026, 5, 29, 12, 0, tzinfo=UTC)
    return TextMetadata(
        id=UUID("11111111-1111-1111-1111-111111111111"),
        title="Hola",
        group="News/Politics",
        native_language="de",
        target_language="es",
        variants=("native",),
        source_url=None,
        created_at=now,
        updated_at=now,
    )


def test_parse_text_metadata_round_trip() -> None:
    metadata = _sample_metadata()

    parsed = parse_text_metadata(metadata.to_dict())

    assert parsed == metadata


def test_parse_text_metadata_rejects_level_key() -> None:
    payload = _sample_metadata().to_dict()
    payload["level"] = "A2"

    with pytest.raises(TextMetadataError, match="forbidden metadata keys"):
        parse_text_metadata(payload)


def test_load_text_metadata_from_disk(tmp_path: Path) -> None:
    metadata = _sample_metadata()
    path = tmp_path / "meta.json"
    save_text_metadata(path, metadata)

    loaded = load_text_metadata(path)

    assert loaded == metadata


def test_load_text_metadata_rejects_level_in_file(tmp_path: Path) -> None:
    path = tmp_path / "meta.json"
    payload = _sample_metadata().to_dict()
    payload["level"] = "B1"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(TextMetadataError, match="forbidden metadata keys"):
        load_text_metadata(path)


def test_read_text_id_ignores_forbidden_keys(tmp_path: Path) -> None:
    metadata = _sample_metadata()
    path = tmp_path / "meta.json"
    payload = metadata.to_dict()
    payload["level"] = "A2"
    path.write_text(json.dumps(payload), encoding="utf-8")

    assert read_text_id(path) == metadata.id


def test_read_text_id_returns_none_for_missing_file(tmp_path: Path) -> None:
    assert read_text_id(tmp_path / "missing.json") is None
