# Phase 06: Onboarding and languages

**Branch:** `phase/06-onboarding-languages`  
**PR title:** `Phase 06: Onboarding wizard, language catalog, target language setup`

## Outcome

- **Onboarding flow** blocks main UI until first-run setup completes
- User sets **native language**, then adds first **target language** with **user language level**
- **Language catalog** searchable; Ukrainian included, Russian excluded
- **Language metadata** stores level per target language
- **Active target language** shown in toolbar (flag, name, level)
- Adding target language enqueues **spaCy language packs** download
- **Remove target language** offers export first (full export in phase 12)

## References

- [common-language.md](../../../../common-language.md): **Onboarding flow**, **Language catalog**, **User language level**, **Remove target language**, **Language metadata**

## Public interfaces

```python
# lexiflow_core.languages.catalog
def list_languages() -> list[LanguageInfo]: ...
def get_language(iso: str) -> LanguageInfo: ...

# lexiflow_core.languages.store
class LanguageStore:
    def add_target(self, iso: str, level: CEFRLevel) -> None: ...
    def get_user_level(self, iso: str) -> CEFRLevel: ...
    def list_targets(self) -> list[str]: ...
```

## TDD cycles

### Cycle 6.1 — Catalog contains uk not ru

**Test:** `get_language("uk")` ok; `"ru"` not in list.

---

### Cycle 6.2 — Add target writes language.json

**Test:** add es A2 → file contains level A2.

---

### Cycle 6.3 — Onboarding flag blocks main window

**Test:** onboarding_complete false → wizard shown (pytest-qt).

---

### Cycle 6.4 — Completing onboarding sets flag

**Test:** finish wizard → settings onboarding_complete true.

---

### Cycle 6.5 — RAM warn below threshold

**Test:** mock RAM 4GB → warning label visible; can continue.

---

### Cycle 6.6 — Toolbar shows active lang + level

**Test:** switcher text contains `A2` after setup.

---

### Cycle 6.7 — spaCy pack download enqueued on add lang

**Test:** add lang → job type DOWNLOAD_SPACY enqueued (stub handler ok).

---

## Manual verification

- Walk wizard in dev build.

## PR checklist

- [ ] English-only UI strings
- [ ] Ollama detect UI present (probe localhost:11434)
