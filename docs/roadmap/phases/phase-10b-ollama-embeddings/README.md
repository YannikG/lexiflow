# Phase 10b: Ollama embedding provider

**Branch:** `phase/10b-ollama-embeddings`  
**PR title:** `Phase 10b: Ollama embedder, skip MiniLM when Ollama configured`  
**ADR:** [0005 — Ollama embedding provider deferred](../../../adr/0005-ollama-embedding-provider-deferred.md)

**Blocked by:** [phase 10 — Embeddings and sqlite-vec](../phase-10-embeddings/README.md)  
**Blocks:** [phase 11 — Simplify and new words](../phase-11-simplify/README.md) (update GitHub **blocked by** when this issue exists)

Insert phase between 10 and 11. Phase 10 establishes MiniLM + `Embedder` + vector storage; this phase adds an optional second provider without re-opening bootstrap design from phase 07.

## Outcome

- When **Ollama endpoint** is set, **embedding jobs** use `OllamaEmbedder` (HTTP) instead of in-process MiniLM.
- **Onboarding** Ollama path no longer downloads MiniLM or shows HF token UI for embeddings (LLM via Ollama only).
- **`required_artifact_ids`:** empty embedding requirement when Ollama embeddings are active (Gemma already skipped).
- **Pinned Ollama embed model** documented in manifest or settings (same discipline as **model pinning**).
- **Provider switch** policy documented and tested (re-embed queue or block switch until rebuild — choose in cycle 10b.3).
- [common-language.md](../../../../common-language.md) **Ollama and embeddings** updated to match shipped behavior.

## References

- [ADR 0005](../../../adr/0005-ollama-embedding-provider-deferred.md)
- [common-language.md](../../../../common-language.md): **Ollama endpoint**, **Ollama and embeddings**, **Embedding model**, **Embedding queue**
- [ui-theme.md](../../../../packages/lexiflow-ui/docs/concepts/ui-theme.md) — onboarding wizard (phase 06) inherits **UI theme** after phase 9-2 baseline
- Phase 10: `Embedder`, `VectorStore`, 384-dim baseline
- Phase 07: `required_artifact_ids`, onboarding LLM setup

## Public interfaces (target)

```python
# lexiflow_core.embed (or llm/ — package layout TBD in PR)
class OllamaEmbedder:
    def __init__(self, *, base_url: str, model: str) -> None: ...
    def embed(self, text: str) -> list[float]: ...

# lexiflow_core.models.requirements
def required_artifact_ids(settings: Settings) -> tuple[str, ...]:
    # When ollama_url and ollama_embeddings_enabled (or implicit): no MiniLM
```

## TDD cycles

### Cycle 10b.1 — OllamaEmbedder returns fixed-dim vector

**Test:** fake HTTP server → `embed("hello")` length matches phase 10 schema (384 unless ADR revision changes dims).

---

### Cycle 10b.2 — Worker selects Ollama embedder when ollama_url set

**Test:** settings with `ollama_url` → embed job uses `OllamaEmbedder`, not MiniLM loader.

---

### Cycle 10b.3 — Provider switch invalidates or re-embeds

**Test:** choose one policy in PR Plan: (A) changing ollama_url clears vectors and enqueues re-embed, or (B) settings change blocked while vectors exist. Document in ADR 0005 follow-up if needed.

---

### Cycle 10b.4 — required_artifact_ids skips MiniLM with Ollama

**Test:** `ollama_url` set → `required_artifact_ids` does not include `embedding-minilm`.

---

### Cycle 10b.5 — Onboarding Ollama path skips embedding download

**Test:** pytest-qt Ollama scenario → no MiniLM download; no HF token section for embeddings; wizard reaches target language.

---

### Cycle 10b.6 — Pin Ollama embed model in manifest

**Test:** lockfile or settings default includes embed model name; mismatch at runtime → clear error.

## Manual verification

- Ollama running with pinned embed model; add text → edit translated → embed job completes; similarity in simplify still works (smoke after phase 11 if 10b merges first, else stub check in 10b).

## PR checklist

- [ ] ADR 0005 consequences implemented; common-language updated
- [ ] Semble/context7 used for Ollama embeddings API
- [ ] No MiniLM import in UI process
- [ ] Phase 11 README **blocked by** includes 10b when issue created

## Deferred out of scope

- User-picked arbitrary Ollama embed models (only pinned default + documented override in settings if needed)
- Embeddings via providers other than HF MiniLM and Ollama
