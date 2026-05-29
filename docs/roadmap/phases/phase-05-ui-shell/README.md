# Phase 05: UI shell

**Branch:** `phase/05-ui-shell`  
**PR title:** `Phase 05: Main window, sidebar, single-instance, worker supervisor stub`

## Outcome

- **Application shell** with toolbar, **sidebar**, **status bar**
- **Navigation modes**: Texts and **Vocabulary** (**empty state** when empty)
- **Single instance**; second launch offers open existing or close
- Worker spawns from same bundle (stub ok from phase 04)
- **Worker status** visible in **status bar** (offline until connected)

## References

- [ADR-0003](../../adr/0003-job-execution-architecture.md)
- [common-language.md](../../../../common-language.md): **Application shell**, **Navigation modes**, **Single instance**, **Worker status**, **Active target language**

## Public interfaces

```python
# lexiflow_ui.single_instance
class SingleInstanceGuard: ...

# lexiflow_ui.worker_supervisor
class WorkerSupervisor:
    def ensure_running(self) -> None: ...
    def shutdown(self, *, wait: bool) -> None: ...
    @property
    def state(self) -> WorkerState: ...
```

## TDD cycles

### Cycle 5.1 — Main window shows LexiFlow + modes

**Test:** pytest-qt — toolbar exists, sidebar exists, title LexiFlow.

---

### Cycle 5.2 — Single instance first launch acquires server

**Test:** guard acquired; server name lexiflow-{user}.

---

### Cycle 5.3 — Second instance shows dialog choice

**Test:** mock second process connection → dialog signal or callback with Open/Close.

**Edge:** stale server from crash — optional cleanup doc.

---

### Cycle 5.4 — Worker supervisor spawn

**Test:** fake subprocess; `ensure_running()` called once; state idle.

---

### Cycle 5.5 — Status bar worker offline when not spawned

**Test:** initial state offline.

---

### Cycle 5.6 — Quit with no jobs exits cleanly

**Test:** close event → supervisor shutdown called.

---

## Manual verification

1. Launch app twice → dialog
2. Status bar visible

## PR checklist

- [ ] No LLM imports in ui package
- [ ] pytest-qt in CI
