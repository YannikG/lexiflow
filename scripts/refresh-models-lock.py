#!/usr/bin/env python3
"""Print current main-branch SHAs for models.lock artifacts (run from repo root)."""

from __future__ import annotations

import tomllib
from pathlib import Path

from huggingface_hub import HfApi

LOCK_PATH = (
    Path(__file__).resolve().parent.parent
    / "packages/lexiflow-core/src/lexiflow_core/models/models.lock"
)


def main() -> None:
    raw = tomllib.loads(LOCK_PATH.read_text(encoding="utf-8"))
    api = HfApi()
    lines: list[str] = []
    for entry in raw["artifacts"]:
        repo = entry["repo"]
        artifact_id = entry["id"]
        sha = api.model_info(repo).sha
        lines.append(f'[[artifacts]]\nid = "{artifact_id}"')
        lines.append(f'repo = "{repo}"')
        lines.append(f'revision = "{sha}"')
        lines.append("")
    print("\n".join(lines).rstrip())


if __name__ == "__main__":
    main()
