#!/usr/bin/env bash
set -euo pipefail

# shellcheck source=packaging/scripts/smoke_bundle_discovery.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/smoke_bundle_discovery.sh"

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

BUNDLE_DIR="${LF_BUNDLE_DIR:-$ROOT/dist/LexiFlow}"
EXPECTED_VERSION="${LF_EXPECTED_VERSION:-}"

resolve_bundle_binary() {
  local candidate=""
  if [[ -x "$ROOT/dist/LexiFlow.app/Contents/MacOS/LexiFlow" ]]; then
    candidate="$ROOT/dist/LexiFlow.app/Contents/MacOS/LexiFlow"
  elif [[ -x "$BUNDLE_DIR/LexiFlow.app/Contents/MacOS/LexiFlow" ]]; then
    candidate="$BUNDLE_DIR/LexiFlow.app/Contents/MacOS/LexiFlow"
  elif [[ -x "$BUNDLE_DIR/LexiFlow.exe" ]]; then
    candidate="$BUNDLE_DIR/LexiFlow.exe"
  elif [[ -x "$BUNDLE_DIR/LexiFlow" ]]; then
    candidate="$BUNDLE_DIR/LexiFlow"
  fi
  if [[ -z "$candidate" ]]; then
    echo "bundle binary not found under $BUNDLE_DIR or dist/LexiFlow.app" >&2
    exit 1
  fi
  printf '%s' "$candidate"
}

BINARY="$(resolve_bundle_binary)"

BUNDLE_ROOTS=("$BUNDLE_DIR")
if [[ -d "$ROOT/dist/LexiFlow.app" ]]; then
  BUNDLE_ROOTS+=("$ROOT/dist/LexiFlow.app")
fi

SQLITE_VEC_LOADABLES=()
while IFS= read -r candidate; do
  SQLITE_VEC_LOADABLES+=("$candidate")
done < <(
  for root in "${BUNDLE_ROOTS[@]}"; do
    list_bundled_sqlite_vec_loadables "$root"
  done | sort -u
)
if [[ ${#SQLITE_VEC_LOADABLES[@]} -eq 0 ]]; then
  echo "bundled sqlite-vec loadable missing under bundle roots: ${BUNDLE_ROOTS[*]}" >&2
  exit 1
fi
if [[ ${#SQLITE_VEC_LOADABLES[@]} -gt 1 ]]; then
  echo "error: found multiple sqlite-vec loadables, ambiguous. Paths: ${SQLITE_VEC_LOADABLES[*]}" >&2
  exit 1
fi
echo "sqlite-vec loadable: ${SQLITE_VEC_LOADABLES[0]}"

ACTUAL_VERSION="$("$BINARY" --version)"
echo "bundle version: $ACTUAL_VERSION"
if [[ -n "$EXPECTED_VERSION" && "$ACTUAL_VERSION" != "$EXPECTED_VERSION" ]]; then
  echo "expected version $EXPECTED_VERSION, got $ACTUAL_VERSION" >&2
  exit 1
fi

VEC_VERSION="$("$BINARY" --sqlite-vec-smoke)"
echo "sqlite-vec version: $VEC_VERSION"
if [[ -z "$VEC_VERSION" ]]; then
  echo "sqlite-vec smoke returned empty version" >&2
  exit 1
fi
echo "sqlite-vec smoke passed"

if [[ -x "$ROOT/dist/LexiFlow.app/Contents/MacOS/LexiFlow" || -x "$BUNDLE_DIR/LexiFlow.app/Contents/MacOS/LexiFlow" ]]; then
  MACOS_APP_ROOTS=()
  if [[ -d "$ROOT/dist/LexiFlow.app" ]]; then
    MACOS_APP_ROOTS+=("$ROOT/dist/LexiFlow.app")
  fi
  if [[ -d "$BUNDLE_DIR/LexiFlow.app" ]]; then
    MACOS_APP_ROOTS+=("$BUNDLE_DIR/LexiFlow.app")
  fi
  LLAMA_SERVERS=()
  while IFS= read -r candidate; do
    LLAMA_SERVERS+=("$candidate")
  done < <(
    list_bundled_llama_server_candidates \
      '*/Contents/Frameworks/bin/llama-server' \
      "${MACOS_APP_ROOTS[@]}"
  )
  if [[ ${#LLAMA_SERVERS[@]} -eq 0 ]]; then
    echo "bundled llama-server missing under LexiFlow.app/Contents/Frameworks/bin" >&2
    exit 1
  fi
  if [[ ${#LLAMA_SERVERS[@]} -gt 1 ]]; then
    echo "error: found multiple llama-server binaries, ambiguous. Paths: ${LLAMA_SERVERS[*]}" >&2
    exit 1
  fi
  LLAMA_SERVER="${LLAMA_SERVERS[0]}"
  if [[ ! -x "$LLAMA_SERVER" ]]; then
    echo "bundled llama-server is not executable: $LLAMA_SERVER" >&2
    exit 1
  fi
  IMPL_DYLIB="$(dirname "$LLAMA_SERVER")/libllama-server-impl.dylib"
  if [[ ! -f "$IMPL_DYLIB" ]]; then
    echo "bundled libllama-server-impl.dylib missing next to llama-server" >&2
    exit 1
  fi
  "$LLAMA_SERVER" --version >/dev/null
  echo "llama-server smoke passed"
fi

if [[ -x "$BUNDLE_DIR/LexiFlow.exe" ]]; then
  LLAMA_SERVERS=()
  while IFS= read -r candidate; do
    LLAMA_SERVERS+=("$candidate")
  done < <(
    list_bundled_llama_server_candidates \
      '*/bin/llama-server.exe' \
      "$BUNDLE_DIR"
  )
  if [[ ${#LLAMA_SERVERS[@]} -eq 0 ]]; then
    echo "bundled llama-server.exe missing under LexiFlow/bin" >&2
    exit 1
  fi
  if [[ ${#LLAMA_SERVERS[@]} -gt 1 ]]; then
    echo "error: found multiple llama-server.exe, ambiguous. Paths: ${LLAMA_SERVERS[*]}" >&2
    exit 1
  fi
  LLAMA_SERVER="${LLAMA_SERVERS[0]}"
  LLAMA_DIR="$(dirname "$LLAMA_SERVER")"
  if ! compgen -G "$LLAMA_DIR/*.dll" > /dev/null; then
    echo "bundled llama-server runtime DLLs missing next to llama-server.exe" >&2
    exit 1
  fi
  "$LLAMA_SERVER" --version >/dev/null
  echo "llama-server smoke passed"
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
fi
