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

## Deferred (phase 06+)

- **Onboarding flow** gate before main shell (phase 06)
- **Active target language** toolbar switcher (phase 06)
- Sidebar group/text tree, reader, add-text (phase 08+)
- Jobs panel, quit-with-jobs dialog, worker idle lifecycle (phase 14)
