"""Pure path calculations for LexiFlow on disk."""

from __future__ import annotations

from pathlib import Path

APP_DATA_NAME = "LexiFlow"


def default_data_root() -> Path:
    """Return the default user library path when settings do not override it."""
    return (Path.home() / APP_DATA_NAME).resolve()


def language_data_root(data_root: Path, language_code: str) -> Path:
    """Return the per-target-language folder (stub for later phases)."""
    return data_root / language_code
