# Global settings and paths

LexiFlow separates machine-local configuration from the portable user library so startup always has a known bootstrap path.

## Bootstrap flow

1. Resolve **app config directory** (OS-specific; holds `settings.toml`).
2. Load **global settings** from `settings.toml`, or use defaults when missing.
3. Resolve **data root** from settings (`data_root` field) or default `~/LexiFlow/`.
4. Ensure runtime layout under `{data_root}/.app/` (databases, models cache, logs).

`bootstrap_runtime()` in `lexiflow_core.config.bootstrap` performs steps 2–4 for callers that need a ready library path on first run.

Settings are read before opening the library so a **data root** override never creates a chicken-and-egg problem.

## Path helpers

| Module | Helper | Purpose |
|--------|--------|---------|
| `platform_dirs` | `app_config_dir()` | Machine-local config directory |
| `paths` | `default_data_root()` | Default user library when settings omit `data_root` |
| `paths` | `language_json_path(data_root, code)` | Per-target-language metadata file |
| `paths` | `language_data_root(data_root, code)` | Per-target-language folder |
| `settings_resolution` | `resolve_data_root(settings)` | Effective library path from settings |
| `app_layout` | `ensure_app_layout(data_root)` | Create `.app/` and `.app/logs/` under the library |
| `bootstrap` | `bootstrap_runtime(settings_store)` | Load settings, resolve data root, ensure layout |
| `settings_store` | `SettingsStore` | Read/write `settings.toml` |
| `settings` | `Settings` | Global settings data model |
| `models.store` | `ModelStore` | Installed revision markers under `.app/models/` |
| `models.lockfile` | `load_models_lock()` | Shipped pin manifest for HF artifacts |

Pure path formulas stay separate from filesystem mutation and from settings I/O.

## Global settings

Stored as TOML in the app config directory. Includes native language, `active_target_language`, onboarding flags, Ollama endpoint, optional **Hugging Face token**, LLM toggle, theme, and the **data root** pointer.

Corrupt `settings.toml` surfaces as `SettingsError`; missing file returns defaults.

## Library backup boundary

**Library backup** exports the **data root** only (texts, per-language data, runtime sqlite under `.app/`). **Global settings** stay on the machine and are not part of the portable zip.

## Database access

`connect_sqlite` opens databases with WAL journaling, foreign keys, and a busy timeout for safe concurrent access by UI and worker in later phases.

`MigrationRunner` applies pending scripts. `MigrationLoader` discovers files; `split_sql_script` parses statements; `SchemaMigrationJournal` tracks applied versions; `ensure_database_parent` prepares the database directory. Packaged scripts ship under `lexiflow_core/migrations/` (`bundled_migrations_dir()`).
