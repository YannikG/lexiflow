# Native LLM via llama-server (no in-process torch)

**Status:** Accepted  
**Date:** 2026-06-01  
**Supersedes:** in-process embedded Gemma path from phase 10-1 (implementation removed)  
**Implementation:** phase 11-1+

## Context

Phase 10-1 wired **EmbeddedGemmaLLM** with a subprocess running `transformers` + `torch`. Phase 11-1 exposed reliability and packaging problems: bootstrap could download weights while the Python env could not run inference; torch wheels are heavy and awkward for a desktop app.

Product direction: two LLM backends only — **native llama-server** (default) and **Ollama** (advanced). Users should not manage GGUF files or LexiFlow-managed model caches for the LLM.

## Decision

1. **Remove** in-process Gemma / `embedded-llm` uv group from the worker path.
2. **Native LLM:** UI supervises a local `llama-server` process; worker calls HTTP `/v1/chat/completions` via `LlamaServerLLM`.
3. **Model source:** pinned `llama_hf_model` in `models.lock`; llama-server loads from Hugging Face with `-hf`. LexiFlow does not download or store LLM weights under `{data_root}/.app/models/`.
4. **Embeddings:** pinned MiniLM repo/revision in `models.lock`; worker loads via `sentence-transformers` from Hugging Face on first use (no LexiFlow bootstrap download in v1).
5. **Readiness:** `native_llm_operational()` checks binary on PATH (or `LEXIFLOW_LLAMA_SERVER_BIN`) and valid lock pin; onboarding blocks native path when false.

## Rationale

| Factor | llama-server |
|--------|----------------|
| Packaging | No torch in LexiFlow Python env |
| UX | Hugging Face fetch delegated to llama-server / sentence-transformers |
| Isolation | LLM crash domain is separate process (aligns with ADR 0003 spirit) |
| Ollama parity | Both native and Ollama are HTTP clients from the worker |

## Consequences

- Update **common-language.md**, concept docs, and phase READMEs for native/Ollama wording.
- Onboarding: no model download page in v1; optional HF token for gated repos.
- CI: `FakeLLM` / HTTP fakes only; no real llama-server in pytest.
- Phase 14 may reintroduce `ModelStore` maintenance UI without v1 bootstrap downloads.
