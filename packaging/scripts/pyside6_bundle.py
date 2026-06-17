"""Minimal PySide6 collection for PyInstaller release bundles."""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

ALLOWED_PYSIDE6_SUBMODULES = frozenset({"QtCore", "QtGui", "QtNetwork", "QtWidgets"})

ALLOWED_PYSIDE6_MODULES = tuple(
    f"PySide6.{name}" for name in sorted(ALLOWED_PYSIDE6_SUBMODULES)
)

ALLOWED_SHIBOKEN_MODULES = frozenset({"shiboken6"})

EXTRA_HIDDENIMPORTS = ("shiboken6", "PySide6.support.deprecated")

PYSIDE6_ANALYSIS_EXCLUDES = (
    "PySide6.Qt3DAnimation",
    "PySide6.Qt3DCore",
    "PySide6.Qt3DExtras",
    "PySide6.Qt3DInput",
    "PySide6.Qt3DLogic",
    "PySide6.Qt3DRender",
    "PySide6.QtBluetooth",
    "PySide6.QtCharts",
    "PySide6.QtDataVisualization",
    "PySide6.QtGraphs",
    "PySide6.QtGraphsWidgets",
    "PySide6.QtHttpServer",
    "PySide6.QtLocation",
    "PySide6.QtMultimedia",
    "PySide6.QtMultimediaWidgets",
    "PySide6.QtNetworkAuth",
    "PySide6.QtNfc",
    "PySide6.QtPositioning",
    "PySide6.QtPrintSupport",
    "PySide6.QtQml",
    "PySide6.QtQuick",
    "PySide6.QtQuick3D",
    "PySide6.QtQuickControls2",
    "PySide6.QtQuickWidgets",
    "PySide6.QtRemoteObjects",
    "PySide6.QtScxml",
    "PySide6.QtSensors",
    "PySide6.QtSerialBus",
    "PySide6.QtSerialPort",
    "PySide6.QtSpatialAudio",
    "PySide6.QtSql",
    "PySide6.QtStateMachine",
    "PySide6.QtSvg",
    "PySide6.QtSvgWidgets",
    "PySide6.QtTest",
    "PySide6.QtTextToSpeech",
    "PySide6.QtUiTools",
    "PySide6.QtWebChannel",
    "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineQuick",
    "PySide6.QtWebEngineWidgets",
    "PySide6.QtWebSockets",
    "PySide6.QtXml",
)

FORBIDDEN_QT_FRAMEWORK_MARKERS = (
    "QtWebEngine",
    "Qt3D",
    "QtCharts",
    "QtMultimedia",
    "QtQuick3D",
    "QtDataVisualization",
    "QtGraphs",
)

_PYSIDE6_IMPORT_RE = re.compile(r"^\s*(?:from|import)\s+PySide6\.(\w+)")


def discover_pyside6_imports(root: Path) -> set[str]:
    """Return PySide6 submodule names imported under *root* (read-only scan)."""
    discovered: set[str] = set()
    for path in _python_files(root):
        discovered.update(
            _pyside6_submodules_in_source(path.read_text(encoding="utf-8"))
        )
    return discovered


def discover_shiboken_imports(root: Path) -> set[str]:
    """Return top-level shiboken module names imported under *root*."""
    discovered: set[str] = set()
    for path in _python_files(root):
        discovered.update(_shiboken_modules_in_source(path.read_text(encoding="utf-8")))
    return discovered


BundleTriple = tuple[list[tuple[str, str]], list[tuple[str, str]], list[str]]


def collect_pyside6_bundle() -> BundleTriple:
    """Collect datas, binaries, and hiddenimports for allowed PySide6 modules only."""
    from PyInstaller.utils.hooks import collect_all

    datas: list[tuple[str, str]] = []
    binaries: list[tuple[str, str]] = []
    hiddenimports: list[str] = list(EXTRA_HIDDENIMPORTS)

    for module in ALLOWED_PYSIDE6_MODULES:
        module_datas, module_binaries, module_hiddenimports = collect_all(module)
        datas.extend(module_datas)
        binaries.extend(module_binaries)
        hiddenimports.extend(module_hiddenimports)

    shiboken_datas, shiboken_binaries, shiboken_hiddenimports = collect_all("shiboken6")
    datas.extend(shiboken_datas)
    binaries.extend(shiboken_binaries)
    hiddenimports.extend(shiboken_hiddenimports)

    return datas, binaries, _dedupe(hiddenimports)


def forbidden_qt_paths_in_bundle(bundle_root: Path) -> list[Path]:
    """Return paths under *bundle_root* that match known-unused Qt frameworks."""
    if not bundle_root.is_dir():
        return []
    hits: list[Path] = []
    for path in bundle_root.rglob("*"):
        name = path.name
        if any(marker in name for marker in FORBIDDEN_QT_FRAMEWORK_MARKERS):
            hits.append(path)
    return sorted(hits)


def _python_files(root: Path) -> Iterable[Path]:
    if not root.is_dir():
        return ()
    return (path for path in root.rglob("*.py") if path.is_file())


def _pyside6_submodules_in_source(source: str) -> set[str]:
    discovered: set[str] = set()
    for match in _PYSIDE6_IMPORT_RE.finditer(source):
        discovered.add(match.group(1))
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return discovered
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.ImportFrom)
            and node.module
            and node.module.startswith("PySide6.")
        ):
            discovered.add(node.module.removeprefix("PySide6.").split(".")[0])
    return discovered


def _shiboken_modules_in_source(source: str) -> set[str]:
    discovered: set[str] = set()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return discovered
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "shiboken6" or alias.name.startswith("shiboken6."):
                    discovered.add("shiboken6")
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module == "shiboken6" or node.module.startswith("shiboken6."):
                discovered.add("shiboken6")
    return discovered


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result
