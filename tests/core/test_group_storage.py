"""Tests for group storage disk operations."""

from __future__ import annotations

from pathlib import Path

import pytest
from lexiflow_core.config.paths import group_dir
from lexiflow_core.library.group_storage import GroupFolderExistsError, GroupStorage


def test_rename_folder_rejects_existing_target(tmp_path: Path) -> None:
    storage = GroupStorage(tmp_path)
    storage.register("es", "News")
    storage.register("es", "Podcasts")
    podcasts_path = group_dir(tmp_path, "es", "podcasts")

    with pytest.raises(GroupFolderExistsError, match="already exists"):
        storage.rename_folder("es", "news", "podcasts")

    assert podcasts_path.is_dir()
