"""Compute and write the next release version for prepare-release automation."""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

from lexiflow_core.version_compare import (
    bump_semver,
    semver_max,
)
from lexiflow_core.version_compare import (
    parse_semver_triple as parse_semver,
)


def _load_sync_version():
    script = Path(__file__).resolve().parent / "sync_version.py"
    spec = importlib.util.spec_from_file_location("lexiflow_sync_version", script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load sync_version from {script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_sync = _load_sync_version()
latest_git_tag_version = _sync.latest_git_tag_version
read_pyproject_version = _sync.read_pyproject_version
write_core_version = _sync.write_core_version
write_pyproject_version = _sync.write_pyproject_version


def resolve_base_version(*, repo_root: Path) -> str:
    """Latest released tag version, or ``pyproject.toml`` when no tag exists."""
    tag_version = latest_git_tag_version(repo_root=repo_root)
    pyproject_version = read_pyproject_version(repo_root=repo_root)
    if tag_version is None:
        return pyproject_version
    return semver_max(tag_version, pyproject_version)


def next_release_version(*, repo_root: Path, bump: str) -> str:
    """Next ``X.Y.Z`` from the greater of latest tag and ``pyproject.toml``."""
    return bump_semver(resolve_base_version(repo_root=repo_root), bump)


def should_auto_prepare(*, repo_root: Path) -> bool:
    """True when ``pyproject.toml`` is behind the latest ``v*`` tag on the remote."""
    tag_version = latest_git_tag_version(repo_root=repo_root)
    if tag_version is None:
        return False
    pyproject_version = read_pyproject_version(repo_root=repo_root)
    return parse_semver(pyproject_version) < parse_semver(tag_version)


def bump_release_files(*, repo_root: Path, bump: str) -> str:
    """Write the next version to pyproject.toml and lexiflow_core.__version__."""
    version = next_release_version(repo_root=repo_root, bump=bump)
    write_pyproject_version(repo_root=repo_root, version=version)
    write_core_version(repo_root=repo_root, version=version)
    return version


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bump LexiFlow release version")
    parser.add_argument(
        "--bump",
        choices=("patch", "minor", "major"),
        default="patch",
        help="Semver bump applied to max(latest tag, pyproject)",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write pyproject.toml and lexiflow_core.__version__",
    )
    parser.add_argument(
        "--check-auto",
        action="store_true",
        help="Exit 0 when auto prepare-release should run, else 1",
    )
    args = parser.parse_args(argv)
    repo_root = Path(__file__).resolve().parents[2]

    if args.check_auto:
        return 0 if should_auto_prepare(repo_root=repo_root) else 1

    version = (
        bump_release_files(repo_root=repo_root, bump=args.bump)
        if args.write
        else next_release_version(repo_root=repo_root, bump=args.bump)
    )
    print(version)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
