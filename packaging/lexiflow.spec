# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for LexiFlow onedir bundle."""

from __future__ import annotations

import platform
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_data_files

block_cipher = None
REPO_ROOT = Path(SPECPATH).resolve().parent
CORE_SRC = REPO_ROOT / "packages/lexiflow-core/src/lexiflow_core"
UI_SRC = REPO_ROOT / "packages/lexiflow-ui/src/lexiflow_ui"
BIN_ROOT = REPO_ROOT / "packaging" / "bin"

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


def _llama_server_binary() -> tuple[str, str] | None:
    key = sys.platform
    if key not in PLATFORM_BIN_KEYS:
        return None
    platform_key, binary_name = PLATFORM_BIN_KEYS[key]
    candidate = BIN_ROOT / platform_key / binary_name
    if candidate.is_file():
        return str(candidate), "bin"
    return None


pyside6_datas, pyside6_binaries, pyside6_hiddenimports = collect_all("PySide6")

datas = [
    (str(UI_SRC / "themes"), "lexiflow_ui/themes"),
    (str(CORE_SRC / "migrations"), "lexiflow_core/migrations"),
    (str(CORE_SRC / "models" / "models.lock"), "lexiflow_core/models"),
    (str(CORE_SRC / "llm" / "prompts"), "lexiflow_core/llm/prompts"),
] + pyside6_datas + collect_data_files("sqlite_vec")

binaries: list[tuple[str, str]] = []
llama_binary = _llama_server_binary()
if llama_binary is not None:
    binaries.append(llama_binary)
binaries += pyside6_binaries

hiddenimports = [
    "tomli_w",
    "sqlite_vec",
    "lexiflow_core",
    "lexiflow_ui",
    "lexiflow_worker",
    "lexiflow_worker.main",
    "lexiflow_worker.embedder",
] + pyside6_hiddenimports

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
