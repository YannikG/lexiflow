# Phase 11-1: Markdown cleanup and native LLM runtime

**Branch:** `phase/11-1-markdown-cleanup`  
**PR title:** `Phase 11-1: Markdown cleanup and native LLM runtime`  
**Issue:** [#33](https://github.com/YannikG/lexiflow/issues/33)

**Blocked by:** [phase 11 — Simplify and new words](../phase-11-simplify/README.md) ([#12](https://github.com/YannikG/lexiflow/issues/12))  
**Blocks:** [phase 12 — Vocabulary](../phase-12-vocabulary/README.md) ([#13](https://github.com/YannikG/lexiflow/issues/13))

**Architecture:** [ADR 0007](../../../adr/0007-native-llama-server-llm.md) — native LLM via supervised `llama-server`; Ollama optional. In-process embedded Gemma (`torch`/`transformers`) was removed.

Insert phase after 11. Phase 08 defined **markdown cleanup** and phase 10-1 wired LLM providers into the worker. Users who finish onboarding still saw raw pasted text in the **native variant** when cleanup failed, llama-server was missing, or LLM output was invalid. This phase makes **staged generation** cleanup reliable end-to-end on both native and Ollama paths.

## Why this phase exists

| Symptom | Observed cause |
|---------|----------------|
| Native tab still shows the raw paste after save | `cleanup` job failed; provisional `native.md` from create is never replaced |
| Worker error: llama-server unreachable or empty LLM response | Binary missing, server not started, or wrong model pin |
| Reader says generic “not available yet” on native while cleanup failed | Job status did not surface cleanup pending/failure on the native tab |
| Translated variant echoes source language | Weak translate prompt; no validation that output differs from source |
| Simplify tab missing while job runs | Simplified tabs only appeared after file landed on disk |

## Outcome

- **Native path:** `native_llm_operational()` gates onboarding; UI supervises `llama-server`; worker calls `LlamaServerLLM` over HTTP.
- **Add text → cleanup:** `native.md` is replaced with validated LLM **markdown cleanup** output when the job succeeds.
- **Cleanup failure UX:** native reader tab and status bar show pending / failed cleanup with actionable messages.
- **Translate output:** validation rejects unchanged source, fenced-only output, and missing titles.
- **Simplify UX:** pending simplified tab and generation overlay while simplify jobs run.
- **Ollama path:** same cleanup chain verified with HTTP LLM (regression).
- CI unchanged: fakes at protocol boundaries; no real llama-server, Gemma download, or torch in pytest.

## Out of scope

- Changes to **plain translation** routing beyond validation and prompt tightening
- **Jobs panel**, retry/cancel UI, log viewer (phase 14)
- Packaging/installer bundling of llama-server (phase 15)
- Heuristic non-LLM pre-formatter for paste

## Workstreams

### A — Native LLM runtime ([ADR 0007](../../../adr/0007-native-llama-server-llm.md))

1. **`LlamaServerLLM`** — HTTP client to `/v1/chat/completions`; pinned `llama_hf_model` from `models.lock`.
2. **`native_llm_operational(settings)`** — query: binary on PATH (or `LEXIFLOW_LLAMA_SERVER_BIN`) and valid lock pin.
3. **`LlamaServerSupervisor`** (UI) — start/stop `llama-server`; loading and error copy in reader/status bar.
4. **`resolve_llm(settings)`** — Ollama when configured; else native when operational; else `UnavailableLLM`.

### B — Cleanup and translate pipeline correctness

1. **`validate_cleanup_output`** — rejects empty, unchanged, or missing `# Title` body; strips LLM code fences.
2. **`handle_cleanup`** — validate before `write_native_variant`; fail job on bad output.
3. **`validate_translate_output`** — rejects unchanged source, fences-only, invalid title.
4. **Prompt tuning** — `cleanup.md`, `translate.md`, language labels for prompts.
5. **Integration tests** — messy paste → worker loop → validated `native.md`.

### C — Reader and poll UX

1. **`cleanup_job_message`**, **`simplified_variant_job_message`**, **`pending_simplified_variants`** — job-status queries.
2. **Reader overlays** — native, translated, and simplified tabs show pending/failed generation copy.
3. **`generation_status`** — language-model loading, worker startup, simplify-specific headlines.
4. **`MainWindow` poll** — reload reader on job completion; status bar errors on failure.

## Public interfaces (delivered)

```python
# lexiflow_core.llm.llama_server
def native_llm_operational(settings: Settings) -> tuple[bool, str | None]: ...

class LlamaServerLLM: ...

# lexiflow_core.jobs.handlers.cleanup_output
class CleanupOutputError(Exception): ...
def validate_cleanup_output(*, raw_paste: str, cleaned: str) -> str: ...

# lexiflow_core.jobs.text_job_status
def cleanup_job_message(jobs, *, text_id: UUID) -> str | None: ...
def pending_simplified_variants(jobs, *, text_id: UUID) -> tuple[str, ...]: ...
def simplified_variant_job_message(jobs, *, text_id: UUID, variant_name: str) -> str | None: ...
```

**CQS:** readiness and job-status helpers are queries. Handlers call validation then commands (`write_native_variant`, `fail`, `complete`).

## Manual verification

1. **Native:** install `llama-server` → complete onboarding → add messy web paste → native tab shows cleaned markdown after worker runs.
2. **Binary missing:** remove `llama-server` from PATH → add text → status bar + native tab show install guidance.
3. **Ollama:** Ollama URL set → add text → cleanup succeeds via HTTP.
4. **Simplify:** click Simplify → simplified tab appears immediately with pending overlay → content when job completes.

## PR checklist

- [ ] Semble/context7 used for llama-server HTTP contract and PySide6 supervisor patterns
- [ ] [llm-providers.md](../../../../packages/lexiflow-core/docs/concepts/llm-providers.md) — native/Ollama only
- [ ] [model-bootstrap.md](../../../../packages/lexiflow-core/docs/concepts/model-bootstrap.md) — no v1 LexiFlow LLM download
- [ ] [add-text-and-staged-generation.md](../../../../packages/lexiflow-core/docs/concepts/add-text-and-staged-generation.md) — cleanup validation and failure behavior
- [ ] [ADR 0007](../../../adr/0007-native-llama-server-llm.md) — accepted
- [ ] Phase 12 issue **blocked by** includes 11-1 when issue created
- [ ] CI: no real model downloads in pytest

## Deferred

- Automatic llama-server install from inside the GUI (phase 15 installer)
- Trash restore UI (phase 13)
- Full cleanup garbage heuristics beyond title/body/unchanged checks
