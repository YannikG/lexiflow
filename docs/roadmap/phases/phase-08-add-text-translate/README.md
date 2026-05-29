# Phase 08: Add text and translate

**Branch:** `phase/08-add-text-translate`  
**PR title:** `Phase 08: Add-text dialog, cleanup and translate jobs`

## Outcome

- **Add text dialog** opens empty via **keyboard shortcuts (v1)**; no clipboard read
- **Input tab** and **language auto-detect** route pasted content correctly
- User must pick **group**; optional source URL in **text metadata**
- **Large paste warning** and **duplicate warning** (URL or **content fingerprint**)
- Save runs **staged generation**: **markdown cleanup** → **native variant** → **plain translation**
- User keeps browsing; **jobs panel** shows progress (polished in phase 14)

## References

- [common-language.md](../../../../common-language.md): **Add text flow**, **Staged generation**, **Input tab**, **Language auto-detect**, **Markdown cleanup**, **Plain translation**, **Prompt templates**, **Duplicate warning**, **Large paste warning**
- Phase 04 JobService

## Public interfaces

```python
# lexiflow_core.text_pipeline
class TextPipeline:
    def submit_new_text(self, draft: TextDraft) -> TextId: ...

# lexiflow_core.llm.prompts
def load_prompt(name: str) -> str: ...

# Job handlers in worker
def handle_cleanup(job: JobRecord, llm: LLMProvider, repo: TextRepository) -> None: ...
def handle_translate(job: JobRecord, llm: LLMProvider, repo: TextRepository) -> None: ...
```

## TDD cycles

### Cycle 8.1 — Prompt files load

**Test:** load `cleanup.md` non-empty; missing → PromptNotFoundError.

---

### Cycle 8.2 — FakeLLM cleanup returns JSON/markdown with document title

**Behavior:** cleanup writes **native variant** with **document title** as H1.

**Test:** handler writes `native.md` starting `# Title`.

---

### Cycle 8.3 — Translate creates translated variant

**Behavior:** **plain translation** produces **translated variant** with target-language **document title**.

**Test:** FakeLLM translate fixture → `translated.md` exists.

---

### Cycle 8.4 — Text metadata title = target language title

**Test:** after translate, meta.json title matches translated H1.

---

### Cycle 8.5 — Duplicate source_url warns

**Test:** existing url → DuplicateWarning with existing id.

---

### Cycle 8.6 — 50k paste warn flag

**Test:** draft 60k chars → requires confirm flag on submit.

---

### Cycle 8.7 — Lang detect flips pipeline silently

**Test:** target tab + detect native → routes as native source (mock detector).

---

### Cycle 8.8 — UI dialog no clipboard on open

**Test:** open dialog → text edit empty (pytest-qt).

---

## Manual verification

- Add paste → wait jobs → text appears in **sidebar** with **target-language title**.

## PR checklist

- [ ] Simplify NOT auto-run on save
- [ ] Worker spawned on submit
