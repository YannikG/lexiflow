"""Download sqlite-vec and SQLite amalgamation sources for Windows ARM64 MSVC build."""

from __future__ import annotations

import argparse
import shutil
import urllib.request
import zipfile
from pathlib import Path

SQLITE_VEC_VERSION = "0.1.9"
SQLITE_VEC_AMALGAMATION_URL = (
    "https://github.com/asg017/sqlite-vec/releases/download/"
    f"v{SQLITE_VEC_VERSION}/sqlite-vec-{SQLITE_VEC_VERSION}-amalgamation.zip"
)
SQLITE_AMALGAMATION_URL = "https://www.sqlite.org/2024/sqlite-amalgamation-3450300.zip"


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
    extracted = scratch_dir / "sqlite-amalgamation-3450300"
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
