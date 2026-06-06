"""Tests for release bundle smoke script helpers."""

from __future__ import annotations

import subprocess
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _discovery_script() -> Path:
    return _repo_root() / "packaging/scripts/smoke_bundle_discovery.sh"


def _smoke_script() -> Path:
    return _repo_root() / "packaging/scripts/smoke_bundle.sh"


def _list_llama_server_candidates(path_glob: str, *roots: Path) -> list[str]:
    discovery_script = _discovery_script()
    command = f'source "{discovery_script}"; list_bundled_llama_server_candidates "$@"'
    result = subprocess.run(
        ["bash", "-c", command, "--", path_glob, *[str(root) for root in roots]],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return [line for line in result.stdout.splitlines() if line]


def _list_sqlite_vec_loadables(*roots: Path) -> list[str]:
    discovery_script = _discovery_script()
    command = (
        f'source "{discovery_script}"; '
        'for root in "$@"; do list_bundled_sqlite_vec_loadables "$root"; done'
    )
    result = subprocess.run(
        ["bash", "-c", command, "--", *[str(root) for root in roots]],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return [line for line in result.stdout.splitlines() if line]


def test_smoke_bundle_script_resolves_windows_exe() -> None:
    script = _smoke_script().read_text(encoding="utf-8")
    assert "LexiFlow.exe" in script
    assert "--sqlite-vec-smoke" in script
    assert "list_bundled_sqlite_vec_loadables" in script
    assert "llama-server.exe" in script
    assert '"$LLAMA_SERVER" --version' in script
    assert "*.dll" in script
    assert "list_bundled_llama_server_candidates" in script
    assert "multiple llama-server.exe" in script


def test_windows_llama_server_discovery_uses_non_overlapping_roots(
    tmp_path: Path,
) -> None:
    bundle_dir = tmp_path / "dist" / "LexiFlow"
    llama_dir = bundle_dir / "_internal" / "bin"
    llama_dir.mkdir(parents=True)
    llama_server = llama_dir / "llama-server.exe"
    llama_server.write_bytes(b"")
    (llama_dir / "ggml.dll").write_bytes(b"")

    paths = _list_llama_server_candidates("*/bin/llama-server.exe", bundle_dir)

    assert paths == [str(llama_server.resolve())]


def test_overlapping_find_roots_resolve_single_unique_path(tmp_path: Path) -> None:
    dist_root = tmp_path / "dist"
    bundle_dir = dist_root / "LexiFlow"
    llama_dir = bundle_dir / "_internal" / "bin"
    llama_dir.mkdir(parents=True)
    llama_server = llama_dir / "llama-server.exe"
    llama_server.write_bytes(b"")

    paths = _list_llama_server_candidates(
        "*/bin/llama-server.exe",
        dist_root,
        bundle_dir,
    )

    assert paths == [str(llama_server.resolve())]


def test_macos_llama_server_discovery_finds_app_bundle_binary(
    tmp_path: Path,
) -> None:
    app_root = tmp_path / "dist" / "LexiFlow.app"
    llama_dir = app_root / "Contents" / "Frameworks" / "bin"
    llama_dir.mkdir(parents=True)
    llama_server = llama_dir / "llama-server"
    llama_server.write_bytes(b"")
    llama_server.chmod(0o755)

    paths = _list_llama_server_candidates(
        "*/Contents/Frameworks/bin/llama-server",
        app_root,
    )

    assert paths == [str(llama_server.resolve())]


def test_macos_duplicate_app_roots_resolve_single_path(tmp_path: Path) -> None:
    app_root = tmp_path / "dist" / "LexiFlow.app"
    llama_dir = app_root / "Contents" / "Frameworks" / "bin"
    llama_dir.mkdir(parents=True)
    llama_server = llama_dir / "llama-server"
    llama_server.write_bytes(b"")
    llama_server.chmod(0o755)
    dist_root = tmp_path / "dist"

    paths = _list_llama_server_candidates(
        "*/Contents/Frameworks/bin/llama-server",
        app_root,
        dist_root / "LexiFlow.app",
    )

    assert paths == [str(llama_server.resolve())]


def test_llama_server_discovery_rejects_genuine_duplicates(tmp_path: Path) -> None:
    bundle_dir = tmp_path / "dist" / "LexiFlow"
    first = bundle_dir / "one" / "bin" / "llama-server.exe"
    second = bundle_dir / "two" / "bin" / "llama-server.exe"
    first.parent.mkdir(parents=True)
    second.parent.mkdir(parents=True)
    first.write_bytes(b"")
    second.write_bytes(b"")

    paths = _list_llama_server_candidates("*/bin/llama-server.exe", bundle_dir)

    assert len(paths) == 2
    assert str(first.resolve()) in paths
    assert str(second.resolve()) in paths


def test_sqlite_vec_discovery_finds_bundled_loadable(tmp_path: Path) -> None:
    bundle_dir = tmp_path / "dist" / "LexiFlow"
    vec_dir = bundle_dir / "_internal" / "sqlite_vec"
    vec_dir.mkdir(parents=True)
    loadable = vec_dir / "vec0.so"
    loadable.write_bytes(b"")

    paths = _list_sqlite_vec_loadables(bundle_dir)

    assert paths == [str(loadable.resolve())]
