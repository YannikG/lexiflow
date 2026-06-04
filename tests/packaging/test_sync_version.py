"""Tests for build-time version sync."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_sync_version():
    script = (
        Path(__file__).resolve().parents[2]
        / "packaging"
        / "scripts"
        / "sync_version.py"
    )
    spec = importlib.util.spec_from_file_location("lexiflow_sync_version", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_sync_version_writes_core_init_from_pyproject(
    tmp_path: Path, monkeypatch
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "pyproject.toml").write_text(
        '[project]\nname = "lexiflow"\nversion = "1.2.3"\n',
        encoding="utf-8",
    )
    core_init = repo_root / "packages/lexiflow-core/src/lexiflow_core/__init__.py"
    core_init.parent.mkdir(parents=True)
    core_init.write_text('__version__ = "0.0.0"\n', encoding="utf-8")
    monkeypatch.delenv("GITHUB_REF_NAME", raising=False)
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.delenv("GITHUB_RUN_NUMBER", raising=False)
    monkeypatch.delenv("LF_SYNC_CI_DEV", raising=False)

    sync_version = _load_sync_version().sync_version
    version = sync_version(repo_root=repo_root)

    assert version == "1.2.3"
    assert '__version__ = "1.2.3"' in core_init.read_text(encoding="utf-8")


def test_sync_version_reads_github_ref_name(tmp_path: Path, monkeypatch) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "pyproject.toml").write_text(
        '[project]\nname = "lexiflow"\nversion = "0.0.0"\n',
        encoding="utf-8",
    )
    core_init = repo_root / "packages/lexiflow-core/src/lexiflow_core/__init__.py"
    core_init.parent.mkdir(parents=True)
    core_init.write_text('__version__ = "0.0.0"\n', encoding="utf-8")
    monkeypatch.setenv("GITHUB_REF_NAME", "v2.0.1")

    sync_version = _load_sync_version().sync_version
    version = sync_version(repo_root=repo_root)

    assert version == "2.0.1"
    assert '__version__ = "2.0.1"' in core_init.read_text(encoding="utf-8")


def test_sync_version_uses_ci_dev_suffix_on_pr_builds(
    tmp_path: Path, monkeypatch
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "pyproject.toml").write_text(
        '[project]\nname = "lexiflow"\nversion = "1.0.0"\n',
        encoding="utf-8",
    )
    core_init = repo_root / "packages/lexiflow-core/src/lexiflow_core/__init__.py"
    core_init.parent.mkdir(parents=True)
    core_init.write_text('__version__ = "0.0.0"\n', encoding="utf-8")
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("LF_SYNC_CI_DEV", "1")
    monkeypatch.setenv("GITHUB_REF_NAME", "feature/phase-15")
    monkeypatch.setenv("GITHUB_RUN_NUMBER", "42")

    sync_version = _load_sync_version().sync_version
    version = sync_version(repo_root=repo_root)

    assert version == "1.0.0.dev42"
    assert '__version__ = "1.0.0.dev42"' in core_init.read_text(encoding="utf-8")


def test_sync_version_resolve_only_does_not_write_files(
    tmp_path: Path, monkeypatch
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    pyproject = repo_root / "pyproject.toml"
    pyproject.write_text(
        '[project]\nname = "lexiflow"\nversion = "2.3.4"\n',
        encoding="utf-8",
    )
    core_init = repo_root / "packages/lexiflow-core/src/lexiflow_core/__init__.py"
    core_init.parent.mkdir(parents=True)
    core_init.write_text('__version__ = "0.0.0"\n', encoding="utf-8")
    monkeypatch.delenv("GITHUB_REF_NAME", raising=False)

    sync_version = _load_sync_version()
    version = sync_version.resolve_build_version(repo_root=repo_root)

    assert version == "2.3.4"
    assert '__version__ = "0.0.0"' in core_init.read_text(encoding="utf-8")


def test_sync_version_can_write_pyproject(tmp_path: Path, monkeypatch) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    pyproject = repo_root / "pyproject.toml"
    pyproject.write_text(
        '[project]\nname = "lexiflow"\nversion = "0.0.0"\n',
        encoding="utf-8",
    )
    core_init = repo_root / "packages/lexiflow-core/src/lexiflow_core/__init__.py"
    core_init.parent.mkdir(parents=True)
    core_init.write_text('__version__ = "0.0.0"\n', encoding="utf-8")
    monkeypatch.setenv("GITHUB_REF_NAME", "v3.4.5")

    sync_version = _load_sync_version().sync_version
    version = sync_version(repo_root=repo_root, write_pyproject=True)

    assert version == "3.4.5"
    assert 'version = "3.4.5"' in pyproject.read_text(encoding="utf-8")
