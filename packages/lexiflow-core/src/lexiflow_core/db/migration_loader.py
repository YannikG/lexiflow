"""Filesystem discovery and loading of SQL migration scripts."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_MIGRATION_PATTERN = re.compile(r"^(\d{3})_.+\.sql$")


@dataclass(frozen=True)
class MigrationScript:
    version: str
    sql: str


class MigrationLoader:
    def __init__(self, scripts_dir: Path) -> None:
        self._scripts_dir = scripts_dir

    def discover(self) -> list[MigrationScript]:
        scripts: list[MigrationScript] = []
        for path in sorted(self._scripts_dir.glob("*.sql")):
            if _MIGRATION_PATTERN.match(path.name) is None:
                continue
            scripts.append(
                MigrationScript(
                    version=path.stem,
                    sql=path.read_text(encoding="utf-8"),
                )
            )
        return scripts


def bundled_migrations_dir() -> Path:
    """Return the packaged SQL migrations directory shipped with lexiflow-core."""
    return Path(__file__).resolve().parent.parent / "migrations"
