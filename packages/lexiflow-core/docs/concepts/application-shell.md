# Application shell

## What this is

The **Application shell** is LexiFlow's main window frame: toolbar, **sidebar**, content area, **status bar**, and **navigation modes**. It is the desktop **Desktop shell** entry point users interact with after onboarding.

## Package boundary

| Package | Role |
|---------|------|
| **lexiflow-ui** | Owns the Application shell (Qt widgets, layout, navigation) |
| **lexiflow-core** | Domain logic only; no UI framework |

Phase 01 does **not** implement the full Application shell. It proves process bootstrap in **lexiflow-ui**: `QApplication` starts, a `MainWindow` titled "LexiFlow" opens with an empty central widget, and the process exits cleanly.

## Phase 01 (foundation)

- **Public API:** `lexiflow_ui.run()` — starts Qt, shows hello window, returns exit code
- **Entry:** `uv run python -m lexiflow_ui`
- **Tests:** pytest-qt smoke (window title, clean quit)

## Deferred (phase 05+)

Full **Application shell** per [common-language.md](../../../../common-language.md): toolbar, **sidebar**, **status bar**, **navigation modes** (Texts / Vocabulary), **single instance**, worker supervision.
