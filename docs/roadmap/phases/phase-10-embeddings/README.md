# Phase 10: Embeddings and sqlite-vec

**Branch:** `phase/10-embeddings`  
**PR title:** `Phase 10: Per-language vector DBs, embed queue, FakeEmbedder`

## Outcome

- Per-language **vocabulary database** and **text vector database** with **vector storage**
- **Embedding queue** runs when **translated variant** is saved or edited
- Background embed **jobs** in worker; UI stays responsive
- Similarity queries ready for **simplify word mix** (phase 11)

## References

- [common-language.md](../../../../common-language.md): **Embedding model**, **Vector storage**, **Embedding queue**, **Vocabulary database**, **Text vector database**

## Public interfaces

```python
class Embedder(Protocol):
    def embed(self, text: str) -> list[float]: ...

class VectorStore:
    def upsert_text_vector(self, text_id: UUID, vec: list[float]) -> None: ...
    def upsert_word_vector(self, lemma: str, vec: list[float]) -> None: ...
    def search_similar_words(self, vec: list[float], *, limit: int) -> list[WordHit]: ...
```

## TDD cycles

### Cycle 10.1 — Load sqlite-vec extension

**Test:** in-memory db; CREATE VIRTUAL TABLE vec0... succeeds.

---

### Cycle 10.2 — Upsert and fetch text vector

**Test:** upsert → search by id returns same vector dims (384).

---

### Cycle 10.3 — Embed job runs on translated update

**Test:** edit translated → EMBED job completed; row in text_vectors.

---

### Cycle 10.4 — FakeEmbedder deterministic

**Test:** same input → same vector (for stable tests).

---

### Cycle 10.5 — WAL on per-lang dbs

**Test:** pragma wal on vocabulary.sqlite connection.

---

## Deferred

**Ollama embeddings** are out of scope for this phase. See [ADR 0005](../../../adr/0005-ollama-embedding-provider-deferred.md) and [phase 10b](../phase-10b-ollama-embeddings/README.md).

## Manual verification

- Optional: real MiniLM locally outside CI.

## PR checklist

- [ ] sqlite-vec bundled or loaded with documented path
- [ ] No embed in UI process
