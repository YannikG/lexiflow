"""Sync project version into lexiflow_core.__version__ before release builds."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
from pathlib import Path


def _read_pyproject_version(repo_root: Path) -> str:
    pyproject = (repo_root / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', pyproject, re.MULTILINE)
    if match is None:
        raise RuntimeError(f"version not found in {repo_root / 'pyproject.toml'}")
    return match.group(1)


def _latest_git_tag_version(repo_root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0", "--match", "v*"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    tag = result.stdout.strip()
    if tag.startswith("v") and tag[1:]:
        return tag.removeprefix("v")
    return tag or None


def _ci_dev_version(repo_root: Path) -> str | None:
    if os.environ.get("GITHUB_ACTIONS") != "true":
        return None
    ref_name = os.environ.get("GITHUB_REF_NAME", "").strip()
    if ref_name.startswith("v"):
        return None
    run_number = os.environ.get("GITHUB_RUN_NUMBER", "").strip()
    if not run_number:
        return None
    base = _latest_git_tag_version(repo_root) or _read_pyproject_version(repo_root)
    return f"{base}.dev{run_number}"


def resolve_build_version(*, repo_root: Path) -> str:
    """Return version from release tag, CI dev build, or pyproject.toml."""
    ref_name = os.environ.get("GITHUB_REF_NAME", "").strip()
    if ref_name.startswith("v") and ref_name[1:]:
        return ref_name.removeprefix("v")
    ci_version = _ci_dev_version(repo_root)
    if ci_version is not None:
        return ci_version
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


def write_pyproject_version(*, repo_root: Path, version: str) -> Path:
    """Write version into root pyproject.toml."""
    pyproject = repo_root / "pyproject.toml"
    content = pyproject.read_text(encoding="utf-8")
    updated, count = re.subn(
        r'^(version\s*=\s*)"[^"]*"',
        rf'\1"{version}"',
        content,
        count=1,
        flags=re.MULTILINE,
    )
    if count != 1:
        raise RuntimeError(f"could not update version in {pyproject}")
    pyproject.write_text(updated, encoding="utf-8")
    return pyproject


def sync_version(
    *,
    repo_root: Path | None = None,
    write_pyproject: bool = False,
) -> str:
    """Resolve build version and write it to lexiflow_core."""
    root = repo_root if repo_root is not None else Path(__file__).resolve().parents[2]
    version = resolve_build_version(repo_root=root)
    write_core_version(repo_root=root, version=version)
    if write_pyproject:
        write_pyproject_version(repo_root=root, version=version)
    return version


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sync LexiFlow build version")
    parser.add_argument(
        "--write-pyproject",
        action="store_true",
        help="Also write resolved version to root pyproject.toml",
    )
    args = parser.parse_args(argv)
    version = sync_version(write_pyproject=args.write_pyproject)
    print(version)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
