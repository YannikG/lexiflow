# Phase 14: Settings, jobs, and polish

**Branch:** `phase/14-settings-polish`  
**PR title:** `Phase 14: Jobs panel, worker lifecycle, theme, updates, reset`

## Outcome

- **Jobs panel** with Pending, Running, Failed, Completed history; Retry and Cancel
- **Shutdown with active jobs**: Wait or Quit anyway
- **Worker idle lifecycle** and **LLM toggle**; crash → **restart worker**
- **Settings**: Ollama, **Hugging Face token**, **data root**, **theme**, appearance
- **Model updates** UI: wire `ModelStore.check_for_updates()` and edit `huggingface_token` (backend from phase 07)
- **About dialog**: **system requirements**, version, logs
- **In-app updates** notification with download link
- **Reset app** factory wipe + **onboarding flow**
- **Re-translate** and **Re-simplify** in reader
- Drag text between **groups**; **properties panel** for **text metadata editing**

## References

- [common-language.md](../../../../common-language.md): **Jobs panel**, **Job history UI**, **Shutdown with active jobs**, **Worker idle lifecycle**, **In-app updates**, **Onboarding flow**, **Theme**, **Appearance**, **Reset app**, **Re-translate**, **Re-simplify**
- [ADR-0006](../../../adr/0006-desktop-ui-theme-strategy.md) — **Theme** toggle calls `apply_app_theme`; **appearance** panel for reader font size
- [ui-theme.md](../../../../packages/lexiflow-ui/docs/concepts/ui-theme.md)

## TDD cycles

### Cycle 14.1 — Cancel running job marks cancelled/failed

**Test:** cancel → job not completed; partial not saved.

---

### Cycle 14.2 — Quit anyway → running becomes pending

**Test:** supervisor shutdown wait=false → queue state.

---

### Cycle 14.3 — Worker idle timeout shuts down process

**Test:** fake timer 5min → supervisor stops worker.

---

### Cycle 14.4 — Restart worker after crash

**Test:** worker exit code != 0 → dialog signal; restart spawns new process.

---

### Cycle 14.5 — Update check notifies when newer tag

**Test:** mock GitHub API → banner with link.

---

### Cycle 14.5b — Model pin update check in settings

**Test:** installed revision older than `models.lock` → settings shows `UpdateAvailable` list; user-initiated only.

**Depends on:** phase 07 `ModelStore.check_for_updates()` and `Settings.huggingface_token`.

---

### Cycle 14.6 — Factory reset deletes models + data

**Test:** reset → empty data root, onboarding flag false.

---

### Cycle 14.7 — Re-translate enqueues job

**Test:** button click → TRANSLATE job for text id.

---

### Cycle 14.8 — Drag group updates repository

**Test:** qt signal → move_to_group called.

---

### Cycle 14.9 — Theme toggle reapplies UI theme

**Behavior:** Changing **Theme** in **settings** updates the visible **UI theme** (restart acceptable in v1 if runtime apply is deferred).

**Test:** pytest-qt — set Dark in settings UI → `apply_app_theme` invoked or app restarts with dark chrome.

**Depends on:** phase 9-2 bootstrap ([ADR-0006](../../../adr/0006-desktop-ui-theme-strategy.md)).

---

## Manual verification

- Full quit/wait flow with queued jobs.

## PR checklist

- [ ] Failed jobs manual retry only
- [ ] Zero telemetry
