# Simplify and word mix

## What this is

**Simplify** is an explicit user action (not part of **staged generation**) that produces a **simplified variant** at a chosen CEFR level. The worker uses vocabulary similarity, **level bucket quotas**, and an LLM with **LLM structured output** validation before any file is written.

## Job payload

| Field | Meaning |
|-------|---------|
| `text_id` | Text to simplify |
| `level` | Target CEFR level (e.g. `A2`) |

Enqueue via `enqueue_simplify` from the UI. Requires an existing **translated variant**.

## Word mix

1. Load translated text vector from **vector storage**.
2. `search_similar_words` against vocabulary embeddings.
3. Join with **vocabulary entries** (level when learned, difficulty rating).
4. Rank by similarity × difficulty weight (**easy** words use weight `0.25`).
5. Fill **level bucket quotas** (~30% at L, ~20% at L−1, ~10% at L+1); remainder from ranked pool or LLM prose.

## Structured output

LLM returns JSON: `title`, `body`, `new_words[]` with `lemma`, `gloss`, `level`. Invalid JSON → job **Failed**, no variant file.

Valid output writes:

- `simplified-{level}.md` with document title H1 (library title unchanged)
- `{variant}.suggestions.json` sidecar for **new words panel**

## Re-simplify

Running simplify again at the same level overwrites that variant file only; other simplified levels are untouched.

## Vocabulary slice (phase 11)

Minimal **vocabulary entries** table supports bucket selection, suggestion filtering, and one-click add from the reader. Full Study/Browse/export is phase 12.

## Related

- [job-queue.md](job-queue.md)
- [embeddings-and-vector-storage.md](embeddings-and-vector-storage.md)
- Phase 11 README in `docs/roadmap/phases/phase-11-simplify/`
