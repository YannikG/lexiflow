# Onboarding flow

First-run setup before the **application shell** is shown.

## Gate

`lexiflow_ui.app.run()` loads **global settings**. When `onboarding_complete` is false, `OnboardingWizard` runs modally. Cancel exits without opening the main window. Finish persists languages and sets `onboarding_complete` true.

Ollama detection and **model bootstrap** are deferred to phase 07; phase 06 covers language setup only.

## Wizard pages

1. **Welcome** — Intro copy; RAM warning when system memory is below 8 GiB (user may continue).
2. **Native language** — Searchable **language catalog** picker.
3. **Target language** — Catalog picker plus CEFR level combo for **user language level**.

## Completion

`complete_onboarding()` in `lexiflow_ui.onboarding.completion` calls core `add_target_with_spacy_download()` then saves settings.

## Testability

`SystemInfo` protocol supplies RAM for the welcome page (injectable in tests). `run_onboarding_if_needed()` accepts a custom wizard factory for pytest-qt.

See [common-language.md](../../../../common-language.md): **Onboarding flow**, **System requirements**, **Native language**, **Target language**.
