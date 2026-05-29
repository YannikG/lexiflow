"""Tests for package import graph and bootstrap orchestration."""

from __future__ import annotations


def test_lexiflow_core_imports_without_cycles() -> None:
    import lexiflow_core
    from lexiflow_core.config import bootstrap, paths, settings
    from lexiflow_core.db import connection, migration_loader, migrations, sql_script

    assert lexiflow_core.__version__
    assert paths.APP_DATA_NAME == "LexiFlow"
    assert settings.resolve_data_root is not None
    assert bootstrap.bootstrap_runtime is not None
    assert migration_loader.MigrationLoader is not None
    assert sql_script.split_sql_script is not None
    assert migrations.MigrationRunner is not None
    assert connection.connect_sqlite is not None
