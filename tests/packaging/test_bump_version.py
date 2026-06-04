"""Tests for release version bump script."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_bump_version():
    script = (
        Path(__file__).resolve().parents[2]
        / "packaging"
        / "scripts"
        / "bump_version.py"
    )
    spec = importlib.util.spec_from_file_location("lexiflow_bump_version", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _init_repo(repo_root: Path, *, pyproject: str, core: str) -> None:
    repo_root.mkdir()
    (repo_root / "pyproject.toml").write_text(
        f'[project]\nname = "lexiflow"\nversion = "{pyproject}"\n',
        encoding="utf-8",
    )
    core_init = repo_root / "packages/lexiflow-core/src/lexiflow_core/__init__.py"
    core_init.parent.mkdir(parents=True)
    core_init.write_text(f'__version__ = "{core}"\n', encoding="utf-8")


def test_next_release_version_bumps_from_latest_tag(
    tmp_path: Path, monkeypatch
) -> None:
    repo_root = tmp_path / "repo"
    _init_repo(repo_root, pyproject="0.0.0", core="0.0.0")

    bump = _load_bump_version()
    monkeypatch.setattr(bump, "latest_git_tag_version", lambda *, repo_root: "1.0.4")

    assert bump.next_release_version(repo_root=repo_root, bump="patch") == "1.0.5"
    assert bump.next_release_version(repo_root=repo_root, bump="minor") == "1.1.0"


def test_should_auto_prepare_when_pyproject_behind_tag(
    tmp_path: Path, monkeypatch
) -> None:
    repo_root = tmp_path / "repo"
    _init_repo(repo_root, pyproject="0.0.0", core="0.0.0")
    bump = _load_bump_version()
    monkeypatch.setattr(bump, "latest_git_tag_version", lambda *, repo_root: "1.0.4")

    assert bump.should_auto_prepare(repo_root=repo_root) is True


def test_should_auto_prepare_skips_when_versions_match(
    tmp_path: Path, monkeypatch
) -> None:
    repo_root = tmp_path / "repo"
    _init_repo(repo_root, pyproject="1.0.4", core="1.0.4")
    bump = _load_bump_version()
    monkeypatch.setattr(bump, "latest_git_tag_version", lambda *, repo_root: "1.0.4")

    assert bump.should_auto_prepare(repo_root=repo_root) is False


def test_bump_release_files_writes_pyproject_and_core(
    tmp_path: Path, monkeypatch
) -> None:
    repo_root = tmp_path / "repo"
    _init_repo(repo_root, pyproject="0.0.0", core="0.0.0")
    bump = _load_bump_version()
    monkeypatch.setattr(bump, "latest_git_tag_version", lambda *, repo_root: "1.0.4")

    version = bump.bump_release_files(repo_root=repo_root, bump="patch")

    assert version == "1.0.5"
    pyproject_path = repo_root / "pyproject.toml"
    pyproject = pyproject_path.read_text(encoding="utf-8")
    assert 'version = "1.0.5"' in pyproject
    core_init = repo_root / "packages/lexiflow-core/src/lexiflow_core/__init__.py"
    assert '__version__ = "1.0.5"' in core_init.read_text(encoding="utf-8")
