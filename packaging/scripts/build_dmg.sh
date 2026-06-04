#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

BUNDLE_DIR="$ROOT/dist/LexiFlow"
VERSION="${LF_VERSION:-0.0.0}"
DMG="$ROOT/dist/LexiFlow-${VERSION}.dmg"
STAGE="$ROOT/dist/dmg-stage"

if [[ -d "$ROOT/dist/LexiFlow.app" ]]; then
  APP_SOURCE="$ROOT/dist/LexiFlow.app"
elif [[ -d "$BUNDLE_DIR/LexiFlow.app" ]]; then
  APP_SOURCE="$BUNDLE_DIR/LexiFlow.app"
elif [[ -d "$BUNDLE_DIR" ]]; then
  APP_SOURCE=""
else
  echo "bundle directory missing: $BUNDLE_DIR" >&2
  exit 1
fi

rm -rf "$STAGE" "$DMG"
mkdir -p "$STAGE"
if [[ -n "$APP_SOURCE" ]]; then
  cp -a "$APP_SOURCE" "$STAGE/"
else
  cp -a "$BUNDLE_DIR" "$STAGE/LexiFlow"
fi

if command -v create-dmg >/dev/null 2>&1; then
  create-dmg \
    --volname "LexiFlow" \
    --window-pos 200 120 \
    --window-size 600 400 \
    --icon-size 100 \
    "$DMG" \
    "$STAGE"
else
  hdiutil create -volname "LexiFlow" -srcfolder "$STAGE" -ov -format UDZO "$DMG"
fi

echo "$DMG"
