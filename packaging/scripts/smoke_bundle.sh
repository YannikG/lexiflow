#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

BUNDLE_DIR="${LF_BUNDLE_DIR:-$ROOT/dist/LexiFlow}"
EXPECTED_VERSION="${LF_EXPECTED_VERSION:-}"

if [[ -x "$ROOT/dist/LexiFlow.app/Contents/MacOS/LexiFlow" ]]; then
  BINARY="$ROOT/dist/LexiFlow.app/Contents/MacOS/LexiFlow"
elif [[ -x "$BUNDLE_DIR/LexiFlow.app/Contents/MacOS/LexiFlow" ]]; then
  BINARY="$BUNDLE_DIR/LexiFlow.app/Contents/MacOS/LexiFlow"
elif [[ -x "$BUNDLE_DIR/LexiFlow" ]]; then
  BINARY="$BUNDLE_DIR/LexiFlow"
else
  echo "bundle binary not found under $BUNDLE_DIR or dist/LexiFlow.app" >&2
  exit 1
fi

ACTUAL_VERSION="$("$BINARY" --version)"
echo "bundle version: $ACTUAL_VERSION"
if [[ -n "$EXPECTED_VERSION" && "$ACTUAL_VERSION" != "$EXPECTED_VERSION" ]]; then
  echo "expected version $EXPECTED_VERSION, got $ACTUAL_VERSION" >&2
  exit 1
fi

WORKER_ROOT="$(mktemp -d)"
trap 'rm -rf "$WORKER_ROOT"' EXIT
"$BINARY" --worker --data-root "$WORKER_ROOT"
echo "worker smoke passed"

if [[ "${LF_SKIP_UI_SMOKE:-0}" != "1" ]]; then
  export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-offscreen}"
  export QT_LOGGING_RULES="${QT_LOGGING_RULES:-*.debug=false;qt.qpa.*=false}"
  timeout 30s "$BINARY" &
  UI_PID=$!
  sleep 5
  if ! kill -0 "$UI_PID" 2>/dev/null; then
    wait "$UI_PID" || true
    echo "UI process exited early" >&2
    exit 1
  fi
  kill "$UI_PID" 2>/dev/null || true
  wait "$UI_PID" 2>/dev/null || true
  echo "UI smoke passed"
fi

echo "bundle smoke passed"
