#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

PLATFORM="${1:-linux}"

VERSION="$(uv run python packaging/scripts/sync_version.py)"
export LF_EXPECTED_VERSION="$VERSION"
export LF_VERSION="$VERSION"

uv run python packaging/scripts/fetch_llama_server.py --platform "$PLATFORM"
uv run pyinstaller packaging/lexiflow.spec --noconfirm
bash packaging/scripts/smoke_bundle.sh

case "$PLATFORM" in
  linux)
    bash packaging/scripts/build_appimage.sh
    ;;
  macos-arm64|macos-x64)
    bash packaging/scripts/build_dmg.sh
    ;;
  windows)
    powershell -File packaging/scripts/build_msi.ps1
    ;;
  *)
    echo "unknown platform: $PLATFORM" >&2
    exit 1
    ;;
esac
