"""Pure path calculations for LexiFlow on disk."""

from __future__ import annotations

from pathlib import Path

APP_DATA_NAME = "LexiFlow"


def default_data_root() -> Path:
    """Return the default user library path when settings do not override it."""
    return (Path.home() / APP_DATA_NAME).resolve()


def language_data_root(data_root: Path, language_code: str) -> Path:
    """Return the per-target-language folder."""
    return data_root / language_code


def language_data_dir(data_root: Path, language_code: str) -> Path:
    """Return the per-language metadata directory (`.data/`)."""
    return language_data_root(data_root, language_code) / ".data"


def groups_json_path(data_root: Path, language_code: str) -> Path:
    """Return the path to the group registry for a target language."""
    return language_data_dir(data_root, language_code) / "groups.json"


def index_db_path(data_root: Path) -> Path:
    """Return the path to the library index database."""
    return data_root / ".app" / "index.sqlite"


def queue_db_path(data_root: Path) -> Path:
    """Return the path to the persistent job queue database."""
    return data_root / ".app" / "queue.sqlite"


def trash_dir(data_root: Path) -> Path:
    """Return the trash directory for deleted texts."""
    return data_root / ".trash"


def group_dir(data_root: Path, language_code: str, group_folder_slug: str) -> Path:
    """Return the on-disk folder for a group within a target language."""
    return language_data_root(data_root, language_code) / group_folder_slug


def text_dir(
    data_root: Path, language_code: str, group_folder_slug: str, text_slug: str
) -> Path:
    """Return the on-disk folder for a text."""
    return group_dir(data_root, language_code, group_folder_slug) / text_slug


def meta_path(text_folder: Path) -> Path:
    """Return the path to a text's metadata file."""
    return text_folder / "meta.json"


def variant_path(text_folder: Path, variant_name: str) -> Path:
    """Return the path to a variant markdown file (e.g. ``native`` → ``native.md``)."""
    return text_folder / f"{variant_name}.md"
