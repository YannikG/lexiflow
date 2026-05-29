# Phase 03: Library index and texts

**Branch:** `phase/03-library-and-texts`  
**PR title:** `Phase 03: Text storage, groups, and library index`

## Outcome

- User can manage **groups** and **texts** on disk per **text storage layout**
- **Text metadata** enforced (no level on text; level lives on **simplified variants** only)
- **Library index** powers **sidebar** listing by language and **group**
- **Add text flow** requires choosing a **group** (no inbox default)
- **Rebuild library index** rescans disk after external edits

## References

- [common-language.md](../../../../common-language.md): **Group**, **Text metadata**, **Text storage layout**, **Document title**, **Library index**, **Rebuild library index**
- Phase 02 path helpers

## Public interfaces

```python
# lexiflow_core.library.text_repository
class TextRepository:
    def create_text(self, req: CreateTextRequest) -> TextRecord: ...
    def get_text(self, text_id: UUID) -> TextRecord: ...
    def move_to_group(self, text_id: UUID, group: str) -> None: ...
    def delete_to_trash(self, text_id: UUID) -> None: ...  # stub trash path phase 13

# lexiflow_core.library.group_repository
class GroupRepository:
    def list_groups(self, lang: str) -> list[str]: ...
    def create_group(self, lang: str, name: str) -> None: ...
    def rename_group(self, lang: str, old: str, new: str) -> None: ...
    def delete_if_empty(self, lang: str, name: str) -> None: ...

# lexiflow_core.library.index
class LibraryIndex:
    def upsert_text(self, record: TextRecord) -> None: ...
    def list_by_lang(self, lang: str) -> list[TextRecord]: ...
    def rebuild_from_disk(self, data_root: Path) -> int: ...
```

## TDD cycles

### Cycle 3.1 — Create text writes metadata + folder

**Behavior:** create with title, **group**, lang → folder exists; **text metadata** has UUID + **target-language title**.

**Test:** temp data root; assert files on disk.

**Edge:** **text slug** collision → short-id suffix; invalid group name chars sanitized.

---

### Cycle 3.2 — Document title on native variant

**Behavior:** saving **native variant** (`native.md`) starts with `# {title}\n\n` per **document title** rules.

**Test:** write variant; read back first line.

**Edge:** title with `#` escaped or rejected.

---

### Cycle 3.3 — Index upsert and query

**Behavior:** after create, `list_by_lang("es")` returns text in **library index**.

**Test:** sqlite temp index.

**Edge:** `rebuild_from_disk` after manual meta edit syncs index.

---

### Cycle 3.4 — Move group updates disk + index

**Behavior:** move text `news` → `podcasts` relocates folder and **library index**.

**Test:** assert old path gone, new path exists, index group updated.

---

### Cycle 3.5 — Group delete empty only

**Behavior:** delete non-empty **group** raises `GroupNotEmptyError`.

**Test:** group with text → error; empty → removed.

---

### Cycle 3.6 — Text metadata excludes level

**Behavior:** schema validator rejects `level` key on **text metadata**.

**Test:** load fixture with level → validation error.

---

## Manual verification

- Python REPL or small script creating text under tmp LexiFlow tree.

## PR checklist

- [ ] Cycles 3.1–3.6 pass
- [ ] Trash move stubbed or minimal `.trash/` move documented for phase 13
- [ ] FTS tables **not** required yet (phase 13)
