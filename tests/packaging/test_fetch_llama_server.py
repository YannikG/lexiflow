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
    ("platform_key", "expected_asset"),
    [
        ("linux", "llama-b9500-bin-ubuntu-x64.tar.gz"),
        ("macos-arm64", "llama-b9500-bin-macos-arm64.tar.gz"),
        ("macos-x64", "llama-b9500-bin-macos-x64.tar.gz"),
        ("windows", "llama-b9500-bin-win-cpu-x64.zip"),
        ("windows-arm64", "llama-b9500-bin-win-cpu-arm64.zip"),
    ],
)
def test_asset_name_for_platform(platform_key: str, expected_asset: str) -> None:
    fetch = _load_fetch_llama_server()
    asset_name, archive_type = fetch._asset_name("b9500", platform_key)
    assert asset_name == expected_asset
    assert archive_type in {"tar.gz", "zip"}


def test_platform_key_detects_windows_arm64(monkeypatch: pytest.MonkeyPatch) -> None:
    fetch = _load_fetch_llama_server()
    monkeypatch.setattr(fetch.platform, "system", lambda: "Windows")
    monkeypatch.setattr(fetch.platform, "machine", lambda: "ARM64")
    assert fetch._platform_key() == "windows-arm64"


def test_platform_key_detects_windows_x64(monkeypatch: pytest.MonkeyPatch) -> None:
    fetch = _load_fetch_llama_server()
    monkeypatch.setattr(fetch.platform, "system", lambda: "Windows")
    monkeypatch.setattr(fetch.platform, "machine", lambda: "AMD64")
    assert fetch._platform_key() == "windows"
