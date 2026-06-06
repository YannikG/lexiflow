"""Tests for vendored sqlite_vec loadable path resolution."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


def test_loadable_path_uses_meipass_when_frozen(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import sqlite_vec

    bundle_root = tmp_path / "bundle"
    bundle_vec = bundle_root / "sqlite_vec"
    bundle_vec.mkdir(parents=True)
    (bundle_vec / "vec0.dylib").write_bytes(b"fake-dylib")

    empty_pkg = tmp_path / "empty_pkg"
    empty_pkg.mkdir()

    monkeypatch.setattr(
        sqlite_vec,
        "_search_directories",
        lambda: [str(bundle_vec), str(empty_pkg)],
    )

    assert sqlite_vec.loadable_path() == str(bundle_vec / "vec0")


def test_loadable_path_prefers_package_dir_when_loadable_present(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import sqlite_vec

    package_dir = tmp_path / "sqlite_vec"
    package_dir.mkdir()
    (package_dir / "__init__.py").write_text("", encoding="utf-8")
    (package_dir / "vec0.dylib").write_bytes(b"fake-dylib")

    monkeypatch.setattr(sqlite_vec, "__file__", str(package_dir / "__init__.py"))
    monkeypatch.setattr(sys, "frozen", False, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", "", raising=False)

    assert sqlite_vec.loadable_path() == str(package_dir / "vec0")


def test_loadable_path_raises_when_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import sqlite_vec

    empty_pkg = tmp_path / "empty_pkg"
    empty_pkg.mkdir()

    monkeypatch.setattr(
        sqlite_vec,
        "_search_directories",
        lambda: [str(empty_pkg)],
    )

    with pytest.raises(FileNotFoundError, match="sqlite-vec loadable"):
        sqlite_vec.loadable_path()


def test_loadable_path_resolves_windows_arm64_stem(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import sqlite_vec

    package_dir = tmp_path / "sqlite_vec"
    package_dir.mkdir()
    (package_dir / "__init__.py").write_text("", encoding="utf-8")
    (package_dir / "vec0.arm64.dll").write_bytes(b"fake-dll")

    monkeypatch.setattr(sqlite_vec, "__file__", str(package_dir / "__init__.py"))
    monkeypatch.setattr(sqlite_vec.platform, "system", lambda: "Windows")
    monkeypatch.setattr(sqlite_vec.platform, "machine", lambda: "ARM64")
    monkeypatch.setattr(sys, "frozen", False, raising=False)

    assert sqlite_vec.loadable_path() == str(package_dir / "vec0.arm64")


def test_loadable_path_falls_back_to_repo_vendor_when_site_packages_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import sqlite_vec

    repo_root = tmp_path / "repo"
    vendor_vec = repo_root / "packaging" / "vendor" / "sqlite_vec" / "sqlite_vec"
    vendor_vec.mkdir(parents=True)
    (vendor_vec / "vec0.dylib").write_bytes(b"fake-dylib")

    site_packages = tmp_path / "site-packages" / "sqlite_vec"
    site_packages.mkdir(parents=True)
    (site_packages / "__init__.py").write_text("", encoding="utf-8")

    monkeypatch.setattr(sqlite_vec, "__file__", str(site_packages / "__init__.py"))
    monkeypatch.setattr(sqlite_vec, "_dev_vendor_directory", lambda: str(vendor_vec))

    assert sqlite_vec.loadable_path() == str(vendor_vec / "vec0")
