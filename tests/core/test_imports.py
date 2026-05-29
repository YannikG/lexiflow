"""Tests for package import graph."""

from __future__ import annotations


def test_lexiflow_core_imports_without_cycles() -> None:
    import lexiflow_core
    from lexiflow_core.config import (
        app_layout,
        bootstrap,
        paths,
        platform_dirs,
        settings,
        settings_resolution,
        settings_serialization,
        settings_store,
    )
    from lexiflow_core.db import (
        connection,
        database_path,
        migration_loader,
        migrations,
        schema_migrations,
        sql_script,
    )
    from lexiflow_core.jobs import JobService, ensure_job_queue, run_worker_loop
    from lexiflow_core.llm import FakeLLM, LLMProvider

    assert lexiflow_core.__version__
    assert paths.APP_DATA_NAME == "LexiFlow"
    assert platform_dirs.app_config_dir is not None
    assert settings.Settings is not None
    assert settings_resolution.resolve_data_root is not None
    assert settings_serialization.settings_to_mapping is not None
    assert settings_store.SettingsStore is not None
    assert app_layout.ensure_app_layout is not None
    assert bootstrap.bootstrap_runtime is not None
    assert migration_loader.MigrationLoader is not None
    assert migration_loader.bundled_migrations_dir is not None
    assert sql_script.split_sql_script is not None
    assert schema_migrations.SchemaMigrationJournal is not None
    assert migrations.MigrationRunner is not None
    assert database_path.ensure_database_parent is not None
    assert connection.connect_sqlite is not None
    assert ensure_job_queue is not None
    assert JobService is not None
    assert run_worker_loop is not None
    assert FakeLLM is not None
    assert LLMProvider is not None
