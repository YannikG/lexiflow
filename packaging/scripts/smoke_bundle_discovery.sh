#!/usr/bin/env bash

_canonical_path() {
  local path="$1"
  if [[ -e "$path" ]]; then
    realpath "$path" 2>/dev/null || printf '%s' "$path"
  else
    printf '%s' "$path"
  fi
}

list_bundled_llama_server_candidates() {
  local path_glob="$1"
  shift
  local -a roots=("$@")
  local -a llama_servers=()
  local -a unique_paths=()
  local root candidate canon existing

  for root in "${roots[@]}"; do
    [[ -d "$root" ]] || continue
    while IFS= read -r candidate; do
      llama_servers+=("$candidate")
    done < <(find "$root" -path "$path_glob" -type f 2>/dev/null)
  done

  for candidate in "${llama_servers[@]}"; do
    canon="$(_canonical_path "$candidate")"
    local seen=0
    if [[ ${#unique_paths[@]} -gt 0 ]]; then
      for existing in "${unique_paths[@]}"; do
        if [[ "$existing" == "$canon" ]]; then
          seen=1
          break
        fi
      done
    fi
    if [[ $seen -eq 0 ]]; then
      unique_paths+=("$canon")
    fi
  done

  if [[ ${#unique_paths[@]} -gt 0 ]]; then
    printf '%s\n' "${unique_paths[@]}"
  fi
}

list_bundled_sqlite_vec_loadables() {
  local root="$1"
  [[ -d "$root" ]] || return 0
  find "$root" -path '*/sqlite_vec/vec0*' -type f 2>/dev/null
}
