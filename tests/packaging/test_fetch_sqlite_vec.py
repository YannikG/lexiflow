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


def test_installed_loadable_path_for_windows_arm64() -> None:
    fetch = _load_fetch_sqlite_vec()
    path = fetch.installed_loadable_path("windows-arm64")
    assert path.name == "vec0.arm64.dll"


def test_installed_loadable_path_for_windows_x64() -> None:
    fetch = _load_fetch_sqlite_vec()
    path = fetch.installed_loadable_path("windows")
    assert path.name == "vec0.dll"


def test_installed_loadable_path_for_linux() -> None:
    fetch = _load_fetch_sqlite_vec()
    path = fetch.installed_loadable_path("linux")
    assert path.name == "vec0.so"


def test_installed_loadable_path_for_macos() -> None:
    fetch = _load_fetch_sqlite_vec()
    path = fetch.installed_loadable_path("macos-arm64")
    assert path.name == "vec0.dylib"


def test_fetch_windows_arm64_returns_vec0_arm64_dll_when_present(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fetch = _load_fetch_sqlite_vec()
    vendor = tmp_path / "sqlite_vec"
    vendor.mkdir()
    dll = vendor / "vec0.arm64.dll"
    dll.write_bytes(b"fake-dll")

    monkeypatch.setattr(
        fetch,
        "installed_loadable_path",
        lambda _key: vendor / "vec0.arm64.dll",
    )

    result = fetch.fetch_sqlite_vec(platform_key="windows-arm64")

    assert result == dll


def test_fetch_windows_arm64_missing_dll_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fetch = _load_fetch_sqlite_vec()
    vendor = tmp_path / "sqlite_vec"
    vendor.mkdir()

    monkeypatch.setattr(
        fetch,
        "installed_loadable_path",
        lambda _key: vendor / "vec0.arm64.dll",
    )

    with pytest.raises(RuntimeError, match="build_sqlite_vec_windows.ps1"):
        fetch.fetch_sqlite_vec(platform_key="windows-arm64")


def test_install_loadable_preserves_other_platform_binaries(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fetch = _load_fetch_sqlite_vec()
    vendor = tmp_path / "vec"
    vendor.mkdir()
    (vendor / "vec0.dylib").write_bytes(b"keep-dylib")
    (vendor / "vec0.so").write_bytes(b"keep-so")
    source = tmp_path / "vec0.dll"
    source.write_bytes(b"windows-dll")

    monkeypatch.setattr(fetch, "destination_path", lambda _key: vendor / "vec0")

    installed = fetch._install_loadable(source, "windows")

    assert installed == vendor / "vec0.dll"
    assert (vendor / "vec0.dll").read_bytes() == b"windows-dll"
    assert (vendor / "vec0.dylib").read_bytes() == b"keep-dylib"
    assert (vendor / "vec0.so").read_bytes() == b"keep-so"
