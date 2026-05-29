"""Tests for library-related path helpers."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.config.paths import (
    group_dir,
    groups_json_path,
    index_db_path,
    language_data_dir,
    meta_path,
    text_dir,
    trash_dir,
    variant_path,
)


def test_language_data_dir(tmp_path: Path) -> None:
    assert language_data_dir(tmp_path, "es") == tmp_path / "es" / ".data"


def test_groups_json_path(tmp_path: Path) -> None:
    assert groups_json_path(tmp_path, "es") == tmp_path / "es" / ".data" / "groups.json"


def test_index_db_path(tmp_path: Path) -> None:
    assert index_db_path(tmp_path) == tmp_path / ".app" / "index.sqlite"


def test_trash_dir(tmp_path: Path) -> None:
    assert trash_dir(tmp_path) == tmp_path / ".trash"


def test_group_and_text_dirs(tmp_path: Path) -> None:
    assert group_dir(tmp_path, "es", "news") == tmp_path / "es" / "news"
    assert text_dir(tmp_path, "es", "news", "article-a3f2") == (
        tmp_path / "es" / "news" / "article-a3f2"
    )


def test_meta_and_variant_paths(tmp_path: Path) -> None:
    text_folder = tmp_path / "es" / "news" / "article-a3f2"
    assert meta_path(text_folder) == text_folder / "meta.json"
    assert variant_path(text_folder, "native") == text_folder / "native.md"
