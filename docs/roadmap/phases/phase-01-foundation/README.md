# Phase 01: Foundation

**Branch:** `phase/01-foundation`  
**PR title:** `Phase 01: Monorepo scaffold with green CI and hello window`

## Outcome

After merge:

- Three packages exist (**lexiflow-core**, **lexiflow-ui**, **lexiflow-worker**) in a uv monorepo
- Minimal **application shell**: LexiFlow window opens and quits cleanly
- **CI quality gates** fully green (lint, typecheck, tests)
- Developer can clone, sync, run, and test from README

**Prerequisite:** Phase 00 on `main`, issues 01–15 created, branch protection enabled.

## Scope

### In

- Monorepo layout, package stubs with `pyproject.toml`
- Minimal main window (quit works)
- CI jobs pass with real tests; coverage config (80% core / 60% ui — may ratchet)
- Dependabot `pip` ecosystem in `.github/dependabot.yml` (phase 00 ships Actions only)
- First concept doc stub: `packages/lexiflow-core/docs/concepts/application-shell.md` (proves **application shell** hello window)

### Out

- Domain logic, storage, worker, LLM (later phases)
- Re-creating AGENTS/CONTRIBUTING/SECURITY (phase 00)
- PyInstaller, release workflow (phase 15)

## References

- [ADR-0001](../../adr/0001-split-packages-and-ci-quality-gates.md)
- [Agent workflow](../../guides/agent-workflow.md)
- [common-language.md](../../../../common-language.md): **Application shell**, **Desktop shell**, **lexiflow-core**, **lexiflow-ui**, **lexiflow-worker**, **CI quality gates**, **TDD vertical slice**, **PR Plan**, **Concept doc**

## Target public interfaces

```python
# lexiflow_ui.app
def run() -> int: ...  # starts QApplication, MainWindow

# lexiflow_worker.main
def main() -> int: ...  # stub: log "worker ready", exit 0

# lexiflow_core.__version__
__version__: str
```

## TDD cycles

Execute **in order**. One behavior per cycle.

---

### Cycle 1.1 — Core package imports

**Behavior:** `lexiflow_core` exposes version string.

**Test:** `tests/core/test_version.py` — `import lexiflow_core; assert lexiflow_core.__version__`

**Green:** Minimal package with `__version__ = "0.0.0"`.

**Edge:** none.

---

### Cycle 1.2 — UI application starts headless-testable

**Behavior:** `run()` returns 0 when app quits immediately (pytest-qt).

**Test:** `tests/ui/test_app_smoke.py` — `qtbot` launches app, closes, exit code 0.

**Green:** `MainWindow` with title "LexiFlow", empty central widget.

**Edge:** `run()` idempotent guard if already instance (optional stub).

---

### Cycle 1.3 — Worker entrypoint stub

**Behavior:** `lexiflow-worker` module main exits 0.

**Test:** `tests/worker/test_main.py` — subprocess or import `main()` → 0.

**Green:** `if __name__ == "__main__": print("worker stub"); return 0`

---

### Cycle 1.4 — Ruff + format gate

**Behavior:** CI fails on lint/format violations.

**Test:** CI job itself (no code test). Locally: introduce violation → `ruff check` fails.

**Green:** `pyproject.toml` ruff config; `uv run ruff check .` clean.

---

### Cycle 1.5 — pytest discovery all packages

**Behavior:** `uv run pytest` collects core + ui tests.

**Test:** CI pytest job passes with ≥3 tests.

**Green:** `tests/` layout, `pytest.ini` / pyproject pytest config.

---

### Cycle 1.6 — mypy on core

**Behavior:** `uv run mypy packages/lexiflow-core` passes.

**Test:** CI mypy job.

**Green:** Typed public APIs for version + stubs.

---

### Cycle 1.7 — pre-commit hooks

**Behavior:** `pre-commit run --all-files` runs ruff.

**Test:** Manual + `.pre-commit-config.yaml` in repo.

**Green:** Hook config committed.

---

## Manual verification

1. `uv sync`
2. `uv run python -m lexiflow_ui` → window appears
3. `uv run pytest`
4. Push PR → all CI checks green

## PR checklist

- [ ] All cycles 1.1–1.7 green
- [ ] README: clone, uv sync, run app, run tests
- [ ] **Plan posted** per [pr-plan-template.md](../../guides/pr-plan-template.md)
- [ ] Concept doc: `application-shell.md` (or phase-appropriate concept)
- [ ] No domain logic beyond hello world
