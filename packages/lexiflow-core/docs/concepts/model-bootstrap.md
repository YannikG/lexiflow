# Model bootstrap and pinning

LexiFlow ships a pinned **models.lock** manifest and downloads artifacts from Hugging Face on first use.

## Pinning

`models.lock` lists each artifact with a stable `id`, Hugging Face `repo`, and full commit `revision`. The app never pins floating “latest” tags in v1. Revisions in `models.lock` must be full commit SHAs from the Hugging Face Hub. spaCy packs are pinned when the job handler lands (phase N+1), not in v1 bootstrap.

`load_models_lock()` reads the bundled manifest shipped inside `lexiflow-core`.

## Local cache

Installed artifacts live under `{data_root}/.app/models/{artifact_id}/`. A `revision.txt` marker records the installed revision. `ModelStore.is_installed()` compares that marker to the lock pin.

`ensure_app_layout()` creates `.app/models/`; downloads happen only through `ModelStore.ensure_installed()`.

## Download boundary

`ModelDownloader` is the protocol boundary. Production uses `HuggingFaceModelDownloader` (`snapshot_download` with pinned revision and optional token). Tests and CI use `FakeModelDownloader`, which writes the revision marker without network I/O.

`NetworkError` signals connectivity failures during onboarding; the wizard shows an error and a **Retry** control.

## Onboarding requirements

`required_artifact_ids(settings)` applies product policy:

- **Ollama endpoint** configured: download the **embedding model** (MiniLM) only.
- **Embedded path**: download embedding model and embedded LLM (Gemma).

Ollama replaces the embedded LLM only; embeddings run in-app from Hugging Face until [phase 10b](../../../../docs/roadmap/phases/phase-10b-ollama-embeddings/README.md) ([ADR 0005](../../../../docs/adr/0005-ollama-embedding-provider-deferred.md)).

## Updates

`ModelStore.check_for_updates()` compares installed revision markers to the lock. Settings UI to trigger checks ships in phase 14; the core API is available from phase 07.

## Settings

Optional `huggingface_token` in **global settings** is passed to the downloader for gated repos and rate limits.

See [common-language.md](../../../../common-language.md): **Model bootstrap**, **Model pinning**, **Hugging Face token**, **Bootstrap network retry**, **Ollama and embeddings**.
