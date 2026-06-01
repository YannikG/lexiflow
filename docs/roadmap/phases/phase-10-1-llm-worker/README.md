# Phase 10-1: Worker LLM provider wiring

**Branch:** `phase/10-1-llm-worker`  
**PR title:** `Phase 10-1: Worker LLM provider wiring (Ollama + embedded Gemma)`  
**Issue:** [#30](https://github.com/YannikG/lexiflow/issues/30)

**Blocked by:** [phase 10 — Embeddings and sqlite-vec](../phase-10-embeddings/README.md) ([#11](https://github.com/YannikG/lexiflow/issues/11))  
**Blocks:** [phase 11 — Simplify and new words](../phase-11-simplify/README.md) ([#12](https://github.com/YannikG/lexiflow/issues/12))

Insert phase after phase 10. Phase 08 built translate/cleanup **handlers** and phase 07 **model bootstrap**; the worker entrypoint still hardcodes `FakeLLM()`, so add-text → translate fails in the real app. This phase wires **production LLM providers** into `lexiflow_worker` while CI keeps `FakeLLM`.

## Why this phase exists

- **Phase 04** introduced `FakeLLM` for headless queue tests ([ADR 0001](../../../adr/0001-split-packages-and-ci-quality-gates.md)).
- **Phase 08** manual verification expects paste → jobs → translated text in the **sidebar**; that requires a real `LLMProvider` in the worker.
- **Phase 11** simplify and **phase 14** **LLM toggle** / **worker-linked model lifecycle** assume the worker can call translate/simplify/cleanup providers ([common-language.md](../../../../common-language.md) **Provider mode**, **Embedded model**, **Ollama endpoint**).

Without 10-1, only pytest with injected fakes exercises the LLM job path end-to-end.

## Outcome

- **`resolve_llm(settings, data_root) -> LLMProvider`** selects provider from **global settings** (same rules as **Provider mode** in glossary).
- **`OllamaLLM`** — HTTP client for translate/cleanup/simplify when **Ollama endpoint** is set.
- **`EmbeddedGemmaLLM`** — loads pinned **embedded model** (`google/gemma-4-E2B-it`) from local cache; inference in an **isolated Python subprocess** (`transformers` + `torch` in `lexiflow_core.llm.gemma_inference`) inside the worker ([ADR 0003](../../../adr/0003-job-execution-architecture.md)).
- **`lexiflow_worker.main`** loads settings from `data_root`, calls `resolve_llm`, passes result to `run_worker_loop` (no hardcoded `FakeLLM()` in production entry).
- Add-text → cleanup → translate completes in the **desktop app** (Ollama or embedded path per onboarding choice).
- CI unchanged: tests inject `FakeLLM` / HTTP fakes at protocol boundaries; no real Gemma download in PR CI.

## References

- [ADR 0003](../../../adr/0003-job-execution-architecture.md) — worker process, LLM subprocess, idle unload
- [ADR 0001](../../../adr/0001-split-packages-and-ci-quality-gates.md) — `FakeLLM` in CI
- [common-language.md](../../../../common-language.md): **LLM provider**, **Provider mode**, **Embedded model**, **Ollama endpoint**, **Worker-linked model lifecycle**, **Staged generation**, **Plain translation**
- [model-bootstrap.md](../../../../packages/lexiflow-core/docs/concepts/model-bootstrap.md) — artifact cache, `required_artifact_ids`
- Phase 08: cleanup/translate handlers
- Phase 10: worker embedder resolution pattern (`lexiflow_worker/embedder.py`)

## Public interfaces (target)

```python
# lexiflow_core.llm.protocol — existing
class LLMProvider(Protocol):
    def complete(
        self, prompt: str, *, json_schema: dict[str, object] | None = None
    ) -> str: ...

# lexiflow_core.llm.ollama
class OllamaLLM:
    def __init__(self, *, base_url: str, model: str) -> None: ...
    def complete(self, prompt: str, *, json_schema: dict[str, object] | None = None) -> str: ...

# lexiflow_core.llm.embedded_gemma (or llm/subprocess_gemma.py — layout TBD in PR)
class EmbeddedGemmaLLM:
    def __init__(self, *, model_dir: Path) -> None: ...
    def complete(self, prompt: str, *, json_schema: dict[str, object] | None = None) -> str: ...

# lexiflow_core.llm.resolution
def resolve_llm(settings: Settings, data_root: Path) -> LLMProvider: ...

# lexiflow_worker.main — load SettingsStore, resolve_llm, run_worker_loop(..., llm=...)
```

**CQS:** `resolve_llm` is a query (reads settings + disk; no queue writes). Worker `main` orchestrates load → run loop.

## TDD cycles

### Cycle 10-1.1 — resolve_llm picks Ollama when ollama_url set

**Test:** `Settings(ollama_url="http://127.0.0.1:11434")` → returns `OllamaLLM` (type or behavior via fake HTTP).

---

### Cycle 10-1.2 — OllamaLLM complete via HTTP fake

**Test:** stub server returns markdown with `# Title` → `complete(prompt)` returns body; no real Ollama in CI.

---

### Cycle 10-1.3 — resolve_llm picks embedded when no Ollama and Gemma installed

**Test:** settings without `ollama_url`, fake installed marker for `embedded-gemma` → `EmbeddedGemmaLLM` (or skip with `pytest.importorskip` if subprocess binary not in CI — use protocol fake that stands in for embedded in unit test, subprocess tested manually).

---

### Cycle 10-1.4 — Worker main uses resolve_llm

**Test:** temp data_root + settings.toml with `ollama_url` → `main(["--data-root", ...])` completes translate job using HTTP fake (patch `resolve_llm` or inject test server).

---

### Cycle 10-1.5 — Staged generation E2E (cleanup → translate)

**Test:** enqueue cleanup + translate chain; worker with `OllamaLLM` fake → `translated.md` exists with H1; **EMBED** job enqueued (phase 10); no `no document title heading found`.

---

### Cycle 10-1.6 — llm_enabled false fails LLM jobs clearly

**Test:** `Settings(llm_enabled=False)` → translate job **failed** with actionable error (not FakeLLM stub output). Full **LLM toggle** UX remains phase 14; worker must not silently use fake completions.

---

## Manual verification

- **Ollama path:** Ollama running; add text → translated variant appears; embed job completes (phase 10 worker embedder).
- **Embedded path:** Gemma cached from onboarding; same flow without Ollama URL.
- Optional: subprocess crash isolation smoke (kill Gemma inference child → worker reports failed job, UI stays up).

## PR checklist

- [ ] `lexiflow_worker.main` no longer hardcodes `FakeLLM()` for production
- [ ] Semble/context7 used for Ollama HTTP API and Gemma subprocess inference contract
- [ ] Concept doc `packages/lexiflow-core/docs/concepts/llm-providers.md`
- [ ] No llama.cpp / heavy ML imports in **lexiflow-ui**
- [ ] Phase 11 issue **blocked by** includes 10-1 ([#30](https://github.com/YannikG/lexiflow/issues/30)) and 10b when issue created
- [ ] CI: no real Hugging Face / Ollama required in pytest

## Deferred out of scope

- **LLM toggle** UI, idle unload timer, crash restart dialog (phase 14)
- **Simplify** job handler (phase 11) — but 10-1 must expose `LLMProvider` simplify can reuse
- **Structured JSON schema** enforcement for simplify (phase 11); `json_schema` param may no-op on Ollama in 10-1
- Swapping provider at runtime without worker restart (restart worker is enough for v1)

## Relationship to phase 10b

[Phase 10b](../phase-10b-ollama-embeddings/README.md) wires **Ollama embeddings**; **10-1** wires **Ollama LLM**. They can land in parallel after phase 10; phase 11 should wait for both.
