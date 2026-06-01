# Embeddings and vector storage

## What this is

LexiFlow stores **384-dimensional** embeddings for translated text and vocabulary lemmas in per-target-language SQLite databases with the **sqlite-vec** extension. Embedding runs in the **worker process**; the UI only enqueues jobs.

## On disk

Under `{data_root}/{language}/.data/`:

| File | Contents |
|------|----------|
| `text_vectors.sqlite` | One vector per text (translated markdown body) |
| `vocabulary.sqlite` | Word vectors for similarity search (vocabulary CRUD is phase 12) |

Both use WAL journaling and schema migrations like other LexiFlow databases.

## sqlite-vec loading

The **sqlite-vec** Python package ships platform wheels (`sqlite-vec>=0.1.6` in `lexiflow-core`). At runtime, `lexiflow_core.vectors.sqlite_vec.load_sqlite_vec(connection)` calls `sqlite_vec.load(connection)` to register the extension on an open SQLite connection before creating `vec0` virtual tables. No separate extension file path is configured; the wheel bundles the native library for each supported OS.

## Embed queue

Background **EMBED** jobs run when:

- Plain **translate** completes and writes the translated variant
- The user saves edits on the **Translated** reader tab

Native and simplified edits do not enqueue embed jobs in v1.

## Public surface (lexiflow-core)

- `Embedder` protocol — `embed(text) -> list[float]`
- `FakeEmbedder` — deterministic vectors for tests and manual worker runs
- `MiniLMEmbedder` — real MiniLM from the local model cache (manual verification; not CI)
- `VectorStore` — upsert/query text and word vectors; `search_similar_words` for phase 11 simplify
- `enqueue_translated_text_embed` — command to queue an embed job

## Testing

CI uses `FakeEmbedder` only. No Hugging Face downloads or torch in PR tests.

## Related

- [ADR 0005](../../../../docs/adr/0005-ollama-embedding-provider-deferred.md) — Ollama embeddings deferred to phase 10b
- [job-queue.md](job-queue.md) — persistent queue and worker consumption
- [markdown-reader.md](../../../lexiflow-ui/docs/concepts/markdown-reader.md) — translated edit enqueue from UI
