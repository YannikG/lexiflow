# Phase 02: Core paths and settings

**Branch:** `phase/02-core-paths-settings`  
**PR title:** `Phase 02: Data root, settings.toml, and migration framework`

## Corrections (2026-05-29)

**Gap in original plan:** **Global settings** were specified inside **data root** (`.app/settings.toml`), while **data root** itself is overridable in settings. That creates a bootstrap chicken-and-egg: the app cannot know which folder to open before it has already read settings.

**Corrected design:**

| Concern | Location | Portable with library backup zip? |
|---------|----------|-----------------------------------|
| **Global settings** (`settings.toml`) | **App config directory** — fixed per machine, resolved before **data root** | No (machine-local) |
| User library (**data root**) | Default `~/LexiFlow/`; path stored in settings as `data_root` | Yes |
| Runtime app data under library (`.app/`) | `{data_root}/.app/` — sqlite DBs, models cache, logs | Yes (part of **data root**) |

- `app_config_dir()` → `settings.toml` (bootstrap always works).
- `resolve_data_root(settings)` → library path; `default_data_root()` when unset.
- **Library backup** (phase 13+) exports **data root** only; machine settings are out of scope for that zip.

**Docs to sync in this PR:** [common-language.md](../../../../common-language.md) (**Global settings**), [docs/architecture/overview.md](../../../architecture/overview.md) (remove `settings.toml` from `.app/` tree).

---

## Outcome

- **Global settings** persist in **app config directory** (machine-local bootstrap)
- **Data root** (user library) overridable via settings; default **app data name** layout under home
- App data directories under **data root** created on first run
- **Schema migration** framework ready for later databases
- Safe concurrent database access pattern for **job queue** and **library index** (later phases)

## Scope

### In

- Path helpers: `app_config_dir`, `default_data_root`, `resolve_data_root`, `{data_root}/.app/`, per-lang paths (stubs)
- Settings schema: `data_root`, native_language, onboarding_complete, ollama_url, theme, etc.
- Migration framework (empty `001_initial.sql` for settings-adjacent DBs later)

### Out

- index.sqlite content (phase 03)
- queue.sqlite (phase 04)

## References

- [common-language.md](../../../../common-language.md): **Global settings**, **App data name**, **Data root**, **Schema migration**
- Phase 01 monorepo

## Public interfaces

```python
# lexiflow_core.config.paths
def app_config_dir() -> Path: ...
def default_data_root() -> Path: ...
def resolve_data_root(settings: Settings) -> Path: ...
def ensure_app_layout(data_root: Path) -> None: ...

# lexiflow_core.config.settings
class SettingsStore:
    def __init__(self, config_dir: Path | None = None) -> None: ...
    def load(self) -> Settings: ...
    def save(self, settings: Settings) -> None: ...

# lexiflow_core.db.migrations
class MigrationRunner:
    def migrate(self, db_path: Path, scripts_dir: Path) -> None: ...

# lexiflow_core.db.connection
def connect_sqlite(path: Path) -> sqlite3.Connection: ...  # WAL enabled
```

## TDD cycles

### Cycle 2.1 — Default data root

**Behavior:** Fresh install uses `~/LexiFlow/` when unset.

**Test:** `test_default_data_root_is_lexiflow_home` with `$HOME` tmp.

**Green:** `default_data_root() -> Path`.

**Edge:** Windows path (`~` expand).

---

### Cycle 2.2 — Settings round-trip

**Behavior:** Save native_language `de`, reload returns `de`. Settings file lives in **app config directory**, not under **data root**.

**Test:** temp dir as `config_dir`; `SettingsStore(config_dir)` write/read `settings.toml`.

**Green:** TOML serialize/deserialize `Settings` dataclass.

**Edge:** missing file → defaults; corrupt file → clear error type `SettingsError`. `data_root` in settings → `resolve_data_root` returns that path.

---

### Cycle 2.3 — WAL on connect

**Behavior:** `connect_sqlite` sets `journal_mode=WAL`.

**Test:** open db, `PRAGMA journal_mode` → `wal`.

**Green:** connection helper.

---

### Cycle 2.4 — Migration applies once

**Behavior:** Script `001.sql` creates table; second migrate no-op.

**Test:** temp db + scripts dir with CREATE TABLE.

**Green:** `schema_migrations(version)` tracking.

**Edge:** failed mid-script rolls back; higher version scripts apply in order.

---

### Cycle 2.5 — Ensure app directories exist

**Behavior:** `ensure_app_layout(data_root)` creates `{data_root}/.app/`, `{data_root}/.app/logs/`. Does **not** create settings (settings live in **app config directory**).

**Test:** nonexistent data root → dirs created idempotently.

**Green:** layout helper.

---

## Manual verification

- Unit tests only; no UI required.

## PR checklist

- [ ] Cycles 2.1–2.5 pass
- [ ] Coverage on `lexiflow-core` maintained/improved
- [ ] No Qt imports in core
- [ ] **Corrections** synced: `common-language.md` + `docs/architecture/overview.md`
