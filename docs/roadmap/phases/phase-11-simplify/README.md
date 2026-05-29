# Phase 11: Simplify and new words

**Branch:** `phase/11-simplify`  
**PR title:** `Phase 11: Level simplify, vocabulary buckets, new word suggestions`

## Outcome

- User runs simplify with **simplify level picker** (default **user language level**)
- Produces **simplified variant** with target-language **document title**
- **Simplify word mix** uses **level bucket quotas** and vocabulary similarity (easy words deprioritized)
- **LLM structured output** validated before save
- **New word suggestions** post-filtered; shown in **new words panel** for one-click add to **Vocabulary**
- **Re-simplify** replaces only the active level's **simplified variant**
- Multiple **simplified variants** per text can coexist

## References

- [common-language.md](../../../../common-language.md): **Simplify word mix**, **Level bucket quotas**, **New word suggestions**, **New words panel**, **LLM structured output**, **Simplified variants**, **Re-simplify**
- Phase 10 VectorStore

## TDD cycles

### Cycle 11.1 — JSON schema validation rejects bad LLM output

**Test:** invalid JSON → job failed, no file write.

---

### Cycle 11.2 — Simplify writes simplified variant

**Behavior:** creates **simplified variant** with **document title**.

**Test:** FakeLLM fixture → `simplified-a2.md` exists with H1.

---

### Cycle 11.3 — Bucket selection prefers hard over easy at same similarity

**Test:** word retrieval scoring with easy weight 0.25.

---

### Cycle 11.4 — New words filtered if lemma exists

**Test:** suggest `correr`, vocab has `correr` → not shown.

---

### Cycle 11.5 — Multiple levels coexist

**Test:** simplify A2 then B1 → both files exist.

---

### Cycle 11.6 — Re-simplify replaces only that level file

**Test:** mtime/content change only `simplified-a2.md`.

---

### Cycle 11.7 — easy word still picked if only fit

**Test:** only easy word in top semantic match → included in prompt list.

---

## Manual verification

- Simplify with FakeLLM in dev; **new words panel** shows words.

## PR checklist

- [ ] Not auto-run on text save
- [ ] Prompt in `prompts/simplify.md`
