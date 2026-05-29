"""Tests for group name slugification and registry."""

from __future__ import annotations

from pathlib import Path

import pytest
from lexiflow_core.library.group_names import slugify_group_name
from lexiflow_core.library.group_registry import (
    GroupNotFoundError,
    GroupRegistry,
    GroupSlugCollisionError,
)


def test_slugify_group_name_sanitizes_unsafe_chars() -> None:
    assert slugify_group_name("News/Politics") == "news-politics"


def test_slugify_group_name_rejects_empty() -> None:
    with pytest.raises(ValueError, match="empty"):
        slugify_group_name("   ")


def test_group_registry_register_and_resolve(tmp_path: Path) -> None:
    registry = GroupRegistry(tmp_path, "es")

    folder_slug = registry.register("News/Politics")

    assert folder_slug == "news-politics"
    assert registry.folder_slug_for_display("News/Politics") == "news-politics"
    assert registry.display_name_for_folder("news-politics") == "News/Politics"
    assert registry.list_display_names() == ["News/Politics"]


def test_group_registry_rename_updates_mapping(tmp_path: Path) -> None:
    registry = GroupRegistry(tmp_path, "es")
    registry.register("Podcasts")

    old_slug, new_slug = registry.rename("Podcasts", "My Podcasts")

    assert old_slug == "podcasts"
    assert new_slug == "my-podcasts"
    assert registry.folder_slug_for_display("My Podcasts") == "my-podcasts"


def test_group_registry_remove(tmp_path: Path) -> None:
    registry = GroupRegistry(tmp_path, "es")
    registry.register("News")

    registry.remove("news")

    with pytest.raises(GroupNotFoundError):
        registry.folder_slug_for_display("News")


def test_group_registry_folder_slug_not_found(tmp_path: Path) -> None:
    registry = GroupRegistry(tmp_path, "es")

    with pytest.raises(GroupNotFoundError):
        registry.folder_slug_for_display("Missing")


def test_group_registry_rejects_slug_collision(tmp_path: Path) -> None:
    registry = GroupRegistry(tmp_path, "es")
    registry.register("Foo Bar")

    with pytest.raises(GroupSlugCollisionError):
        registry.register("Foo-Bar")
