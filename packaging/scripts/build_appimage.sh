#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

BUNDLE_DIR="$ROOT/dist/LexiFlow"
APPDIR="$ROOT/dist/LexiFlow.AppDir"
VERSION="${LF_VERSION:-0.0.0}"
APPIMAGE="$ROOT/dist/LexiFlow-${VERSION}-x86_64.AppImage"

if [[ ! -d "$BUNDLE_DIR" ]]; then
  echo "bundle directory missing: $BUNDLE_DIR" >&2
  exit 1
fi

rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin" "$APPDIR/usr/share/applications" "$APPDIR/usr/share/icons/hicolor/256x256/apps"

cp -a "$BUNDLE_DIR/." "$APPDIR/usr/bin/"
ln -sf usr/bin/LexiFlow "$APPDIR/AppRun"
cp packaging/assets/lexiflow.desktop "$APPDIR/lexiflow.desktop"
cp packaging/assets/lexiflow.desktop "$APPDIR/usr/share/applications/lexiflow.desktop"
if [[ -f packaging/assets/icon.png ]]; then
  cp packaging/assets/icon.png "$APPDIR/lexiflow.png"
  cp packaging/assets/icon.png "$APPDIR/usr/share/icons/hicolor/256x256/apps/lexiflow.png"
fi

if ! command -v appimagetool >/dev/null 2>&1; then
  echo "appimagetool not found; install from https://github.com/AppImage/AppImageKit" >&2
  exit 1
fi

ARCH=x86_64 appimagetool "$APPDIR" "$APPIMAGE"
echo "$APPIMAGE"
