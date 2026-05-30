# Application shell

## What this is

The **Application shell** is LexiFlow's main window frame: toolbar, **sidebar**, content area, **status bar**, and **navigation modes**. It is the desktop **Desktop shell** entry point users interact with after onboarding.

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

- **Add text** entry points: File menu, toolbar button, sidebar button, empty-state button (Texts mode)
- Sidebar lists target-language titles from the library index; after add-text, the shell re-reads the index on a short timer ladder while jobs may still be running
- Reader view deferred to phase 09

## Deferred (later phases)

- Sidebar group/text tree, reader
- Jobs panel, quit-with-jobs dialog, worker idle lifecycle (phase 14)
