"""Shared helpers for bundling llama-server and its platform runtime libraries."""

from __future__ import annotations

import shutil
from pathlib import Path


def runtime_lib_globs(platform_key: str) -> tuple[str, ...]:
    """Return glob patterns for shared libraries shipped next to llama-server."""
    if platform_key.startswith("windows"):
        return ("*.dll",)
    if platform_key.startswith("macos"):
        return ("*.dylib",)
    return ("*.so", "*.so.*")


def copy_runtime_libs(
    source_dir: Path,
    destination_dir: Path,
    platform_key: str,
) -> int:
    """Copy llama.cpp shared libraries beside the llama-server binary."""
    destination_dir.mkdir(parents=True, exist_ok=True)
    copied = 0
    seen: set[str] = set()
    for pattern in runtime_lib_globs(platform_key):
        for lib_path in sorted(source_dir.glob(pattern)):
            if not lib_path.is_file() or lib_path.name in seen:
                continue
            seen.add(lib_path.name)
            shutil.copy2(lib_path, destination_dir / lib_path.name)
            copied += 1
    return copied
