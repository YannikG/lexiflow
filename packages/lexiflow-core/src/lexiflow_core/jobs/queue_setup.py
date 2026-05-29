"""Job queue setup and migration."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.config.paths import queue_db_path
from lexiflow_core.db.database_path import ensure_database_parent
from lexiflow_core.db.migration_loader import queue_migrations_dir
from lexiflow_core.db.migrations import MigrationRunner


def ensure_job_queue(data_root: Path) -> Path:
    """Apply queue migrations and return the database path."""
    db_path = queue_db_path(data_root)
    ensure_database_parent(db_path)
    MigrationRunner().migrate(db_path, queue_migrations_dir())
    return db_path
