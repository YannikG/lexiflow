"""Sync project version into lexiflow_core.__version__ before release builds."""

from __future__ import annotations

import os
import re
from pathlib import Path


def _read_pyproject_version(repo_root: Path) -> str:
    pyproject = (repo_root / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', pyproject, re.MULTILINE)
    if match is None:
        raise RuntimeError(f"version not found in {repo_root / 'pyproject.toml'}")
    return match.group(1)


def resolve_build_version(*, repo_root: Path) -> str:
    """Return version from GITHUB_REF_NAME (vX.Y.Z) or root pyproject.toml."""
    ref_name = os.environ.get("GITHUB_REF_NAME", "").strip()
    if ref_name.startswith("v") and ref_name[1:]:
        return ref_name.lstrip("v")
    return _read_pyproject_version(repo_root)


def write_core_version(*, repo_root: Path, version: str) -> Path:
    """Write __version__ into lexiflow_core/__init__.py."""
    core_init = repo_root / "packages/lexiflow-core/src/lexiflow_core/__init__.py"
    if not core_init.is_file():
        raise FileNotFoundError(f"core package init not found: {core_init}")
    content = core_init.read_text(encoding="utf-8")
    updated, count = re.subn(
        r'^__version__\s*=\s*"[^"]*"',
        f'__version__ = "{version}"',
        content,
        count=1,
        flags=re.MULTILINE,
    )
    if count != 1:
        raise RuntimeError(f"could not update __version__ in {core_init}")
    core_init.write_text(updated, encoding="utf-8")
    return core_init


def sync_version(*, repo_root: Path | None = None) -> str:
    """Resolve build version and write it to lexiflow_core."""
    root = repo_root if repo_root is not None else Path(__file__).resolve().parents[2]
    version = resolve_build_version(repo_root=root)
    write_core_version(repo_root=root, version=version)
    return version


def main() -> int:
    version = sync_version()
    print(version)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
