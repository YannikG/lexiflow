# Add text and staged generation

Phase 08 wires the **add text dialog** to **staged generation** through a headless **text pipeline** and persisted **background jobs**.

## Flow

1. User opens **add text dialog** (shortcut: standard **New**, e.g. Ctrl+N / Cmd+N). Paste field starts **empty**; the app does **not** read the clipboard on open.
2. User picks a **group** (required), optional **source URL**, **input tab** (Native or Target), and pastes content.
3. `TextPipeline.submit_new_text` validates **duplicate warning** and **large paste warning** (50k characters, soft guard).
4. A provisional **text** is created on disk (`Untitled` title, raw body in `native.md`).
5. A `cleanup` job is enqueued; the UI calls `WorkerSupervisor.ensure_running()`.
6. Worker runs **markdown cleanup** → enqueues `translate` (plain translation, or ensure-native then plain for Target-tab paste).
7. **Plain translation** writes `translated.md` and sets **text metadata** / **library index** title to the target-language **document title**.

**Simplify** is not part of this chain.

## Modules

| Module | Role |
|--------|------|
| `lexiflow_core.text_pipeline` | `TextDraft`, validation, routing, enqueue cleanup |
| `lexiflow_core.llm.prompts` | Bundled `cleanup.md` / `translate.md` templates |
| `lexiflow_core.jobs.handlers` | `handle_cleanup`, `handle_translate`, dispatch by `JobType` |
| `lexiflow_ui.dialogs.add_text_dialog` | Modal form |
| `lexiflow_ui.add_text_flow` | Duplicate/large-paste dialogs, pipeline + worker spawn |

## Language routing

**Language auto-detect** uses an optional `LanguageDetector` protocol. When detection conflicts with the **input tab**, routing follows detection silently (`resolve_source_route`).

## Duplicate detection

- Same **source URL** in the active target language (library index query).
- Same **content fingerprint** (normalized paste hash) stored in `meta.json` at create time.

Raises `DuplicateWarning`; UI may retry with `ignore_duplicate=True`.
