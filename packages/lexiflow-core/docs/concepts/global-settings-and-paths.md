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

| Helper | Purpose |
|--------|---------|
| `app_config_dir()` | Machine-local config directory |
| `default_data_root()` | Default user library when settings omit `data_root` |
| `resolve_data_root(settings)` | Effective library path from settings (`settings` module) |
| `ensure_app_layout(data_root)` | Create `.app/` and `.app/logs/` under the library |
| `bootstrap_runtime(settings_store)` | Load settings, resolve data root, ensure layout (`bootstrap` module) |
| `language_data_root(data_root, code)` | Per-target-language folder (stub until later phases) |

## Global settings

Stored as TOML in the app config directory. Includes native language, onboarding flags, Ollama endpoint, LLM toggle, theme, and the **data root** pointer.

Corrupt `settings.toml` surfaces as `SettingsError`; missing file returns defaults.

## Library backup boundary

**Library backup** exports the **data root** only (texts, per-language data, runtime sqlite under `.app/`). **Global settings** stay on the machine and are not part of the portable zip.

## Database access

`connect_sqlite` opens databases with WAL journaling, foreign keys, and a busy timeout for safe concurrent access by UI and worker in later phases.

`MigrationRunner` applies ordered `NNN_*.sql` scripts once per database inside a transaction. `MigrationLoader` discovers scripts; `split_sql_script` parses statements. Packaged scripts ship under `lexiflow_core/migrations/` (`bundled_migrations_dir()`).
