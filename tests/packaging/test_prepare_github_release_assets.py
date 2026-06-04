"""Tests for GitHub release asset size handling."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_prepare_github_release_assets():
    script = (
        Path(__file__).resolve().parents[2]
        / "packaging"
        / "scripts"
        / "prepare_github_release_assets.py"
    )
    spec = importlib.util.spec_from_file_location(
        "lexiflow_prepare_github_release_assets",
        script,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_asset_needs_compression_at_github_limit() -> None:
    prepare = _load_prepare_github_release_assets()
    limit = prepare.GITHUB_RELEASE_MAX_BYTES
    assert prepare.asset_needs_compression(limit - 1) is False
    assert prepare.asset_needs_compression(limit) is True


def test_prepare_directory_leaves_small_files_uncompressed(
    tmp_path: Path, monkeypatch
) -> None:
    prepare = _load_prepare_github_release_assets()
    merged = tmp_path / "merged"
    merged.mkdir()
    small = merged / "LexiFlow-1.0.3-x86_64.AppImage"
    small.write_bytes(b"tiny")

    prepare.prepare_directory(merged)

    assert small.is_file()
    assert not small.with_suffix(small.suffix + ".zst").exists()
    checksums = (merged / "checksums.txt").read_text(encoding="utf-8")
    assert "LexiFlow-1.0.3-x86_64.AppImage" in checksums
