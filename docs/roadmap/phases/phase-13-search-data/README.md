# Phase 13: Search and data management

**Branch:** `phase/13-search-data`  
**PR title:** `Phase 13: Global search overlay, trash, library backup`

## Outcome

- **Library index** full-text search across all **variants**, scoped to **active target language**
- **Global search UI** overlay from toolbar and **sidebar**; fresh query each open; **search hit navigation**
- **Find in texts** and vocabulary search share same matching rules
- **Trash** for deleted texts; restore and empty trash
- **Library backup** export; restore to new **data root** or replace with **strong confirmation**
- **Rebuild library index** in **settings**
- Nice-to-have: **external markdown import** via single file drop

## References

- [common-language.md](../../../../common-language.md): **Library index**, **Global search UI**, **Search hit navigation**, **Find in texts**, **Trash**, **Library backup**, **Rebuild library index**

## TDD cycles

### Cycle 13.1 — FTS indexes variant bodies

**Test:** search keyword in native.md body → hit.

---

### Cycle 13.2 — Language scope filters results

**Test:** es + de texts; search scoped es → only es.

---

### Cycle 13.3 — Fuzzy fallback when zero hits

**Test:** typo query → still match via rapidfuzz layer.

---

### Cycle 13.4 — Snippet highlights match

**Test:** result snippet contains `<mark>` or offset for UI.

---

### Cycle 13.5 — Delete moves to trash not rm

**Test:** delete text → exists under `.trash/`; gone from index.

---

### Cycle 13.6 — Restore re-indexes

**Test:** restore → back in list_by_lang.

---

### Cycle 13.7 — Export zip roundtrip

**Test:** export → extract to new root → rebuild index finds texts.

---

### Cycle 13.8 — No search result cache

**Test:** search twice after edit → second includes new content (integration).

---

## Manual verification

- Ctrl+F overlay keyboard nav.

## PR checklist

- [ ] Open hit navigates reader to text + tab variant if stored (**search hit navigation**)
- [ ] Vocabulary never deleted with text
