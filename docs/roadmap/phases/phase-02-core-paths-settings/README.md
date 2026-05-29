# Phase 02: Core paths and settings

**Branch:** `phase/02-core-paths-settings`  
**PR title:** `Phase 02: Data root, settings.toml, and migration framework`

## Outcome

- **Global settings** persist under **data root** (default **app data name** layout)
- **Data root** overridable; app data directories created on first run
- **Schema migration** framework ready for later databases
- Safe concurrent database access pattern for **job queue** and **library index** (later phases)

## Scope

### In

- Path helpers: `data_root`, `.app/`, per-lang paths (stubs)
- settings schema: native_language, onboarding_complete, ollama_url, theme, etc.
- Migration framework (empty `001_initial.sql` for settings-adjacent DBs later)

### Out

- index.sqlite content (phase 03)
- queue.sqlite (phase 04)

## References

- [common-language.md](../../../../common-language.md): **Global settings**, **App data name**, **Data root**, **Schema migration**
- Phase 01 monorepo

## Public interfaces

```python
# lexiflow_core.config.settings
class SettingsStore:
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

**Edge:** Windows path (~ expand); override via settings.

---

### Cycle 2.2 — Settings round-trip

**Behavior:** Save native_language `de`, reload returns `de`.

**Test:** temp dir as data root; write/read settings.toml.

**Green:** TOML serialize/deserialize `Settings` dataclass.

**Edge:** missing file → defaults; corrupt file → clear error type `SettingsError`.

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

**Behavior:** `ensure_app_layout(data_root)` creates `.app/`, `.app/logs/`.

**Test:** nonexistent root → dirs created idempotently.

**Green:** layout helper.

---

## Manual verification

- Unit tests only; no UI required.

## PR checklist

- [ ] Cycles 2.1–2.5 pass
- [ ] Coverage on `lexiflow-core` maintained/improved
- [ ] No Qt imports in core
