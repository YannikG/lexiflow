# Desktop UI theme strategy (stylesheet on standard widgets)

**Status:** Accepted  
**Date:** 2026-05-30  
**Supersedes:** none  
**Implementation:** [phase 9-2 — UI theme migration](../roadmap/phases/phase-09-2-ui-theme-migration/README.md)

## Context

Phases 05–09 shipped the **application shell** with default PySide6 (Fusion) styling. **Global settings** already store a **Theme** preference (`system`, `light`, `dark`), but no **UI theme** layer applies it. Downstream phases (17, 11–14) will add substantial UI surface; ad-hoc per-widget styling would diverge quickly.

LexiFlow is **Apache 2.0** ([LICENSE](../../LICENSE)). The project is hobby OSS with no commercial distribution plans, but the license should stay permissive so others can fork and use the app freely.

Several third-party Qt theme libraries were evaluated for PySide6.

## Decision

1. **Widget-first** — Keep `QMainWindow` and standard `QWidget` tree from phases 05–09. No QML rewrite. No full **FluentWindow** / frameless shell migration in v1.
2. **Stylesheet-based UI theme** — Map `Settings.theme` to a global Qt stylesheet at app startup via **`lexiflow_ui.theme_stylesheet`** (resolve, apply, and QSS builder). **Implementation (phase 9-2):** Fusion base + bundled **`dark_theme.json`** / **`light_theme.json`** color tokens, not `qt-material`.
3. **Core stays Qt-free** — Theme resolution and apply live in **lexiflow-ui** only. **lexiflow-core** keeps the `Theme` literal on `Settings`; no Qt imports in core.
4. **Phase split** — Phase **9-2** delivers theme bootstrap and migrates the existing shell off default chrome. Phase **14** wires the **Theme** toggle in **settings** and the **appearance** panel (font size already on `Settings`).
5. **Convention** — Feature widgets must not call `setStyleSheet` inline; styling flows from the global **UI theme** (see [ui-theme.md](../../packages/lexiflow-ui/docs/concepts/ui-theme.md)).

## Evaluated alternatives

| Option | License | Verdict |
|--------|---------|---------|
| **PySide6-Fluent-Widgets** (QFluentWidgets) | GPLv3 (commercial license available) | **Rejected** — GPL conflicts with Apache 2.0 when bundled in PyInstaller unless the whole project relicenses to GPL or a commercial Fluent license is purchased. Full component-library migration also touches every shell widget. |
| **qt-material** | BSD-2-Clause | **Rejected after spike** — Permissive, but Material chrome diverged from reader contrast and neutral shell goals. |
| **qt-modern-style** | MIT | **Rejected after spike** — Recorded in spike appendix; not selected for v1. |
| **QtModernRedux6** | Per-package | **Rejected for v1** — Dark-biased; smaller ecosystem; frameless focus overlaps deferred shell work. |
| **Fusion + bundled theme QSS** | Apache (ours) | **Selected (implementation)** — `dark_theme.json` / `light_theme.json` + global QSS; no third-party theme runtime dependency. |
| **QML / Qt Quick Material** | LGPL (Qt) | **Rejected** — Requires rewriting the widget shell; out of scope for v1. |

## Rationale

| Factor | Stylesheet on widgets |
|--------|------------------------|
| **License** | Apache + bundled JSON tokens; no GPL theme runtime. |
| **Migration cost** | Global QSS applies to existing `QPushButton`, `QListWidget`, etc. without replacing class hierarchy. |
| **Settings model** | `Theme` literal already exists; effective light/dark resolved from OS when `system`. |
| **Package boundary** | `theme.py` resolves preference and applies once; `theme_stylesheet.py` owns QSS generation only. |
| **Downstream phases** | Phase 17 tree, phase 13 search overlay, phase 14 settings inherit theme automatically if they use standard widgets. |

## Considered alternatives

- **Relicense LexiFlow to GPLv3 for Fluent widgets:** Maximizes visual polish but reduces fork freedom; rejected for v1.
- **Buy QFluentWidgets commercial license:** Avoids GPL but adds cost and vendor lock-in; rejected for hobby scope.
- **Defer theme to phase 14 only:** Settings UI without bootstrap leaves UI-heavy phases 11–17 and phase 17 shell work building on default Fusion; rejected.

## Consequences

- **Phase 9-2:** ADR + concept doc + `lexiflow_ui.theme_stylesheet` bootstrap; dark/light theme QSS; migrate shell widgets; spike compares Fusion vs themed chrome on macOS (see `docs/spike/phase-9-2/`).
- **Phase 14:** **Theme** dropdown calls `apply_app_theme` without restart when feasible; **appearance** panel for reader font size and future density/accent.
- **Phase 15:** PyInstaller spec bundles `lexiflow_ui/themes/*.json` with the app (no `qt-material` assets).
- **Phase 17+:** New controls use standard Qt widgets; no inline QSS in feature code.
- **Dependency:** No third-party Qt theme package in **lexiflow-ui** for v1 (Fusion + bundled JSON only).

## Open questions (resolved in phase 9-2 implementation)

- **Accent color** — Theme defaults (`#0078D4` dark / `#005FB8` light focus and buttons).
- **Reader pane** — `reader.background` / `editor.foreground` tokens on read panes via global QSS object names; scrollbars in the reader and **new words panel** use `reader.scrollbar*` tokens.
- **Runtime toggle** — Startup apply only in 9-2; phase 14 may re-call `apply_app_theme`.
