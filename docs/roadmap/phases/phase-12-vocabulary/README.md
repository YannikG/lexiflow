# Phase 12: Vocabulary

**Branch:** `phase/12-vocabulary`  
**PR title:** `Phase 12: Vocabulary CRUD, Study/Browse, highlight-add, export`

## Outcome

- **Vocabulary study** mode: Study (flashcards) and Browse (full list)
- Study: shuffle, reveal, **promote fluency**; hidden when **mastered**
- Browse: edit **difficulty rating**, delete with **delete undo window**
- **Reader add word** from Translated / **simplified variant** tabs
- **Lemma resolution** via spaCy pack or LLM
- **Level when learned** defaults per glossary rules
- **Vocabulary export** and **vocabulary import** with duplicate handling
- **Remove target language** can offer export before wipe

## References

- [common-language.md](../../../../common-language.md): **Vocabulary**, **Vocabulary study**, **Reader add word**, **Vocabulary export**, **Vocabulary import**, **Lemma resolution**, **Level when learned**
- [ui-theme.md](../../../../packages/lexiflow-ui/docs/concepts/ui-theme.md) — Study/Browse modes use standard widgets + **UI theme**

## TDD cycles

### Cycle 12.1 — Add vocabulary entry dedups lemma

**Test:** second add same lemma → error or merge policy documented.

---

### Cycle 12.2 — Promote hard → well after reveal only

**Test:** UI Study — Got it disabled before reveal (pytest-qt).

---

### Cycle 12.3 — Got it hidden at easy

**Test:** easy entry → button not visible.

---

### Cycle 12.4 — Delete undo restores row

**Test:** delete → undo → lemma back within timeout.

---

### Cycle 12.5 — Export zip contains manifest + sqlite

**Test:** export → zip structure valid.

---

### Cycle 12.6 — Import skip duplicate lemma

**Test:** import existing lemma → skipped count.

---

### Cycle 12.7 — Import overwrite replaces translation

**Test:** overwrite flag true → updated.

---

### Cycle 12.8 — Highlight-add enqueues LEMMA job

**Test:** selection → dialog prefilled surface form.

---

### Cycle 12.9 — Level when learned from simplified tab

**Test:** add from B1 context → level B1.

---

## Manual verification

- Full loop: simplify → add word → Study promote.

## PR checklist

- [ ] UI label "Vocabulary" not Wörterbuch
- [ ] Vocab survives text delete
