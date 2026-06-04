"""Tests for Windows ARM64 sqlite-vec source preparation."""

from __future__ import annotations

import importlib.util
import zipfile
from pathlib import Path


def _load_prepare_sqlite_vec_windows_arm64():
    script = (
        Path(__file__).resolve().parents[2]
        / "packaging"
        / "scripts"
        / "prepare_sqlite_vec_windows_arm64.py"
    )
    spec = importlib.util.spec_from_file_location(
        "lexiflow_prepare_sqlite_vec_windows_arm64",
        script,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_minimal_sqlite_vec_amalgamation(work_dir: Path) -> None:
    (work_dir / "sqlite-vec.c").write_text(
        '#include "sqlite-vec.h"\n',
        encoding="utf-8",
    )
    (work_dir / "sqlite-vec.h").write_text(
        "#ifndef SQLITE_VEC_H\n#endif\n",
        encoding="utf-8",
    )


def _write_minimal_sqlite_amalgamation_zip(archive: Path) -> None:
    sqlite_dir = archive.parent / "sqlite-amalgamation-3450300"
    sqlite_dir.mkdir()
    (sqlite_dir / "sqlite3ext.h").write_text("/* ext */\n", encoding="utf-8")
    (sqlite_dir / "sqlite3.h").write_text("/* sqlite3 */\n", encoding="utf-8")
    with zipfile.ZipFile(archive, "w") as zf:
        for path in sqlite_dir.rglob("*"):
            if path.is_file():
                zf.write(path, path.relative_to(archive.parent))
    shutil_rmtree = __import__("shutil").rmtree
    shutil_rmtree(sqlite_dir)


def test_vendor_sqlite_amalgamation_copies_headers(tmp_path: Path, monkeypatch) -> None:
    prepare = _load_prepare_sqlite_vec_windows_arm64()
    scratch = tmp_path / "scratch"
    scratch.mkdir()

    def fake_download(url: str, destination: Path) -> None:
        _write_minimal_sqlite_amalgamation_zip(destination)

    monkeypatch.setattr(prepare, "_download", fake_download)

    vendor_dir = tmp_path / "vendor"
    prepare.vendor_sqlite_amalgamation(vendor_dir, scratch_dir=scratch)

    assert (vendor_dir / "sqlite3ext.h").is_file()
    assert (vendor_dir / "sqlite3.h").is_file()


def test_prepare_windows_arm64_build_tree_layout(tmp_path: Path, monkeypatch) -> None:
    prepare = _load_prepare_sqlite_vec_windows_arm64()
    work_dir = tmp_path / "work"

    def fake_download(url: str, destination: Path) -> None:
        if "sqlite-vec" in url:
            staging = destination.parent / "vec-staging"
            staging.mkdir()
            _write_minimal_sqlite_vec_amalgamation(staging)
            with zipfile.ZipFile(destination, "w") as zf:
                for path in staging.iterdir():
                    if path.is_file():
                        zf.write(path, path.name)
        elif "sqlite.org" in url:
            _write_minimal_sqlite_amalgamation_zip(destination)
        else:
            raise AssertionError(f"unexpected download url: {url}")

    monkeypatch.setattr(prepare, "_download", fake_download)

    result = prepare.prepare_windows_arm64_build_tree(work_dir)

    assert result == work_dir
    assert (work_dir / "sqlite-vec.c").is_file()
    assert (work_dir / "sqlite-vec.h").is_file()
    assert (work_dir / "vendor" / "sqlite3ext.h").is_file()
