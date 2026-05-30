# Library and text storage

LexiFlow stores learning texts on disk under the user **data root**. A SQLite **library index** caches metadata for fast **sidebar** listing. Full-text search over variant bodies is added in a later phase.

## Layout

Per target language:

```
{data_root}/{lang}/
  .data/
    groups.json          # group folder slug → display name
  {group_folder_slug}/
    {text_slug}/
      meta.json
      native.md
      translated.md      # later phases
      simplified-a2.md   # later phases
```

Global under the library:

```
{data_root}/.app/index.sqlite   # library index
{data_root}/.trash/             # deleted texts (minimal stub in phase 03)
```

Path helpers live in `lexiflow_core.config.paths`. Filesystem mutations belong in repository modules.

## Groups

- **Group** display name is user-facing (shown in **sidebar**).
- On disk, each group folder uses a **group folder slug** (sanitized from the display label).
- `{lang}/.data/groups.json` maps folder slug → display name.
- `GroupRepository` creates, lists, renames, and deletes empty groups.
- `delete_if_empty` raises `GroupNotEmptyError` when texts remain.

## Texts

- Each **text** has a stable UUID in `meta.json`.
- `meta.json` `group` field stores the group **display name**, not the folder slug.
- **Text slug** folder name comes from title plus a short random suffix; collisions retry.
- **Text metadata** has no `level` field; CEFR level exists only on **simplified variant** files.
- At add-text save, `title` is provisional (`Untitled`) until **plain translation** sets the **target-language title** from the translated variant H1.

## Variants and document title

- **Native variant** (`native.md`) starts with `# {title}\n\n` per **document title** rules.
- **Translated variant** (`translated.md`) is written by the translate job handler; `meta.json` `title` and the library index row are updated to the translated H1.
- `LibraryIndex.find_by_source_url` supports add-text **duplicate warning** by URL. `find_by_content_fingerprint` remains for index storage; add-text duplicate checks use source URL only in v1.
- Titles containing `#` are rejected at write time.
- User edits from the reader call `TextRepository.save_variant_edit`; they update variant markdown and, when the user saves from edit mode, the **library title** from the title field and optional **source URL**. Markdown H1 alone does not retitle the text.

## Library index

- Database: `{data_root}/.app/index.sqlite`.
- Call `ensure_app_layout(data_root)` then `ensure_library_index(data_root)` before constructing `LibraryIndex`, or use `LibraryCoordinator.open(data_root)`.
- `LibraryIndex` is a read-only observer during `rebuild_from_disk`; it never writes `meta.json`.
- The `texts` table caches title, group, languages, variants, and timestamps for fast `list_by_lang` without disk reads.
- `get_by_id` resolves text locations for `TextRepository.get_text`.
- `list_by_lang` returns texts for **sidebar** listing (group display name, title, slug).
- `last_viewed_tab` column stores the per-text **last viewed tab** (Native, Translated, or simplified variant id).
- `rebuild_from_disk` rescans all language folders after external edits; infers missing `groups.json` entries from folder slugs and repairs the registry (does not write `meta.json`).

## Repositories

| Type | Module | Role |
|------|--------|------|
| `LibraryCoordinator` | `lexiflow_core.library.library_coordinator` | Orchestrates storage + index sync |
| `TextStorage` | `lexiflow_core.library.text_storage` | Disk-only text folder CRUD |
| `GroupStorage` | `lexiflow_core.library.group_storage` | Disk-only group registry + folders |
| `TextRepository` | `lexiflow_core.library.text_repository` | Public facade delegating to coordinator |
| `GroupRepository` | `lexiflow_core.library.group_repository` | Public facade delegating to coordinator |
| `LibraryIndex` | `lexiflow_core.library.index` | SQLite metadata cache |

`TextRepository` and `GroupRepository` share one `LibraryCoordinator` per `LibraryIndex` instance.

## Downstream contracts

- Phase 13 adds FTS to **library index** and full **trash** restore UX.
