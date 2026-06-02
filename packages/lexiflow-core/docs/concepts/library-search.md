# Library search

Full-text search over the **library index** for the **active target language**.

## Public API

```python
from lexiflow_core.library.search import search_texts

hits = search_texts(index, lang="es", query="palabra")
```

Each `SearchHit` includes `text_id`, `title`, matching `variant`, HTML `snippet` with `<mark>` around the match, and optional `match_offset` for reader scroll.

## Matching layers

1. Case-insensitive prefix match via SQLite FTS5 (`text_search` virtual table).
2. If no FTS hits, `rapidfuzz` partial-ratio fallback over titles and variant bodies scoped to the target language.
3. No in-memory result cache; edits re-index through `LibraryIndex.upsert_text`.

## Index maintenance

- Migration `005_fts_search.sql` creates `text_search`.
- `LibraryIndex.upsert_text` indexes all `*.md` files in the text folder.
- `remove_from_index` and trash delete remove FTS rows.
- `rebuild_from_disk` clears and rebuilds FTS alongside metadata rows.

## Consumers

- **Global search UI** inline fields (lexiflow-ui)
- **Find in texts** from vocabulary browse (same `search_texts` function)

See [library-and-text-storage.md](library-and-text-storage.md) for disk layout and trash/backup.
