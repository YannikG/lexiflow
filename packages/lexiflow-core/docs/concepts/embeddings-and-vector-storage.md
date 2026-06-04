# Embeddings and vector storage

## What this is

LexiFlow stores **384-dimensional** embeddings for translated text and vocabulary lemmas in per-target-language SQLite databases with the **sqlite-vec** extension. Embedding runs in the **worker process**; the UI only enqueues jobs.

## On disk

Under `{data_root}/{language}/.data/`:

| File | Contents |
|------|----------|
| `text_vectors.sqlite` | One vector per text (translated markdown body) |
| `vocabulary.sqlite` | Vocabulary entries table + word embedding vectors |

Both use WAL journaling and schema migrations like other LexiFlow databases.

## Vector extension

LexiFlow depends on **sqlite-vec** (declared in `lexiflow-core`). Release builds use a vendored copy under `packaging/vendor/sqlite_vec/` with per-platform `vec0` loadables fetched or built in CI. Windows ARM64 compiles the extension from upstream sources until PyPI ships a `win_arm64` wheel. Operators do not configure a separate `.so` / `.dll` path.

Before any vector database is opened, core calls `load_sqlite_vec(connection)`, which registers sqlite-vec on that SQLite connection. Migrations then create `vec0` virtual tables for 384-float embeddings.

## Embed queue

Background **EMBED** jobs run when:

- Plain **translate** completes and writes the translated variant
- The user saves edits on the **Translated** reader tab
- The user adds a word from the **new words panel**

Native and simplified edits do not enqueue embed jobs in v1.

## Public surface (lexiflow-core)

- `Embedder` protocol — `embed(text) -> list[float]`
- `FakeEmbedder` — deterministic vectors for tests and manual worker runs
- `LlamaServerEmbedder` — native path HTTP client for `/v1/embeddings` (not used in CI)
- `VectorStore` — upsert/query text and word vectors; `search_similar_words` for simplify **word mix**
- `VocabularyStore` — entries CRUD, Study/Browse, export/import (see [vocabulary.md](vocabulary.md))
- `enqueue_translated_text_embed` / `enqueue_vocabulary_word_embed` — commands to queue embed jobs

## Native embedding server

On the native path (no **Ollama endpoint**), the UI supervises a second `llama-server` instance on `llama_embed_server_url` (default `http://127.0.0.1:8081`) with `--embedding` and the pinned `native-embedding` GGUF. The worker uses `LlamaServerEmbedder` when that server is healthy.

Upgrading from an older build that stored vectors from in-process MiniLM may change similarity semantics; LexiFlow does not auto re-embed existing libraries.

## Testing

CI uses `FakeEmbedder` only. No Hugging Face downloads or torch in PR tests.

## Related

- [ADR 0005](../../../../docs/adr/0005-ollama-embedding-provider-deferred.md) — Ollama embeddings deferred to phase 10b
- [ADR 0007](../../../../docs/adr/0007-native-llama-server-llm.md) — native LLM and embeddings via llama-server
- [job-queue.md](job-queue.md) — persistent queue and worker consumption
- [simplify-and-word-mix.md](simplify-and-word-mix.md) — simplify job and word vectors
- [markdown-reader.md](../../../lexiflow-ui/docs/concepts/markdown-reader.md) — translated edit and new words panel
