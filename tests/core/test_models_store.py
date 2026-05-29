"""Tests for lexiflow_core.models.store and download."""

from __future__ import annotations

from pathlib import Path

import pytest
from lexiflow_core.models.download import FakeModelDownloader, ModelAccessError
from lexiflow_core.models.lockfile import load_models_lock
from lexiflow_core.models.paths import artifact_revision_path, models_cache_dir
from lexiflow_core.models.store import ModelStore


def test_ensure_installed_writes_revision_marker(tmp_path: Path) -> None:
    data_root = tmp_path / "library"
    lock_path = tmp_path / "models.lock"
    lock_path.write_text(
        """
[[artifacts]]
id = "embedding-minilm"
repo = "sentence-transformers/all-MiniLM-L6-v2"
revision = "c9745ed1d9f207416be6d2e6f8de32d1f16199bf"
""".strip(),
        encoding="utf-8",
    )
    lock = load_models_lock(lock_path)
    store = ModelStore(
        data_root=data_root,
        lock=lock,
        downloader=FakeModelDownloader(),
    )

    result = store.ensure_installed("embedding-minilm", on_progress=lambda *_: None)

    marker = artifact_revision_path(data_root, "embedding-minilm")
    assert marker.is_file()
    assert (
        marker.read_text(encoding="utf-8") == "c9745ed1d9f207416be6d2e6f8de32d1f16199bf"
    )
    assert result == models_cache_dir(data_root) / "embedding-minilm"


def test_ensure_installed_passes_huggingface_token_to_downloader(
    tmp_path: Path,
) -> None:
    data_root = tmp_path / "library"
    lock_path = tmp_path / "models.lock"
    lock_path.write_text(
        """
[[artifacts]]
id = "embedding-minilm"
repo = "sentence-transformers/all-MiniLM-L6-v2"
revision = "c9745ed1d9f207416be6d2e6f8de32d1f16199bf"
""".strip(),
        encoding="utf-8",
    )
    downloader = FakeModelDownloader()
    store = ModelStore(
        data_root=data_root,
        lock=load_models_lock(lock_path),
        downloader=downloader,
        huggingface_token="hf_test_token",
    )

    store.ensure_installed("embedding-minilm", on_progress=lambda *_: None)

    assert downloader.last_token == "hf_test_token"


def test_check_for_updates_detects_older_installed_revision(tmp_path: Path) -> None:
    data_root = tmp_path / "library"
    lock_path = tmp_path / "models.lock"
    lock_path.write_text(
        """
[[artifacts]]
id = "embedding-minilm"
repo = "sentence-transformers/all-MiniLM-L6-v2"
revision = "newer-revision-sha"

[[artifacts]]
id = "embedded-gemma"
repo = "google/gemma-2-2b-it"
revision = "gemma-pinned-sha"
""".strip(),
        encoding="utf-8",
    )
    marker = artifact_revision_path(data_root, "embedding-minilm")
    marker.parent.mkdir(parents=True)
    marker.write_text("older-revision-sha", encoding="utf-8")

    store = ModelStore(
        data_root=data_root,
        lock=load_models_lock(lock_path),
        downloader=FakeModelDownloader(),
    )

    updates = store.check_for_updates()

    assert len(updates) == 1
    assert updates[0].artifact_id == "embedding-minilm"
    assert updates[0].installed_revision == "older-revision-sha"
    assert updates[0].pinned_revision == "newer-revision-sha"


def test_fake_downloader_reports_progress(tmp_path: Path) -> None:
    data_root = tmp_path / "library"
    lock_path = tmp_path / "models.lock"
    lock_path.write_text(
        """
[[artifacts]]
id = "embedding-minilm"
repo = "sentence-transformers/all-MiniLM-L6-v2"
revision = "abc"
""".strip(),
        encoding="utf-8",
    )
    progress: list[float] = []
    store = ModelStore(
        data_root=data_root,
        lock=load_models_lock(lock_path),
        downloader=FakeModelDownloader(),
    )

    store.ensure_installed("embedding-minilm", on_progress=progress.append)

    assert progress == [1.0]


def test_ensure_installed_propagates_model_access_error(tmp_path: Path) -> None:
    data_root = tmp_path / "library"
    lock_path = tmp_path / "models.lock"
    lock_path.write_text(
        """
[[artifacts]]
id = "embedding-minilm"
repo = "sentence-transformers/all-MiniLM-L6-v2"
revision = "abc"
""".strip(),
        encoding="utf-8",
    )

    store = ModelStore(
        data_root=data_root,
        lock=load_models_lock(lock_path),
        downloader=FakeModelDownloader(error=ModelAccessError("gated")),
    )

    with pytest.raises(ModelAccessError):
        store.ensure_installed("embedding-minilm", on_progress=lambda *_: None)
