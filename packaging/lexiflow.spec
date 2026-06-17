# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for LexiFlow onedir bundle."""

from __future__ import annotations

import importlib.util
import platform
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_data_files, copy_metadata

block_cipher = None
REPO_ROOT = Path(SPECPATH).resolve().parent


def _load_llama_runtime_libs():
    script = REPO_ROOT / "packaging" / "scripts" / "llama_runtime_libs.py"
    spec = importlib.util.spec_from_file_location("lexiflow_llama_runtime_libs", script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_llama_runtime = _load_llama_runtime_libs()
runtime_lib_globs = _llama_runtime.runtime_lib_globs
CORE_SRC = REPO_ROOT / "packages/lexiflow-core/src/lexiflow_core"
UI_SRC = REPO_ROOT / "packages/lexiflow-ui/src/lexiflow_ui"
BIN_ROOT = REPO_ROOT / "packaging" / "bin"
VENDOR_VEC_DIR = REPO_ROOT / "packaging" / "vendor" / "sqlite_vec" / "sqlite_vec"


def _sqlite_vec_datas() -> list[tuple[str, str]]:
    return collect_data_files(
        "sqlite_vec",
        excludes=["vec0*", "*.dylib", "*.so", "*.dll"],
    )


def _host_vec0_filenames() -> list[str]:
    machine = platform.machine().lower()
    if sys.platform == "win32":
        if machine in {"arm64", "aarch64"}:
            return ["vec0.arm64.dll"]
        return ["vec0.dll"]
    if sys.platform == "darwin":
        return ["vec0.dylib"]
    if sys.platform == "linux":
        return ["vec0.so"]
    return ["vec0.dylib", "vec0.so", "vec0.dll", "vec0.arm64.dll"]


def _sqlite_vec_binaries() -> list[tuple[str, str]]:
    """Ship vendored vec0 native loadables next to the sqlite_vec package in the bundle."""
    entries: list[tuple[str, str]] = []
    for filename in _host_vec0_filenames():
        loadable = VENDOR_VEC_DIR / filename
        if loadable.is_file():
            entries.append((str(loadable), "sqlite_vec"))
    if not entries:
        expected = ", ".join(_host_vec0_filenames())
        raise RuntimeError(
            f"sqlite-vec loadable missing under {VENDOR_VEC_DIR} "
            f"(expected one of: {expected}); "
            "run packaging/scripts/fetch_sqlite_vec.py"
        )
    return entries

PLATFORM_BIN_KEYS = {
    "linux": ("linux", "llama-server"),
    "darwin": (
        "macos-arm64" if platform.machine().lower() in {"arm64", "aarch64"} else "macos-x64",
        "llama-server",
    ),
    "win32": (
        "windows-arm64"
        if platform.machine().lower() in {"arm64", "aarch64"}
        else "windows",
        "llama-server.exe",
    ),
}


def _llama_server_binaries() -> list[tuple[str, str]]:
    key = sys.platform
    if key not in PLATFORM_BIN_KEYS:
        return []
    platform_key, binary_name = PLATFORM_BIN_KEYS[key]
    platform_dir = BIN_ROOT / platform_key
    candidate = platform_dir / binary_name
    if not candidate.is_file():
        return []
    dest = "bin"
    entries: list[tuple[str, str]] = [(str(candidate), dest)]
    seen: set[str] = set()
    for pattern in runtime_lib_globs(platform_key):
        for lib_path in sorted(platform_dir.glob(pattern)):
            if lib_path.is_file() and lib_path.name not in seen:
                seen.add(lib_path.name)
                entries.append((str(lib_path), dest))
    return entries


pyside6_datas, pyside6_binaries, pyside6_hiddenimports = collect_all("PySide6")

spacy_datas: list[tuple[str, str]] = []
spacy_binaries: list[tuple[str, str]] = []
spacy_hiddenimports: list[str] = []
for metadata_pkg in (
    "spacy",
    "thinc",
    "catalogue",
    "srsly",
    "murmurhash",
    "preshed",
    "cymem",
    "wasabi",
    "weasel",
):
    spacy_datas += copy_metadata(metadata_pkg)
spacy_pkg_datas, spacy_pkg_binaries, spacy_pkg_hiddenimports = collect_all("spacy")
spacy_datas += spacy_pkg_datas
spacy_binaries += spacy_pkg_binaries
spacy_hiddenimports += spacy_pkg_hiddenimports

sqlean_datas: list[tuple[str, str]] = []
sqlean_binaries: list[tuple[str, str]] = []
sqlean_hiddenimports: list[str] = []
if sys.platform != "win32":
    sqlean_datas, sqlean_binaries, sqlean_hiddenimports = collect_all("sqlean")

datas = [
    (str(UI_SRC / "themes"), "lexiflow_ui/themes"),
    (str(CORE_SRC / "migrations"), "lexiflow_core/migrations"),
    (str(CORE_SRC / "models" / "models.lock"), "lexiflow_core/models"),
    (str(CORE_SRC / "llm" / "prompts"), "lexiflow_core/llm/prompts"),
] + pyside6_datas + _sqlite_vec_datas() + spacy_datas + sqlean_datas

binaries: list[tuple[str, str]] = _llama_server_binaries()
binaries += _sqlite_vec_binaries()
binaries += pyside6_binaries + spacy_binaries + sqlean_binaries

hiddenimports = [
    "tomli_w",
    "sqlite_vec",
    "lexiflow_core",
    "lexiflow_core.db.sqlite_bootstrap",
    "lexiflow_ui",
    "lexiflow_worker",
    "lexiflow_worker.main",
    "lexiflow_worker.embedder",
] + pyside6_hiddenimports + spacy_hiddenimports + sqlean_hiddenimports

pathex = [
    str(REPO_ROOT / "packages/lexiflow-ui/src"),
    str(REPO_ROOT / "packages/lexiflow-core/src"),
    str(REPO_ROOT / "packages/lexiflow-worker/src"),
]

a = Analysis(
    [str(REPO_ROOT / "packages/lexiflow-ui/src/lexiflow_ui/launcher.py")],
    pathex=pathex,
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

icon_file = None
if sys.platform == "darwin":
    icon_candidate = REPO_ROOT / "packaging/assets/icon.icns"
    if icon_candidate.is_file():
        icon_file = str(icon_candidate)
elif sys.platform == "win32":
    icon_candidate = REPO_ROOT / "packaging/assets/icon.ico"
    if icon_candidate.is_file():
        icon_file = str(icon_candidate)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="LexiFlow",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="LexiFlow",
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="LexiFlow.app",
        icon=icon_file,
        bundle_identifier="com.lexiflow.app",
    )
