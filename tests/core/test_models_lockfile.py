"""Tests for lexiflow_core.models.lockfile."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.models.lockfile import load_models_lock


def test_load_models_lock_parses_two_artifacts_with_revisions(tmp_path: Path) -> None:
    lock_path = tmp_path / "models.lock"
    lock_path.write_text(
        """
[[artifacts]]
id = "embedding-minilm"
repo = "sentence-transformers/all-MiniLM-L6-v2"
revision = "c9745ed1d9f207416be6d2e6f8de32d1f16199bf"

[[artifacts]]
id = "embedded-gemma"
repo = "google/gemma-2-2b-it"
revision = "9cf48e52b224519b2f38bc8fd9a74b3c6386dd51"
""".strip(),
        encoding="utf-8",
    )

    lock = load_models_lock(lock_path)

    assert len(lock.artifacts) == 2
    assert lock.artifacts[0].id == "embedding-minilm"
    assert lock.artifacts[0].repo == "sentence-transformers/all-MiniLM-L6-v2"
    assert lock.artifacts[0].revision == "c9745ed1d9f207416be6d2e6f8de32d1f16199bf"
    assert lock.artifacts[1].id == "embedded-gemma"
    assert lock.artifacts[1].revision == "9cf48e52b224519b2f38bc8fd9a74b3c6386dd51"


def test_bundled_models_lock_loads_two_artifacts() -> None:
    from lexiflow_core.models.lockfile import bundled_models_lock_path

    lock = load_models_lock(bundled_models_lock_path())

    assert len(lock.artifacts) >= 2
    for artifact in lock.artifacts:
        assert artifact.id
        assert artifact.repo
        assert artifact.revision
