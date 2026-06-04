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
