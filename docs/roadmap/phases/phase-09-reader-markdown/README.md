# Phase 09: Reader and markdown

**Branch:** `phase/09-reader-markdown`  
**PR title:** `Phase 09: Reader tabs, Qt markdown, edit mode, last tab memory`

## Outcome

- Open text from **sidebar** in **markdown reader**
- **Reader tabs**: Native, Translated, Simplified (flat or menu per **simplified variants** count)
- **Read mode** default; **edit mode** saves variant source without re-translate
- **Last viewed tab** remembered; first open defaults to Translated
- Source URL opens in browser; font size in **settings** → Appearance
- **Document title** rendered once, not duplicated in body

## References

- [common-language.md](../../../../common-language.md): **Reader tabs**, **Read mode**, **Edit mode**, **Last viewed tab**, **Markdown reader**, **Markdown editing**, **Document title**

## TDD cycles

### Cycle 9.1 — Open text defaults Translated tab

**Test:** pytest-qt first open → translated pane visible.

---

### Cycle 9.2 — Remember last tab

**Test:** switch Native, reopen → Native selected (settings or index column).

---

### Cycle 9.3 — Single simplified → flat tab label

**Test:** one `simplified-a2.md` → tab text contains `A2` not dropdown.

---

### Cycle 9.4 — Multiple simplified → dropdown

**Test:** a2 + b1 files → simplified dropdown with 2 items.

---

### Cycle 9.5 — Edit save writes md file

**Test:** edit translated body → file on disk updated.

---

### Cycle 9.6 — Edit does not enqueue translate

**Test:** save edit → no new TRANSLATE job (embed job phase 10).

---

### Cycle 9.7 — Document title rendered not duplicated in body

**Test:** renderer skips duplicate heading if body also starts with h1 (or strip on save).

---

## Manual verification

- Read + edit + reload persists.

## PR checklist

- [ ] No QWebEngineView
- [ ] Read mode default
