# Language pack install

spaCy **language packs** install in the UI when the user adds a target language, not via the **background job** queue.

## Coordinator

`lexiflow_ui.spacy_pack_install.install_spacy_pack_with_progress()`:

- Shows a window-modal `QProgressDialog` with a determinate bar and live status lines (same pattern as model downloads in **Settings**).
- Calls `lexiflow_core.languages.spacy_pack.install_spacy_pack()` with optional injected `ensure_model` / `load_model` for tests.
- On `SpacyPackError`, shows `QMessageBox.critical` and returns `False`.
- Skips the dialog when `spacy_pack_available()` is already true.

## Entry points

| Flow | Module |
|------|--------|
| First-run onboarding | `onboarding/wizard.py` — after `complete_language_onboarding()`, before `finalize_onboarding()` |
| Add language | `switch_language_flow.py` — after `add_target_language()`, before `switch_active_target()` |

Both accept an injectable `install_spacy_pack` callable for pytest-qt.

## Rollback

On failure, callers invoke `discard_failed_target()` from `lexiflow_core.languages.setup` so partial language metadata is removed. Onboarding also restores settings saved before `complete_language_onboarding()`.

## Packaging

Install runs in the UI process (same PyInstaller bundle as the worker). spaCy is an optional runtime dependency; without it, the user sees a clear error in the dialog.

See [common-language.md](../../../../common-language.md): **spaCy language packs**, **Background job**.
