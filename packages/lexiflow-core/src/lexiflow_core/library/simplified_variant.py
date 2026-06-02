"""Remove simplified variants from a text folder."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

from lexiflow_core.config.paths import meta_path, variant_path
from lexiflow_core.library.models import TextRecord
from lexiflow_core.library.reader_tabs import SIMPLIFIED_PREFIX
from lexiflow_core.library.text_metadata import (
    TextMetadata,
    load_text_metadata,
    metadata_to_record,
    save_text_metadata,
)
from lexiflow_core.simplify.suggestions_store import suggestions_path


class SimplifiedVariantError(Exception):
    """Raised when a simplified variant cannot be removed."""


def remove_simplified_variant_files(text_folder: Path, variant_name: str) -> None:
    """Delete simplified markdown and suggestions sidecar when present."""
    if not variant_name.startswith(SIMPLIFIED_PREFIX):
        raise SimplifiedVariantError(f"not a simplified variant: {variant_name!r}")
    markdown = variant_path(text_folder, variant_name)
    if markdown.is_file():
        markdown.unlink()
    sidecar = suggestions_path(text_folder, variant_name)
    if sidecar.is_file():
        sidecar.unlink()


def remove_simplified_variant_metadata(
    text_folder: Path, variant_name: str
) -> TextMetadata:
    """Drop a simplified variant from text metadata."""
    if not variant_name.startswith(SIMPLIFIED_PREFIX):
        raise SimplifiedVariantError(f"not a simplified variant: {variant_name!r}")
    metadata = load_text_metadata(meta_path(text_folder))
    variants = tuple(v for v in metadata.variants if v != variant_name)
    return replace(
        metadata,
        variants=variants,
        updated_at=datetime.now(UTC),
    )


def apply_simplified_variant_removal(
    text_folder: Path, variant_name: str
) -> TextRecord:
    """Remove on-disk simplified content and update metadata."""
    remove_simplified_variant_files(text_folder, variant_name)
    updated = remove_simplified_variant_metadata(text_folder, variant_name)
    save_text_metadata(meta_path(text_folder), updated)
    return metadata_to_record(
        updated,
        group_folder_slug=text_folder.parent.name,
        text_slug=text_folder.name,
        folder=str(text_folder),
    )
