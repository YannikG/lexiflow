# Onboarding flow

First-run setup before the **application shell** is shown.

## Gate

`lexiflow_ui.app.run()` loads **global settings**. When `onboarding_complete` is false, `OnboardingWizard` runs modally. Cancel exits without opening the main window. Finish runs language setup, then sets `onboarding_complete` true.

## Wizard pages

1. **Welcome** — Intro copy; RAM warning when system memory is below 8 GiB (user may continue).
2. **Native language** — Searchable **language catalog** picker.
3. **LLM mode** — Built-in llama-server (default) or Ollama (advanced).
4. **LLM configuration** — Form for the chosen mode:
   - **Native**: llama-server readiness note, link to pinned LLM on Hugging Face, optional HF token.
   - **Ollama**: URL + detect; optional HF token for embeddings.
5. **Target language** — Catalog picker plus CEFR level combo for **user language level**.

There is no model download step. LLM and embedding weights load from Hugging Face when first needed.

## Completion

`complete_language_onboarding()` adds the first target language and enqueues `DOWNLOAD_SPACY`. `finalize_onboarding()` sets `onboarding_complete` after all wizard steps succeed.

## Testability

`SystemInfo` supplies RAM for the welcome page. `OllamaProbe` is injectable. `run_onboarding_if_needed()` accepts a custom wizard factory for pytest-qt.

See [common-language.md](../../../../common-language.md): **Onboarding flow**, **Onboarding LLM setup**, **System requirements**.
