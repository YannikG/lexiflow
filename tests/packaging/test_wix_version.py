"""Tests for WiX Product version normalization."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_wix_version():
    script = (
        Path(__file__).resolve().parents[2] / "packaging" / "scripts" / "wix_version.py"
    )
    spec = importlib.util.spec_from_file_location("lexiflow_wix_version", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_normalize_wix_product_version_pads_semver_to_four_parts() -> None:
    normalize = _load_wix_version().normalize_wix_product_version

    assert normalize("1.0.0") == "1.0.0.0"


def test_normalize_wix_product_version_keeps_four_part_release() -> None:
    normalize = _load_wix_version().normalize_wix_product_version

    assert normalize("1.0.0.0") == "1.0.0.0"


def test_normalize_wix_product_version_strips_non_numeric_suffixes() -> None:
    normalize = _load_wix_version().normalize_wix_product_version

    assert normalize("1.0.0.dev42") == "1.0.0.0"
