# Global search UI

Inline search fields for the **library index** in the **active target language**.

## Entry points

- Toolbar **Search library** field with dropdown results
- `Find` keyboard shortcut (`Ctrl+F` / `Cmd+F`) focuses the toolbar search field with a fresh query

## Behavior

- `LibrarySearchField` runs `search_texts` as the user types (debounced by 150ms).
- `Find` clears any previous query before focus.
- Matching hits appear in a popup list under the field (title, variant, snippet).
- Arrow keys move selection; Enter opens the hit; Escape closes the list.
- **Search hit navigation** opens the reader on the matching variant tab and scrolls to the matched text when possible.

## Find in texts

Vocabulary browse context menu **Find in texts** uses the same search function with the entry lemma and navigates to the first hit.

## Library data

- **Library** → **Trash…** opens trash restore and empty in **Texts** and **Vocabulary** tabs for the **active target language**
- **Options** → export/restore/replace **library backup** and **rebuild library index**
- Vocabulary menu → **Export vocabulary…** and **Import vocabulary…**

Phase 14 moves backup and index controls into the full **Settings** panel.

See [library-search.md](../../../lexiflow-core/docs/concepts/library-search.md) and [ui-theme.md](ui-theme.md).
