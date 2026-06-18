# UI theme

## What this is

**UI theme** is the visual layer applied to LexiFlow's PySide6 widgets: colors, spacing, and control chrome driven by a global stylesheet. It is distinct from the user's **Theme** preference (`system`, `light`, `dark`) stored in **global settings** — that preference is the input; **UI theme** is the applied result.

See [ADR-0006](../../../../docs/adr/0006-desktop-ui-theme-strategy.md) for the library choice and rejected alternatives.

## Package boundary

| Package | Role |
|---------|------|
| **lexiflow-core** | `Settings.theme` literal only — no Qt |
| **lexiflow-ui** | `theme_stylesheet.py` — resolve **Theme** preference, apply stylesheet, build QSS from bundled color tokens |

## Phase 9-2 (UI theme migration)

- App startup applies **UI theme** from **global settings** before the main window is shown
- Resolves **Theme** = System to OS light or dark
- Primary styling: **dark theme** / **light theme** color tokens, applied as Fusion + global QSS in `lexiflow_ui.theme_stylesheet`
- Token files: `themes/dark_theme.json`, `themes/light_theme.json`
- **UI theme migration** — remove inline `setStyleSheet` from phase 05–09 shell modules (see below); rely on global QSS

### Shell modules in scope (phase 9-2)

Global **UI theme** must cover these without per-widget QSS:

| Area | Modules |
|------|---------|
| Main window | `main_window.py` |
| Sidebar | `sidebar.py`, `empty_state.py` |
| Reader | `reader_widget.py`, `widgets/word_panel.py` |
| Dialogs | `dialogs/add_text_dialog.py`, onboarding pages under `onboarding/` |
| Chrome | `widgets/worker_status.py`, `widgets/active_target_language.py` |

Onboarding ships in phase 06 but is restyled in phase 9-2 so it matches the shell.

### Tab object names (global QSS)

These `objectName` values must stay in sync with `TAB_PUSH_BUTTON_IDS` in `theme_stylesheet.py`:

| Widget | objectName |
|--------|------------|
| Reader native tab | `reader_tab_native` |
| Reader translated tab | `reader_tab_translated` |
| Reader simplified tab | `reader_tab_simplified` |
| Reader simplified menu | `reader_simplified_menu` |
| Add-text native / target | `add_text_tab_native`, `add_text_tab_target` |

## Inline QSS exceptions

No exceptions today. If global QSS cannot style a widget (e.g. reader monospace block), add a row here with rationale and link from the code comment:

| Module | Widget / use | Why global QSS is insufficient |
|--------|----------------|--------------------------------|
| *(none yet)* | | |

## Conventions for later phases

1. **Standard widgets first** — Use `QPushButton`, `QTreeWidget`, `QDialog`, etc. Theme covers them globally.
2. **No inline QSS in feature code** — Do not call `setStyleSheet` on widgets in feature modules. Exceptions require a comment linking to this doc and ADR-0006.
3. **No Fluent component library in v1** — PySide6-Fluent-Widgets rejected (GPL vs Apache). Do not import `qfluentwidgets`.
4. **New panels and overlays** — Build with standard Qt widgets (phase 11 **new words panel**, phase 13 **global search UI**, phase 14 **settings**) so they inherit **UI theme** automatically.
5. **Reader typography** — **Markdown reader** body uses `reader.background` / `editor.foreground` on read panes; scrollbars in the reader and **new words panel** use `reader.scrollbar*` tokens; font size from **appearance** settings (phase 14).

## Phase 14 (settings)

- **Settings** UI exposes **Theme** toggle; changing it reapplies **UI theme** (restart acceptable in v1 if runtime switch is hard)
- **Appearance** panel: reader font size and future density/accent options

## Related docs

- [application-shell.md](application-shell.md)
- [global-settings-and-paths.md](../../../lexiflow-core/docs/concepts/global-settings-and-paths.md) — `Settings.theme` field
