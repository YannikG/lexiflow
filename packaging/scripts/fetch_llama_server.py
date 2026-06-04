"""Download a pinned llama.cpp prebuilt llama-server for packaging."""

from __future__ import annotations

import argparse
import importlib.util
import os
import platform
import shutil
import stat
import sys
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from types import ModuleType


def _load_llama_runtime_libs() -> ModuleType:
    script = Path(__file__).resolve().parent / "llama_runtime_libs.py"
    spec = importlib.util.spec_from_file_location("lexiflow_llama_runtime_libs", script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_llama_runtime = _load_llama_runtime_libs()
copy_runtime_libs = _llama_runtime.copy_runtime_libs

DEFAULT_RELEASE = "b9500"
GITHUB_RELEASE_BASE = "https://github.com/ggml-org/llama.cpp/releases/download"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


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
    raise RuntimeError(f"unsupported platform for llama-server fetch: {system}")


def asset_name(release: str, platform_key: str) -> tuple[str, str]:
    """Return GitHub release asset filename and archive type for a platform key."""
    tag = release if release.startswith("b") else f"b{release}"
    if platform_key == "linux":
        return f"llama-{tag}-bin-ubuntu-x64.tar.gz", "tar.gz"
    if platform_key == "macos-arm64":
        return f"llama-{tag}-bin-macos-arm64.tar.gz", "tar.gz"
    if platform_key == "macos-x64":
        return f"llama-{tag}-bin-macos-x64.tar.gz", "tar.gz"
    if platform_key == "windows":
        return f"llama-{tag}-bin-win-cpu-x64.zip", "zip"
    if platform_key == "windows-arm64":
        return f"llama-{tag}-bin-win-cpu-arm64.zip", "zip"
    raise RuntimeError(f"unknown platform key: {platform_key}")


def _download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "LexiFlow-packaging"})
    with urllib.request.urlopen(request, timeout=120) as response:
        with destination.open("wb") as handle:
            while chunk := response.read(8192):
                handle.write(chunk)


def _extract_llama_server(
    archive: Path,
    archive_type: str,
    destination: Path,
    *,
    platform_key: str,
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    binary_name = destination.name
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        if archive_type == "tar.gz":
            with tarfile.open(archive, "r:gz") as tar:
                tar.extractall(temp_path, filter="data")
        else:
            with zipfile.ZipFile(archive, "r") as zf:
                zf.extractall(temp_path)
        matches = list(temp_path.rglob(binary_name))
        if not matches:
            raise FileNotFoundError(f"{binary_name} not found in {archive}")
        source_binary = matches[0]
        shutil.copy2(source_binary, destination)
        lib_count = copy_runtime_libs(
            source_binary.parent,
            destination.parent,
            platform_key,
        )
        if lib_count == 0 and not platform_key.startswith("windows"):
            raise FileNotFoundError(
                f"no runtime libraries found next to {binary_name} in {archive}"
            )
    if not destination.name.endswith(".exe"):
        mode = destination.stat().st_mode
        destination.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def fetch_llama_server(
    *,
    platform_key: str | None = None,
    release: str | None = None,
    output_dir: Path | None = None,
) -> Path:
    """Download llama-server into packaging/bin/<platform_key>/."""
    key = platform_key if platform_key is not None else detect_platform_key()
    tag = (
        release
        if release is not None
        else os.environ.get("LLAMA_CPP_RELEASE", DEFAULT_RELEASE)
    )
    asset_filename, archive_type = asset_name(tag, key)
    url = f"{GITHUB_RELEASE_BASE}/{tag}/{asset_filename}"
    root = _repo_root()
    target_dir = (
        output_dir if output_dir is not None else root / "packaging" / "bin" / key
    )
    binary_name = "llama-server.exe" if key.startswith("windows") else "llama-server"
    destination = target_dir / binary_name
    with tempfile.TemporaryDirectory() as temp_dir:
        archive = Path(temp_dir) / asset_filename
        print(f"Downloading {url}", file=sys.stderr)
        _download(url, archive)
        _extract_llama_server(archive, archive_type, destination, platform_key=key)
    print(destination)
    return destination


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fetch llama-server for LexiFlow packaging",
    )
    parser.add_argument(
        "--platform",
        choices=["linux", "macos-arm64", "macos-x64", "windows", "windows-arm64"],
        default=None,
    )
    parser.add_argument("--release", default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args(argv)
    fetch_llama_server(
        platform_key=args.platform,
        release=args.release,
        output_dir=args.output_dir,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
