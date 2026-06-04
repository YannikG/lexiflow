"""Download or build sqlite-vec loadable binaries for vendored packaging."""

from __future__ import annotations

import argparse
import platform
import shutil
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path

SQLITE_VEC_VERSION = "0.1.9"
GITHUB_RELEASE_BASE = (
    f"https://github.com/asg017/sqlite-vec/releases/download/v{SQLITE_VEC_VERSION}"
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _vendor_vec_dir() -> Path:
    return _repo_root() / "packaging" / "vendor" / "sqlite_vec" / "sqlite_vec"


def detect_platform_key() -> str:
    """Return packaging platform key for the current host OS and CPU."""
    system = platform.system()
    machine = platform.machine().lower()
    if system == "Linux":
        return "linux"
    if system == "Darwin":
        return "macos-arm64" if machine in {"arm64", "aarch64"} else "macos-x64"
    if system == "Windows":
        return "windows-arm64" if machine in {"arm64", "aarch64"} else "windows"
    raise RuntimeError(f"unsupported platform for sqlite-vec fetch: {system}")


def loadable_asset(platform_key: str) -> tuple[str, str, str]:
    """Return release asset name, archive type, and installed filename stem."""
    if platform_key == "linux":
        return (
            f"sqlite-vec-{SQLITE_VEC_VERSION}-loadable-linux-x86_64.tar.gz",
            "tar.gz",
            "vec0",
        )
    if platform_key == "macos-arm64":
        return (
            f"sqlite-vec-{SQLITE_VEC_VERSION}-loadable-macos-aarch64.tar.gz",
            "tar.gz",
            "vec0",
        )
    if platform_key == "macos-x64":
        return (
            f"sqlite-vec-{SQLITE_VEC_VERSION}-loadable-macos-x86_64.tar.gz",
            "tar.gz",
            "vec0",
        )
    if platform_key == "windows":
        return (
            f"sqlite-vec-{SQLITE_VEC_VERSION}-loadable-windows-x86_64.tar.gz",
            "tar.gz",
            "vec0",
        )
    if platform_key == "windows-arm64":
        return ("", "", "vec0.arm64")
    raise RuntimeError(f"unknown platform key: {platform_key}")


def destination_path(platform_key: str) -> Path:
    """Return vendor path for the platform loadable file (without extension)."""
    _, _, stem = loadable_asset(platform_key)
    return _vendor_vec_dir() / stem


def _download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "LexiFlow-packaging"})
    with urllib.request.urlopen(request, timeout=120) as response:
        with destination.open("wb") as handle:
            while chunk := response.read(8192):
                handle.write(chunk)


def _find_loadable(extracted_root: Path, stem: str) -> Path:
    for suffix in (".dll", ".dylib", ".so"):
        matches = list(extracted_root.rglob(f"{stem}{suffix}"))
        if matches:
            return matches[0]
    matches = list(extracted_root.rglob(stem))
    if matches:
        return matches[0]
    raise FileNotFoundError(f"{stem} loadable not found under {extracted_root}")


def _install_loadable(source: Path, platform_key: str) -> Path:
    dest_base = destination_path(platform_key)
    dest_base.parent.mkdir(parents=True, exist_ok=True)
    suffix = source.suffix
    if suffix:
        dest = dest_base.with_suffix(suffix)
        for old in dest_base.parent.glob(f"{dest_base.name}.*"):
            old.unlink(missing_ok=True)
    else:
        dest = dest_base
        if dest.exists():
            dest.unlink()
    shutil.copy2(source, dest)
    return dest


def fetch_prebuilt(platform_key: str) -> Path:
    """Download an official sqlite-vec loadable release asset."""
    asset_name, archive_type, stem = loadable_asset(platform_key)
    url = f"{GITHUB_RELEASE_BASE}/{asset_name}"
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        archive = temp_path / asset_name
        _download(url, archive)
        extract_root = temp_path / "extract"
        extract_root.mkdir()
        if archive_type == "tar.gz":
            with tarfile.open(archive, "r:gz") as tar:
                tar.extractall(extract_root, filter="data")
        else:
            with zipfile.ZipFile(archive, "r") as zf:
                zf.extractall(extract_root)
        loadable = _find_loadable(extract_root, stem)
        return _install_loadable(loadable, platform_key)


def fetch_sqlite_vec(*, platform_key: str | None = None) -> Path:
    """Populate vendored sqlite-vec loadable for a packaging platform key."""
    key = platform_key if platform_key is not None else detect_platform_key()
    if key == "windows-arm64":
        msg = (
            "windows-arm64 requires build_sqlite_vec_windows.ps1; "
            "run that script before fetch_sqlite_vec"
        )
        dest = destination_path(key).with_suffix(".dll")
        if not dest.is_file():
            raise RuntimeError(msg)
        return dest
    return fetch_prebuilt(key)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fetch sqlite-vec loadable for packaging",
    )
    parser.add_argument(
        "--platform",
        required=True,
        choices=[
            "linux",
            "macos-arm64",
            "macos-x64",
            "windows",
            "windows-arm64",
        ],
    )
    args = parser.parse_args(argv)
    path = fetch_sqlite_vec(platform_key=args.platform)
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
