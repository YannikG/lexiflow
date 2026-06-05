"""Tests for release bundle smoke script helpers."""

from __future__ import annotations

from pathlib import Path


def test_smoke_bundle_script_resolves_windows_exe() -> None:
    root = Path(__file__).resolve().parents[2]
    script = (root / "packaging/scripts/smoke_bundle.sh").read_text(encoding="utf-8")
    assert "LexiFlow.exe" in script
    assert "--sqlite-vec-smoke" in script
