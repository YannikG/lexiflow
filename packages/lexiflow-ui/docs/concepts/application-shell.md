# Application shell

## What this is

The **Application shell** is LexiFlow's main window frame: toolbar, **sidebar**, content area, **status bar**, and **navigation modes**. It is the desktop **Desktop shell** entry point users interact with after onboarding.

Implementation: `lexiflow_ui.main_window` package (`window.py` plus mixins for menu, chrome, texts, jobs, navigation, and shell dialogs). Import `MainWindow` from `lexiflow_ui.main_window`.

## Package boundary

| Package | Role |
|---------|------|
| **lexiflow-ui** | Owns the Application shell (Qt widgets, layout, navigation) |
| **lexiflow-core** | Domain logic only; no UI framework |

## Phase 05 (shell)

- **Public API:** `lexiflow_ui.run()` — single-instance guard, bootstrap data root, worker supervisor, main window
- **Main window:** toolbar with **Texts** / **Vocabulary** modes, sidebar chrome (Texts mode), stacked **empty state** views, **status bar** with **Worker status**
- **Navigation modes:** Texts shows sidebar + empty state; Vocabulary shows empty state only
- **Worker:** supervisor created at startup; **offline** until `ensure_running()` (lazy spawn on first AI job wired in later phases)
- **Tests:** pytest-qt for shell layout, single instance, worker supervisor stub

## Phase 06 (onboarding and languages)

- **Onboarding flow** gates `run()` until language setup completes (see `onboarding-flow.md`)
- **Active target language** toolbar display shows flag, name, and **user language level**
- Main window receives `Settings` and `data_root` after onboarding

## Phase 08 (add text)

- **Add text** entry points: Texts menu, sidebar button, empty-state button (Texts mode)
- Sidebar lists target-language titles from the library index; after add-text, the shell re-reads the index on a short timer ladder while jobs may still be running

## Phase 09 (reader)

- Sidebar text selection opens the **Markdown reader** in the content area (see [markdown-reader.md](markdown-reader.md))
- **Reader tabs**, **read mode**, **edit mode**, and **last viewed tab** persistence in the library index

## Phase 09-2 (UI theme migration)

- **UI theme** bootstrap at app startup — see [ui-theme.md](ui-theme.md) and [ADR-0006](../../../../docs/adr/0006-desktop-ui-theme-strategy.md)
- **Theme** from **global settings** applied before the main window (system / light / dark)
- Shell widgets from phases 05–09 migrate off default Fusion chrome; no inline `setStyleSheet` in feature modules

## Phase 12 (vocabulary)

- **Vocabulary** mode shows `VocabularyWidget` (browse table, search, export/import)
- **Study** mode shows `StudyWidget` (flashcard deck)
- Sidebar hidden in Vocabulary mode
- **Options** menu → vocabulary export/import and **Delete language** (optional export-first flow)
- Reader **Add word** on translated/simplified tabs

See [vocabulary-study.md](vocabulary-study.md).

## Phase 13 (search and data)

- **Global search UI** toolbar field — see [global-search-ui.md](global-search-ui.md)
- **Search hit navigation** opens reader on matching variant tab
- Vocabulary browse **Find in texts** uses the same search rules
- **Library** menu → **Switch language…** and **Trash…** (restore and empty, scoped to **active target language**)
- **Options** menu → **library backup** export/restore/replace, **rebuild library index**, vocabulary export/import, and **Delete language**

## Phase 14 (settings and jobs)

- **Jobs panel** (status bar link): queue, success, and failed tabs; retry failed jobs; cancel queue jobs; poll while open
- **Shutdown with active jobs**: wait or quit anyway (see [worker-supervision.md](worker-supervision.md))
- **Library** menu → **Switch language…**; **Delete language…** under **Options** opens switch dialog after wipe
- **Settings** and **About** menu entries (partial: theme, Ollama, HF token, reader font; about version and RAM)

## Deferred (later phases)

- ~~Sidebar group/text tree~~ → [phase 17 UI cleanup](../../../../docs/roadmap/phases/phase-17-ui-cleanup/README.md)
- Drag between groups, text properties panel, in-app updates banner, full settings data root (phase 14 remainder)
