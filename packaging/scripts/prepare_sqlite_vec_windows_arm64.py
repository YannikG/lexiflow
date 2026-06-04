"""Download sqlite-vec and SQLite amalgamation sources for Windows ARM64 MSVC build."""

from __future__ import annotations

import argparse
import importlib.util
import io
import shutil
import urllib.request
import zipfile
from pathlib import Path

# Matches upstream scripts/vendor.sh (sqlite-vec v0.1.9).
SQLITE_AMALGAMATION_URL = "https://www.sqlite.org/2024/sqlite-amalgamation-3450300.zip"


def _load_fetch_sqlite_vec():
    script = Path(__file__).resolve().parent / "fetch_sqlite_vec.py"
    spec = importlib.util.spec_from_file_location("lexiflow_fetch_sqlite_vec", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_fetch = _load_fetch_sqlite_vec()
SQLITE_VEC_VERSION = _fetch.SQLITE_VEC_VERSION
SQLITE_VEC_AMALGAMATION_URL = (
    f"{_fetch.GITHUB_RELEASE_BASE}/sqlite-vec-{SQLITE_VEC_VERSION}-amalgamation.zip"
)


def _download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "LexiFlow-packaging"})
    with urllib.request.urlopen(request, timeout=120) as response:
        with destination.open("wb") as handle:
            while chunk := response.read(8192):
                handle.write(chunk)


def vendor_sqlite_amalgamation(vendor_dir: Path, *, scratch_dir: Path) -> None:
    """Populate ``vendor_dir`` with SQLite headers required by sqlite-vec.c."""
    archive = scratch_dir / "sqlite-amalgamation.zip"
    _download(SQLITE_AMALGAMATION_URL, archive)
    with zipfile.ZipFile(archive, "r") as zip_archive:
        zip_archive.extractall(scratch_dir)
    extracted = scratch_dir / Path(SQLITE_AMALGAMATION_URL).stem
    if not extracted.is_dir():
        raise FileNotFoundError("sqlite amalgamation directory missing after extract")
    vendor_dir.mkdir(parents=True, exist_ok=True)
    for name in ("sqlite3ext.h", "sqlite3.h"):
        source = extracted / name
        if not source.is_file():
            raise FileNotFoundError(f"{name} missing in sqlite amalgamation")
        shutil.copy2(source, vendor_dir / name)


def prepare_windows_arm64_build_tree(work_dir: Path) -> Path:
    """Extract amalgamation sources and vendor SQLite headers under ``work_dir``."""
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True)
    scratch = work_dir / ".download"
    scratch.mkdir()

    vec_archive = scratch / "sqlite-vec-amalgamation.zip"
    _download(SQLITE_VEC_AMALGAMATION_URL, vec_archive)
    with zipfile.ZipFile(vec_archive, "r") as zip_archive:
        zip_archive.extractall(work_dir)

    for required in ("sqlite-vec.c", "sqlite-vec.h"):
        if not (work_dir / required).is_file():
            raise FileNotFoundError(f"{required} missing from sqlite-vec amalgamation")

    vendor_sqlite_amalgamation(work_dir / "vendor", scratch_dir=scratch)
    shutil.rmtree(scratch)
    return work_dir


def official_amalgamation_root_files() -> set[str]:
    """Return top-level file names in the published sqlite-vec amalgamation zip."""
    request = urllib.request.Request(
        SQLITE_VEC_AMALGAMATION_URL,
        headers={"User-Agent": "LexiFlow-packaging"},
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        payload = response.read()
    with zipfile.ZipFile(io.BytesIO(payload), "r") as zip_archive:
        return {name for name in zip_archive.namelist() if "/" not in name}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "work_dir",
        type=Path,
        help="Directory to populate with sqlite-vec.c, sqlite-vec.h, and vendor/",
    )
    args = parser.parse_args(argv)
    path = prepare_windows_arm64_build_tree(args.work_dir.resolve())
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
