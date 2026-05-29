# Ollama embedding provider deferred until after phase 10

**Status:** Accepted  
**Date:** 2026-05-29  
**Supersedes:** none  
**Implementation:** [phase 10b — Ollama embeddings](../roadmap/phases/phase-10b-ollama-embeddings/README.md) (after [phase 10](../roadmap/phases/phase-10-embeddings/README.md))

## Context

Onboarding offers **Ollama** for translate/simplify/cleanup (LLM only). Users still download the pinned **MiniLM** embedding model from Hugging Face on that path ([ADR context in phase 07](../roadmap/phases/phase-07-model-bootstrap/README.md), cycle 7.4). Domain language states: **Ollama replaces embedded LLM only; embeddings run in-app from Hugging Face** ([common-language.md](../../common-language.md)).

Ollama exposes an embeddings HTTP API (`/api/embeddings`), so a single-provider setup (LLM + embeddings via Ollama) is technically possible and would simplify onboarding (no HF token / MiniLM download when Ollama is selected).

## Decision

1. **Phase 10** ships the baseline embedding stack: `Embedder` protocol, in-process **MiniLM** (384-dim), sqlite-vec storage, and the **embedding queue**. Do not block phase 10 on Ollama embeddings.
2. **Phase 10b** (new roadmap phase, immediately after phase 10) implements optional **Ollama-backed embeddings** when `ollama_url` is configured, including ADR follow-through in code and `common-language.md`.
3. Until phase 10b merges, **required_artifact_ids** and onboarding copy remain unchanged: MiniLM is always required, even with Ollama.

## Rationale

| Factor | Defer to 10b |
|--------|----------------|
| **Vector contract** | Phase 10 fixes schema and tests on 384-dim MiniLM. Ollama embed models vary by name and dimension; choosing and pinning one compatible model needs the `Embedder` + `VectorStore` APIs from phase 10. |
| **Provider switch** | Moving HF → Ollama (or back) invalidates existing vectors unless we store provider metadata and re-embed; that policy belongs with embed jobs, not model bootstrap. |
| **Phase scope** | Phase 07 owns download/bootstrap; phase 10 owns embed runtime; Ollama embed wiring spans worker, settings, onboarding, and `required_artifact_ids`. |
| **Simplify / search** | Phase 11+ assume stable similarity; baseline embedder must exist first. |

## Considered alternatives

- **Implement in phase 07 (onboarding):** Skips MiniLM download for Ollama users without an `OllamaEmbedder` or dimension strategy — breaks phase 10/11 assumptions.
- **Never support Ollama embeddings:** Keeps HF friction for all Ollama users; rejected as UX goal for a later release.
- **Insert into phase 14 settings only:** Hides policy in polish phase; onboarding and `required_artifact_ids` would stay wrong until then.

## Consequences

- **Phase 10:** `Embedder` + `MiniLMEmbedder` (or equivalent) only; document Ollama deferral in phase 10 README.
- **Phase 10b:** `OllamaEmbedder`, pinned Ollama embed model id, skip MiniLM bootstrap when Ollama provides embeddings, onboarding/settings updates, tests with HTTP fake; update **Ollama and embeddings** in common-language.
- **Phase 11+:** May assume vectors exist; must tolerate provider metadata if 10b adds re-embed on switch (specified in 10b README).
- **GitHub issues (v1):** Add issue **Phase 10b** blocked by phase 10, blocking phase 11 (update phase 11 blocker when created).

## Open questions (resolve in phase 10b spec / PR)

- Which **Ollama embed model** is pinned (must match 384-dim sqlite-vec schema from phase 10, or phase 10b extends schema with per-vector provider + dimension)?
- **Re-embed** on provider change: mandatory for v1 10b or follow-up cycle?
- **Rate limits / offline:** Ollama down during embed job — same retry semantics as LLM HTTP errors?
