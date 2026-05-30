# Phase 9-2: UI theme migration

**Branch:** `phase/09-2-ui-theme-migration`  
**PR title:** `Phase 9-2: UI theme migration — strategy and shell bootstrap`  
**ADR:** [0006 — Desktop UI theme strategy](../../../adr/0006-desktop-ui-theme-strategy.md)

**Blocked by:** [phase 09 — Reader and markdown](../phase-09-reader-markdown/README.md)  
**Blocks:** [phase 17 — UI cleanup](../phase-17-ui-cleanup/README.md) (themed baseline before shell restructuring)

Mid-roadmap insert (like [phase 10b](../phase-10b-ollama-embeddings/README.md)). Phases 10–17 numbers are unchanged. Phase 10 (embeddings) is **not** blocked by 9-2; only phase 17 is.

## Why this phase exists

Phases 05–09 delivered a working loop on **default PySide6 (Fusion) chrome**. Before phase 17 shell cleanup and UI-heavy phases 11–14, we need a documented **UI theme** strategy and a migration path so new screens do not accumulate ad-hoc styling.

## Outcome

- **UI theme** strategy recorded in [ADR-0006](../../../adr/0006-desktop-ui-theme-strategy.md)
- **Theme** preference from **global settings** drives applied stylesheet at app startup (system / light / dark)
- Existing **application shell** widgets (toolbar, sidebar, reader, dialogs, empty states) inherit **UI theme** without per-widget `setStyleSheet`
- [ui-theme.md](../../../../packages/lexiflow-ui/docs/concepts/ui-theme.md) documents conventions for later phases

## Scope in / out

| In | Out |
|----|-----|
| ADR-0006, concept doc, roadmap cascade, glossary | Full restyle of every future screen |
| Theme bootstrap API + wire into `run()` (impl PR) | **Settings** appearance panel (phase 14) |
| Migrate phase 05–09 shell widgets (impl PR) | Sidebar group tree (phase 17) |
| Manual theme spike (screenshots for PR Plan) | Reader typography beyond theme inheritance |
| | Runtime **Theme** toggle without restart (phase 14 unless easy in 9-2) |

## References

- [ADR-0006](../../../adr/0006-desktop-ui-theme-strategy.md)
- [common-language.md](../../../../common-language.md): **Theme**, **UI theme**, **UI theme migration**, **Appearance**, **Application shell**, **Global settings**
- [ui-theme.md](../../../../packages/lexiflow-ui/docs/concepts/ui-theme.md)
- [application-shell.md](../../../../packages/lexiflow-ui/docs/concepts/application-shell.md)

## Public interfaces

Implementation PR only — no code in the spec PR.

```python
# lexiflow_ui.theme
def apply_app_theme(app: QApplication, *, theme: Theme) -> None: ...
def resolve_effective_theme(theme: Theme) -> Literal["light", "dark"]: ...
```

## Manual spike (before implementation PR)

Run three short PySide6 demos on macOS:

1. `qt-material` — dark and light themes
2. `qt-modern-style` — default light
3. Plain Fusion — current baseline

Capture screenshots; attach to PR Plan. If Material feels wrong on macOS, ADR allows **qt-modern-style** (MIT) as fallback before adding the dependency.

## TDD cycles

Vertical slices — one test → minimal code → refactor. Spec PR delivers cycles as documentation; implementation PR executes them.

### Cycle 9-2.1 — Dark theme at startup

**Behavior:** When **global settings** have **Theme** = Dark, app launches with dark **UI theme** (not default Fusion).

**Test:** pytest-qt — launch with dark settings → styled control palette differs from unthemed Fusion baseline.

---

### Cycle 9-2.2 — System theme follows OS

**Behavior:** **Theme** = System resolves to light or dark from OS preference.

**Test:** mock OS dark → effective dark stylesheet applied.

---

### Cycle 9-2.3 — Shell widgets inherit theme

**Behavior:** **Main window**, **sidebar**, and reader chrome need no inline QSS.

**Test:** pytest-qt — `MainWindow` visible with themed settings → smoke pass; no crash.

---

### Cycle 9-2.4 — Single bootstrap in `run()`

**Behavior:** **UI theme** applied once from `lexiflow_ui.run()` before `MainWindow` is constructed.

**Test:** unit test on call order / single apply.

---

### Cycle 9-2.5 — No inline QSS in shell widgets

**Behavior:** Phase 05–09 shell modules rely on global **UI theme** only.

**Test:** review checklist or grep guard — no `setStyleSheet` in `main_window`, `sidebar`, `reader_widget`, `empty_state`, add-text/onboarding dialogs except documented exceptions in [ui-theme.md](../../../../packages/lexiflow-ui/docs/concepts/ui-theme.md).

---

## Manual verification

1. Launch app — light, dark, and system themes look coherent on macOS
2. Sidebar, toolbar, reader tabs, add-text dialog visually consistent
3. Second instance dialog and onboarding wizard inherit theme

## PR checklist

- [ ] ADR-0006 and concept doc merged (spec PR) or included (single PR)
- [ ] Roadmap and downstream phase READMEs reference **UI theme** conventions
- [ ] **Plan posted** per [pr-plan-template.md](../../../guides/pr-plan-template.md)
- [ ] Semble + Context7 noted in PR Plan (impl PR: `qt-material` API)
- [ ] No Qt imports added to **lexiflow-core**
- [ ] Rejected QFluentWidgets path documented in ADR (GPL vs Apache)
