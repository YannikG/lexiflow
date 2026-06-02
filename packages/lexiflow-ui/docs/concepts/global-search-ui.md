# Global search UI

Inline search fields for the **library index** in the **active target language**.

## Entry points

- Toolbar **Search library** field with dropdown results
- `Find` keyboard shortcut (`Ctrl+F` / `Cmd+F`) focuses the toolbar search field

## Behavior

- `LibrarySearchField` runs `search_texts` as the user types.
- Matching hits appear in a popup list under the field (title, variant, snippet).
- Arrow keys move selection; Enter opens the hit; Escape closes the list.
- **Search hit navigation** opens the reader on the matching variant tab and scrolls to the matched text when possible.

## Find in texts

Vocabulary browse context menu **Find in texts** uses the same search function with the entry lemma and navigates to the first hit.

## Library and data

File → **Library and data…** opens trash restore/empty, **library backup** export/restore, and **rebuild library index**. Phase 14 moves these controls into the full **Settings** panel.

See [library-search.md](../../../lexiflow-core/docs/concepts/library-search.md) and [ui-theme.md](ui-theme.md).
