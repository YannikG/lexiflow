# Onboarding flow

First-run setup before the **application shell** is shown.

## Gate

`lexiflow_ui.app.run()` loads **global settings**. When `onboarding_complete` is false, `OnboardingWizard` runs modally. Cancel exits without opening the main window. Finish runs language setup, then sets `onboarding_complete` true.

## Wizard pages

1. **Welcome** — Intro copy; RAM warning when system memory is below 8 GiB (user may continue).
2. **Native language** — Searchable **language catalog** picker.
3. **LLM mode** — Choose one of: Hugging Face download, Ollama, or manual import (radios only).
4. **LLM configuration** — Form for the chosen mode (opened on Next; wizard height fits that form only):
   - **Hugging Face download**: numbered Gemma license steps, **Open Gemma on Hugging Face** (system browser), optional HF token; continues to bootstrap.
   - **Ollama**: URL + detect; embedding downloads on Next (token optional); skips bootstrap.
   - **Manual import**: two folder pickers with pinned-repo helper text; imports on Next; skips bootstrap.
5. **Model bootstrap** — Hugging Face download path only: downloads pinned LLM and embedding artifacts with progress; on gated-repo failure, same Gemma link plus **Open Gemma** and **Retry download**.
6. **Target language** — Catalog picker plus CEFR level combo for **user language level**.

## Completion

`complete_language_onboarding()` adds the first target language and enqueues `DOWNLOAD_SPACY`. `finalize_onboarding()` sets `onboarding_complete` after all wizard steps succeed.

## Testability

`SystemInfo` supplies RAM for the welcome page. `OllamaProbe`, `ModelStore`, and `FakeModelDownloader` are injectable. `run_onboarding_if_needed()` accepts a custom wizard factory for pytest-qt.

## Phase 9-2 (UI theme migration)

Wizard pages ship in phase 06 on default Fusion chrome. Phase 9-2 restyles onboarding to match the **UI theme** baseline (see [ui-theme.md](ui-theme.md)).

See [common-language.md](../../../../common-language.md): **Onboarding flow**, **Onboarding LLM setup**, **Model bootstrap**, **System requirements**.
