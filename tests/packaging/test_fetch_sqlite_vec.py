"""Tests for sqlite-vec fetch asset selection."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


def _load_fetch_sqlite_vec():
    script = (
        Path(__file__).resolve().parents[2]
        / "packaging"
        / "scripts"
        / "fetch_sqlite_vec.py"
    )
    spec = importlib.util.spec_from_file_location("lexiflow_fetch_sqlite_vec", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    ("platform_key", "expected_asset"),
    [
        (
            "linux",
            "sqlite-vec-0.1.9-loadable-linux-x86_64.tar.gz",
        ),
        (
            "macos-arm64",
            "sqlite-vec-0.1.9-loadable-macos-aarch64.tar.gz",
        ),
        (
            "windows",
            "sqlite-vec-0.1.9-loadable-windows-x86_64.tar.gz",
        ),
    ],
)
def test_loadable_asset_for_prebuilt_platforms(
    platform_key: str, expected_asset: str
) -> None:
    fetch = _load_fetch_sqlite_vec()
    asset_name, archive_type, stem = fetch.loadable_asset(platform_key)
    assert asset_name == expected_asset
    assert archive_type == "tar.gz"
    assert stem == "vec0"


def test_loadable_asset_for_windows_arm64_requires_local_build() -> None:
    fetch = _load_fetch_sqlite_vec()
    asset_name, archive_type, stem = fetch.loadable_asset("windows-arm64")
    assert asset_name == ""
    assert archive_type == ""
    assert stem == "vec0.arm64"


def test_destination_path_for_windows_arm64() -> None:
    fetch = _load_fetch_sqlite_vec()
    path = fetch.destination_path("windows-arm64")
    assert path.name == "vec0.arm64"
