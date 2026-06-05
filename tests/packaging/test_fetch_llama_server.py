"""Tests for llama-server fetch asset selection."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


def _load_fetch_llama_server():
    script = (
        Path(__file__).resolve().parents[2]
        / "packaging"
        / "scripts"
        / "fetch_llama_server.py"
    )
    spec = importlib.util.spec_from_file_location("lexiflow_fetch_llama_server", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    ("platform_key", "asset_suffix"),
    [
        ("linux", "bin-ubuntu-x64.tar.gz"),
        ("macos-arm64", "bin-macos-arm64.tar.gz"),
        ("macos-x64", "bin-macos-x64.tar.gz"),
        ("windows", "bin-win-cpu-x64.zip"),
        ("windows-arm64", "bin-win-cpu-arm64.zip"),
    ],
)
def test_asset_name_for_platform(platform_key: str, asset_suffix: str) -> None:
    fetch = _load_fetch_llama_server()
    release = fetch.DEFAULT_RELEASE
    asset_filename, archive_type = fetch.asset_name(release, platform_key)
    assert asset_filename == f"llama-{release}-{asset_suffix}"
    assert archive_type in {"tar.gz", "zip"}


def test_platform_key_detects_windows_arm64(monkeypatch: pytest.MonkeyPatch) -> None:
    fetch = _load_fetch_llama_server()
    monkeypatch.setattr(fetch.platform, "system", lambda: "Windows")
    monkeypatch.setattr(fetch.platform, "machine", lambda: "ARM64")
    assert fetch.detect_platform_key() == "windows-arm64"


def test_platform_key_detects_windows_x64(monkeypatch: pytest.MonkeyPatch) -> None:
    fetch = _load_fetch_llama_server()
    monkeypatch.setattr(fetch.platform, "system", lambda: "Windows")
    monkeypatch.setattr(fetch.platform, "machine", lambda: "AMD64")
    assert fetch.detect_platform_key() == "windows"


def _load_llama_runtime_libs():
    script = (
        Path(__file__).resolve().parents[2]
        / "packaging"
        / "scripts"
        / "llama_runtime_libs.py"
    )
    spec = importlib.util.spec_from_file_location("lexiflow_llama_runtime_libs", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_copy_runtime_libs_copies_dylibs_beside_server(tmp_path: Path) -> None:
    runtime = _load_llama_runtime_libs()
    source = tmp_path / "src"
    destination = tmp_path / "out"
    source.mkdir()
    (source / "llama-server").write_text("", encoding="utf-8")
    (source / "libllama-server-impl.dylib").write_bytes(b"dylib")
    (source / "libggml.0.dylib").write_bytes(b"dylib")
    (source / "readme.txt").write_text("skip", encoding="utf-8")

    copied = runtime.copy_runtime_libs(source, destination, "macos-arm64")

    assert copied == 2
    assert (destination / "libllama-server-impl.dylib").is_file()
    assert (destination / "libggml.0.dylib").is_file()
    assert not (destination / "readme.txt").exists()
