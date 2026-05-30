# Phase 17: UI cleanup

**Branch:** `phase/17-ui-cleanup`  
**PR title:** `Phase 17: UI cleanup — sidebar tree, language switcher, shell alignment`

## Outcome

Close gaps between **Application shell** / [common-language.md](../../../../common-language.md) and what earlier phases shipped as placeholders. One phase, one PR: work through the **UI cleanup checklist** below (vertical TDD slices per item).

**Blocked by:** phase 09 (reader) — sidebar selection and content area are in place before restructuring navigation.

## Why this phase exists

Phases 05–09 delivered a working loop (add text → jobs → flat sidebar list → reader) but deferred several shell behaviors documented in domain language. Backend pieces (groups, index, `LanguageStore.list_targets()`, `delete_to_trash`) exist; the UI still shows flat lists, read-only labels, and missing affordances. This phase is an explicit **cleanup todo list**, not new domain features.

## UI cleanup checklist

Track each item in the PR Plan. Check off in the PR description as items merge.

| # | Item | Spec / intent | Notes |
|---|------|---------------|--------|
| 1 | **Sidebar group/text tree** | **Navigation modes**: Texts = **sidebar tree** plus reader. **Group** holds **texts**. | Replace flat `QListWidget` titles with group nodes and text leaves from **library index** (`group_display_name`, title). Click text → open reader (same as today). |
| 2 | **Active target language switcher** | **Active target language**: toolbar **switcher** (flag, name, **user language level**). | Replace read-only toolbar label with control over `LanguageStore.list_targets()`; persist `Settings.active_target_language`; refresh sidebar + content scope. |
| 3 | **Add text entry points** | One clear primary action; no duplicate chrome. | Remove toolbar **Add text** button. Keep File menu (⌘N), sidebar button, empty-state button; document in **application-shell**. |
| 4 | **Delete text affordance** | User can remove a **text** from the library. | Wire UI to `TextRepository.delete_to_trash` (moves to **Trash**). Full trash/restore UI remains phase 13; this item is at least delete-from-sidebar or reader with confirm. |
| 5 | **Shell copy and empty states** | Guidance matches current behavior. | e.g. “Select a text in the sidebar” when tree exists; no “reader deferred” / flat-list assumptions. |

Add rows to this table only when a new shell gap is discovered; do not mix unrelated features (jobs panel, search, vocabulary) into this phase.

## References

- [common-language.md](../../../../common-language.md): **Navigation modes**, **Group**, **Active target language**, **Application shell**, **Trash**
- [application-shell.md](../../../../packages/lexiflow-ui/docs/concepts/application-shell.md)
- Phase 03 **library index** (group + title columns)
- Phase 06 **LanguageStore** / target languages
- Phase 13 defers full **Trash** settings UX (item 4 may stay minimal until then)

## TDD cycles (suggested order)

Implement one checklist row at a time: one test → minimal UI → refactor.

### Cycle 17.1 — Sidebar shows groups with nested texts

**Test:** pytest-qt — two groups, two texts → tree has group nodes; clicking text opens reader.

---

### Cycle 17.2 — Switch active target language refreshes sidebar

**Test:** two targets in `LanguageStore` → switcher changes ISO → sidebar lists only that language’s texts.

---

### Cycle 17.3 — Delete text removes from index and sidebar

**Test:** delete action → text gone from tree; folder under `.trash/{id}` (core behavior already tested; assert via UI flow).

---

## Manual verification

- Tree expand/collapse; select text in each group; switch language and confirm library scope.
- Add text still works from sidebar / menu after tree lands.

## PR checklist

- [ ] Every completed checklist row cited in PR Plan
- [ ] [application-shell.md](../../../../packages/lexiflow-ui/docs/concepts/application-shell.md) updated; deferred shell items removed or moved here
- [ ] No new domain terms in `CONTEXT.md` (use **common-language** only)
- [ ] Semble + Context7 noted in PR Plan (Qt tree widget APIs)

## Out of scope

- **Global search**, full **Trash** settings, **properties panel**, drag-between-groups (phases 13–14)
- **Vocabulary** UI, **jobs panel**, onboarding changes
- New core storage or index schema unless required for tree performance
