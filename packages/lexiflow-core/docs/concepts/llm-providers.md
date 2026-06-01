# LLM providers

LexiFlow routes translate, cleanup, and simplify jobs through a single **LLM provider** protocol. The worker resolves the active provider from **global settings** and installed model artifacts.

## Provider mode

- **Ollama endpoint** set in `settings.toml`: all LLM jobs use `OllamaLLM` (HTTP `POST /api/generate`). LexiFlow does not manage the Ollama process. Users must pull the pinned model tag (`gemma4:2b` for Gemma 4 E2B) locally.
- **No Ollama URL**: jobs use **Embedded model** Gemma 4 E2B from the official Hub repo `google/gemma-4-E2B-it` when `embedded-gemma` is installed under `{data_root}/.app/models/`.
- **LLM toggle** off (`llm_enabled = false`): `DisabledLLM` fails jobs with a clear message (full settings UX is phase 14).
- **Embedded path without a cached Gemma snapshot**: `UnavailableLLM` fails jobs with bootstrap guidance instead of crashing the worker at startup.

`resolve_llm(settings, data_root)` in `lexiflow_core.llm.resolution` performs selection. It is a query: no queue writes.

## Embedded Gemma 4 E2B

- Pinned in `models.lock` as **`google/gemma-4-E2B-it`** (official Google weights, same repo as the license page).
- Bootstrap downloads the full Hugging Face snapshot via `ModelStore` / `HuggingFaceModelDownloader`.
- Inference runs in a **child Python subprocess** (`python -m lexiflow_core.llm.gemma_inference`) so native ML crashes do not take down the worker ([ADR 0003](../../../../docs/adr/0003-job-execution-architecture.md)). The child loads `transformers` + `torch` against the cached `google/gemma-4-E2B-it` directory.
- Not used in CI: tests inject a fake `GemmaGenerator` at the protocol boundary.

## Ollama HTTP client

`OllamaLLM` sends non-streaming generate requests. Errors surface as `OllamaError` and become failed job messages.

## CI and tests

- Tests use `FakeLLM`, HTTP fakes, or a fake `GemmaGenerator` at protocol boundaries.
- No real Ollama, Hugging Face downloads, or GPU inference in pytest.

## Worker entry

`lexiflow_worker.main` loads `SettingsStore`, calls `resolve_llm`, and passes the provider to `run_worker_loop`. Production never hardcodes `FakeLLM`.

See [common-language.md](../../../../common-language.md): **LLM provider**, **Provider mode**, **Embedded model**, **Ollama endpoint**, **Worker-linked model lifecycle**.
