# Phase 11-1: Markdown cleanup and native inference runtime

> **Architecture update (2026-06):** In-process embedded Gemma (`torch`/`transformers`) was replaced by **native llama-server** + **Ollama** only. See [ADR 0007](../../../adr/0007-native-llama-server-llm.md). Workstreams B/C (cleanup validation, reader UX) remain the acceptance focus; Workstream A targets `native_llm_operational` and HTTP LLM wiring instead of `embedded-llm`.

**Branch:** `phase/11-1-markdown-cleanup`  
**PR title:** `Phase 11-1: Markdown cleanup works after model bootstrap`  
**Issue:** [#33](https://github.com/YannikG/lexiflow/issues/33)

**Blocked by:** [phase 11 — Simplify and new words](../phase-11-simplify/README.md) ([#12](https://github.com/YannikG/lexiflow/issues/12))  
**Blocks:** [phase 12 — Vocabulary](../phase-12-vocabulary/README.md) ([#13](https://github.com/YannikG/lexiflow/issues/13))

Insert phase after 11. Phase 08 defined **markdown cleanup** and phase 10-1 wired **embedded Gemma** into the worker. In the real app, users who finish **model bootstrap** in onboarding still see raw pasted text in **native variant** because cleanup jobs fail: weights download succeeds but the inference subprocess cannot import `transformers` / `torch`. This phase closes that gap and makes **staged generation** cleanup reliable end-to-end.

## Why this phase exists

| Symptom | Observed cause |
|---------|----------------|
| Native tab still shows the raw paste after save | `cleanup` job failed; provisional `native.md` from create is never replaced |
| Worker error: `Gemma inference subprocess failed … No module named 'transformers'` | Model snapshot on disk; Python inference runtime not installed or not verified |
| Reader says generic “not available yet” on native while cleanup failed | `text_job_status` only covers translate/simplify variants, not cleanup |
| Wizard reports bootstrap complete | `embedded_gemma_installed()` checks weights + revision marker only, not runnable inference |

Phase 10-1 assumed the embedded subprocess would load ML deps; phase 07 only downloads Hugging Face artifacts. Nothing guarantees the same Python env can run `python -m lexiflow_core.llm.gemma_inference`.

## Outcome

- **Embedded path:** finishing onboarding means cleanup jobs can call the cached Gemma snapshot (runtime installed and smoke-checked, not just weights).
- **Add text → cleanup:** `native.md` is replaced with LLM **markdown cleanup** output (structured markdown, junk stripped, wording preserved). User no longer stuck on the provisional create-time file when cleanup succeeds.
- **Cleanup failure UX:** native reader tab and status bar show pending / failed cleanup with actionable messages (not raw subprocess tracebacks).
- **Ollama path:** same cleanup chain verified with HTTP LLM (regression; no new Ollama features).
- CI unchanged: fakes at protocol boundaries; no real Gemma or torch in pytest.

## Out of scope

- Changes to **plain translation** handler, prompts, or post-translate metadata rules
- **Simplify** feature work (may benefit from shared runtime fix; not acceptance criteria here)
- **Jobs panel**, retry/cancel UI, log viewer (phase 14)
- Packaging/installer bundling of torch wheels (phase 15; this phase defines dev + runtime contract only)

## Root cause (fix plan)

### Workstream A — Inference runtime matches bootstrap promise

1. Add an **`embedded-llm`** uv dependency group (pinned `transformers` + `torch` compatible with `google/gemma-4-E2B-it`).
2. Introduce **`embedded_inference_runtime_ready(data_root) -> bool | str`** (query): subprocess import smoke or lightweight `-m lexiflow_core.llm.gemma_inference --check` mode; returns actionable reason when false.
3. **Onboarding embedded path:** after weight download, run runtime check; block “complete” (or show install/retry step) until ready. Document `uv sync --group embedded-llm` for dev installs.
4. **`resolve_llm`:** when weights present but runtime missing, return provider that fails jobs with bootstrap guidance (not mid-job `ModuleNotFoundError`).

### Workstream B — Cleanup pipeline correctness

1. **`validate_cleanup_output(raw_paste, cleaned) -> None`** in core (raises `CleanupOutputError` on empty, unchanged, or non-markdown garbage). Validation checks structure only (paragraphs, list/heading markers, length sanity); **does not** change translation or library naming rules.
2. **`handle_cleanup`:** validate before `write_native_variant`; fail job with short message; do not mark cleanup completed on bad LLM output.
3. **Prompt tuning (minimal):** tighten `cleanup.md` examples for plain-text paste → readable markdown body; keep “preserve wording verbatim” rule.
4. **Integration test:** enqueue cleanup with messy paste fixture → worker loop → `native.md` content differs from raw paste and passes validation.

### Workstream C — Reader and poll UX for cleanup

1. Extend **`text_job_status.missing_variant_message`** (or sibling) for **native variant** + `JobType.CLEANUP`.
2. **Reader native tab:** when file exists but cleanup still pending, show “still being generated”; when cleanup failed, show `Generation failed: …` (same pattern as translated tab).
3. **`MainWindow` poll:** on cleanup completion, reload reader native content; on cleanup failure, `WorkerStatusBar.show_job_error` with shortened message.

## References

- [common-language.md](../../../../common-language.md): **Markdown cleanup**, **Staged generation**, **Add text flow**, **Model bootstrap**, **Embedded model**, **Background job**
- [add-text-and-staged-generation.md](../../../../packages/lexiflow-core/docs/concepts/add-text-and-staged-generation.md)
- [llm-providers.md](../../../../packages/lexiflow-core/docs/concepts/llm-providers.md)
- [model-bootstrap.md](../../../../packages/lexiflow-core/docs/concepts/model-bootstrap.md)
- Phase 08: cleanup handler, `cleanup.md`
- Phase 10-1: `EmbeddedGemmaLLM`, `resolve_llm`, worker main
- [ADR 0003](../../../../docs/adr/0003-job-execution-architecture.md) — subprocess isolation

## Public interfaces (target)

```python
# lexiflow_core.llm.runtime — new module (SRP: embedded inference readiness)
def embedded_inference_runtime_ready(*, python: str | None = None) -> tuple[bool, str | None]:
    """Query: True when subprocess can import ML deps; else (False, user_message)."""

# lexiflow_core.jobs.handlers.cleanup_output — new module (SRP: validate LLM cleanup)
class CleanupOutputError(Exception): ...

def validate_cleanup_output(*, raw_paste: str, cleaned: str) -> None: ...

# lexiflow_core.jobs.text_job_status — extend queries
def cleanup_job_message(jobs, *, text_id: UUID) -> str | None: ...

# pyproject.toml (workspace root)
[dependency-groups]
embedded-llm = ["torch>=...", "transformers>=..."]
```

**CQS:** readiness and job-status helpers are queries. Handlers call validation then commands (`write_native_variant`, `fail`, `complete`).

## TDD cycles

### Cycle 11-1.1 — embedded-llm dependency group documented

**Test:** import test or lockfile doc that group exists; CI does not install group by default.

---

### Cycle 11-1.2 — embedded_inference_runtime_ready detects missing transformers

**Test:** patch subprocess / import to simulate missing module → `(False, actionable message)`.

---

### Cycle 11-1.3 — resolve_llm fails clearly when weights OK, runtime missing

**Test:** fake installed marker + patch runtime ready false → `complete()` raises with bootstrap hint, not `ModuleNotFoundError`.

---

### Cycle 11-1.4 — validate_cleanup_output rejects empty and unchanged

**Test:** empty string → `CleanupOutputError`; cleaned identical to raw paste → error.

---

### Cycle 11-1.5 — validate_cleanup_output accepts structured markdown

**Test:** messy paste in, fixture with paragraphs and `# section` body markers → passes.

---

### Cycle 11-1.6 — handle_cleanup fails job when validation fails

**Test:** FakeLLM returns garbage → job failed, native.md unchanged from pre-cleanup state.

---

### Cycle 11-1.7 — handle_cleanup writes validated markdown

**Test:** FakeLLM returns formatted markdown → job completed, native.md updated, translate job enqueued.

---

### Cycle 11-1.8 — Worker E2E cleanup after add text

**Test:** `submit_new_text` → run_worker_loop with FakeLLM → native.md markdownized per validation.

---

### Cycle 11-1.9 — text_job_status cleanup messages

**Test:** pending cleanup → “still being generated”; failed cleanup with error → “Generation failed: …”.

---

### Cycle 11-1.10 — Reader shows cleanup failure on native tab

**Test:** pytest-qt open text with failed cleanup job → message visible in native reader.

---

### Cycle 11-1.11 — Onboarding gate (embedded path)

**Test:** bootstrap coordinator with weights installed, runtime not ready → onboarding not complete / shows retry (exact UX TBD in PR; test public coordinator API).

---

## Manual verification

1. **Dev embedded:** `uv sync --group embedded-llm` → complete onboarding → add messy web paste → native tab shows cleaned markdown after worker runs.
2. **Runtime missing:** remove transformers from env, weights still on disk → add text → status bar + native tab show install/bootstrap message (no multi-line traceback).
3. **Ollama:** Ollama URL set, no embedded weights → add text → cleanup succeeds via HTTP.

## PR checklist

- [ ] Semble/context7 used for transformers subprocess contract and uv dependency groups
- [ ] Update [llm-providers.md](../../../../packages/lexiflow-core/docs/concepts/llm-providers.md) — runtime vs weights distinction, `embedded-llm` group
- [ ] Update [model-bootstrap.md](../../../../packages/lexiflow-core/docs/concepts/model-bootstrap.md) — onboarding completes only when runtime ready (embedded path)
- [ ] Update [add-text-and-staged-generation.md](../../../../packages/lexiflow-core/docs/concepts/add-text-and-staged-generation.md) — cleanup validation and failure behavior
- [ ] Phase 12 issue **blocked by** includes 11-1 when issue created
- [ ] CI: no torch/transformers download in pytest

## Deferred

- Automatic `uv sync` from inside the GUI (phase 14/15 installer owns env mutation)
- Heuristic non-LLM pre-formatter for paste (only if LLM path still too slow after this phase)
- Trash restore UI (phase 13)
