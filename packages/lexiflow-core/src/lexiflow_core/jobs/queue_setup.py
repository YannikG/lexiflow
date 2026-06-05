"""Job queue setup and migration."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.config.paths import queue_db_path
from lexiflow_core.db.connection import connect_sqlite
from lexiflow_core.db.database_path import ensure_database_parent
from lexiflow_core.db.migration_loader import queue_migrations_dir
from lexiflow_core.db.migrations import MigrationRunner

_OBSOLETE_JOB_TYPES = ("download_spacy",)


def _remove_obsolete_jobs(db_path: Path) -> None:
    """Delete legacy job rows whose types are no longer supported."""
    connection = connect_sqlite(db_path)
    try:
        for job_type in _OBSOLETE_JOB_TYPES:
            connection.execute(
                "DELETE FROM jobs WHERE job_type = ?",
                (job_type,),
            )
        connection.commit()
    finally:
        connection.close()


def ensure_job_queue(data_root: Path) -> Path:
    """Apply queue migrations and return the database path."""
    db_path = queue_db_path(data_root)
    ensure_database_parent(db_path)
    MigrationRunner().migrate(db_path, queue_migrations_dir())
    _remove_obsolete_jobs(db_path)
    return db_path
