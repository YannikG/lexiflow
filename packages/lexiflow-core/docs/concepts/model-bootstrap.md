# Model bootstrap and pinning

LexiFlow ships a pinned **models.lock** manifest. Runtime libraries fetch models from Hugging Face; LexiFlow does not download or cache weights under `{data_root}/.app/models/`.

## Pinning

`models.lock` lists each artifact with a stable `id`, Hugging Face `repo`, and full commit `revision`. The app never pins floating “latest” tags in v1. Revisions in `models.lock` must be full commit SHAs from the Hugging Face Hub.

Native LLM artifacts also carry `llama_hf_model`, passed to `llama-server -hf`.

`load_models_lock()` reads the bundled manifest shipped inside `lexiflow-core`.

## Runtime loading

| Capability | Loader | LexiFlow responsibility |
|------------|--------|-------------------------|
| **LLM (native)** | `llama-server -hf` | Pin spec; supervise process |
| **Embeddings (native)** | `llama-server -hf` + `--embedding` | Pin `native-embedding`; supervise second process; pass HF token |
| **Ollama LLM** | User's Ollama | HTTP client only |

First use may require network access and optional `huggingface_token` in **global settings** for gated repos.

## ModelStore (phase 14)

`ModelStore` remains in core for future update checks and optional manual cache management (phase 14). Onboarding does **not** call `ensure_installed()` in v1 after this change.

## Native inference runtime

On the **native path**, onboarding validates `native_llm_operational()`: `llama-server` on PATH (or `LEXIFLOW_LLAMA_SERVER_BIN`) and a valid `llama_hf_model` pin.

Release bundles ship a pinned llama.cpp prebuilt (`packaging/scripts/fetch_llama_server.py`, overridable via `LLAMA_CPP_RELEASE`). The UI supervises that binary; it loads pinned weights from Hugging Face with `-hf`.

## Settings

Optional `huggingface_token` in **global settings** is passed to Hugging Face clients for gated repos and rate limits.

See [common-language.md](../../../../common-language.md): **Model bootstrap**, **Model pinning**, **Hugging Face token**, **Ollama and embeddings**.
