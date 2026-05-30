# Markdown reader

## What this is

The **Markdown reader** is LexiFlow's reading surface for **text variants**: native, translated, and simplified levels. It uses Qt native markdown rendering (`QTextBrowser`), not a web view.

## Reader tabs

- **Native** and **Translated** are always shown when those variants exist on disk.
- **Simplified**: one `simplified-*.md` file → flat tab with level label (e.g. A2). Two or more → **Simplified** menu listing each level.
- **Default tab on open:** **last viewed tab** per text from the library index; first open defaults to **Translated**.

## Read mode and edit mode

- **Document title** in the sidebar and reader header comes from **text metadata**. LLM translate/cleanup sets the initial title; in **edit mode** the user changes it in a dedicated title field (not from markdown H1).
- **Read mode** is default: library title label plus rendered markdown in the reading pane (including any H1 in the file).
- **Edit mode** shows a **title** text field, an optional **source URL** field, markdown source beside a **live preview**, and Save/Cancel beneath the content. Save writes variant markdown, the library title, and source URL via `TextRepository.save_variant_edit`; Cancel discards. Unsaved edits use the shared `lexiflow_ui.unsaved_changes` guard before switching reader tabs, opening another text, leaving Texts mode, or closing the window. Save does not enqueue translate or simplify jobs (re-embedding is phase 10).

## Settings

- **Reader font size** (`Settings.reader_font_size`, default 14) applies to the read and edit panes. Appearance settings UI is phase 14.

## Package boundary

| Package | Role |
|---------|------|
| **lexiflow-ui** | `ReaderWidget`, sidebar open flow, Qt widgets |
| **lexiflow-core** | Tab resolution, markdown display prep, variant I/O, index `last_viewed_tab` |

## Related

- [application-shell.md](application-shell.md) — sidebar selection opens reader
- [library-and-text-storage.md](../../../lexiflow-core/docs/concepts/library-and-text-storage.md) — variant files and index column
