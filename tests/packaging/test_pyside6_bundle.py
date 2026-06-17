"""Tests for minimal PySide6 release bundle collection."""

from __future__ import annotations

from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_pyside6_bundle():
    import importlib.util

    script = _repo_root() / "packaging" / "scripts" / "pyside6_bundle.py"
    spec = importlib.util.spec_from_file_location("lexiflow_pyside6_bundle", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_pyside6_import_scanner_detects_common_import_styles() -> None:
    pyside6_bundle = _load_pyside6_bundle()
    source = """
from PySide6 import QtCore
from PySide6.QtWidgets import QWidget
import PySide6.QtNetwork
import PySide6.QtGui as QtGui
"""
    discovered = pyside6_bundle.discover_pyside6_imports_from_source(source)
    assert discovered == {"QtCore", "QtGui", "QtNetwork", "QtWidgets"}


def test_pyside6_import_scanner_flags_disallowed_submodule() -> None:
    pyside6_bundle = _load_pyside6_bundle()
    source = "from PySide6 import QtWebEngineWidgets\n"
    discovered = pyside6_bundle.discover_pyside6_imports_from_source(source)
    unknown = discovered - pyside6_bundle.ALLOWED_PYSIDE6_SUBMODULES
    assert unknown == {"QtWebEngineWidgets"}


def test_lexiflow_ui_pyside6_imports_within_allowlist() -> None:
    pyside6_bundle = _load_pyside6_bundle()
    ui_src = _repo_root() / "packages" / "lexiflow-ui" / "src"
    discovered = pyside6_bundle.discover_pyside6_imports(ui_src)
    unknown = discovered - pyside6_bundle.ALLOWED_PYSIDE6_SUBMODULES
    assert not unknown, (
        "Unexpected PySide6 imports in lexiflow-ui; update ALLOWED_PYSIDE6_SUBMODULES "
        f"in packaging/scripts/pyside6_bundle.py: {sorted(unknown)}"
    )


def test_lexiflow_ui_shiboken_imports_within_allowlist() -> None:
    pyside6_bundle = _load_pyside6_bundle()
    ui_src = _repo_root() / "packages" / "lexiflow-ui" / "src"
    discovered = pyside6_bundle.discover_shiboken_imports(ui_src)
    unknown = discovered - pyside6_bundle.ALLOWED_SHIBOKEN_MODULES
    assert not unknown, (
        "Unexpected shiboken imports in lexiflow-ui; update ALLOWED_SHIBOKEN_MODULES "
        f"in packaging/scripts/pyside6_bundle.py: {sorted(unknown)}"
    )


def test_collect_pyside6_bundle_returns_merged_triple() -> None:
    pytest = __import__("pytest")
    pytest.importorskip("PyInstaller")
    pyside6_bundle = _load_pyside6_bundle()
    datas, binaries, hiddenimports = pyside6_bundle.collect_pyside6_bundle()
    assert datas
    assert binaries
    assert "shiboken6" in hiddenimports
    assert "PySide6.support.deprecated" in hiddenimports


def test_forbidden_qt_frameworks_not_in_built_bundle() -> None:
    pyside6_bundle = _load_pyside6_bundle()
    root = _repo_root()
    candidates = [
        root / "dist" / "LexiFlow",
        root / "dist" / "LexiFlow.app",
    ]
    bundle_root = next((path for path in candidates if path.is_dir()), None)
    if bundle_root is None:
        return
    forbidden = pyside6_bundle.forbidden_qt_paths_in_bundle(bundle_root)
    assert not forbidden, (
        "Release bundle contains unused Qt frameworks; "
        f"update packaging/scripts/pyside6_bundle.py: {forbidden[:10]}"
    )
