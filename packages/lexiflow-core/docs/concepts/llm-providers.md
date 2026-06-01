# LLM providers

LexiFlow routes translate, cleanup, and simplify jobs through a single **LLM provider** protocol. The worker resolves the active provider from **global settings** and installed model artifacts.

## Provider mode

There are exactly two LLM backends:

- **Native llama-server** (default): LexiFlow supervises a local `llama-server` process. The language model is pinned in `models.lock` as `llama_hf_model` and loaded by llama-server from Hugging Face via `-hf`. No torch or transformers in the Python environment.
- **Ollama endpoint** (advanced): when `ollama_url` is set in `settings.toml`, all LLM jobs use `OllamaLLM` (HTTP `POST /api/generate`). LexiFlow does not manage the Ollama process. Users must pull a compatible model locally (see Ollama docs for tags).

**LLM toggle** off (`llm_enabled = false`): `DisabledLLM` fails jobs with a clear message.

**Native path without llama-server binary**: `UnavailableLLM` with install guidance (`llama-server` on PATH or `LEXIFLOW_LLAMA_SERVER_BIN`).

`resolve_llm(settings, data_root)` in `lexiflow_core.llm.resolution` performs selection. It is a query: no queue writes.

## Native llama-server

- Pinned Hugging Face model spec in `models.lock` as **`native-llm`** (`llama_hf_model`, e.g. `repo:quantized-file`).
- LexiFlow does **not** download or cache LLM weights; llama-server fetches them on first use.
- The **UI process** supervises `llama-server` via `LlamaServerSupervisor`; the worker calls `LlamaServerLLM` over HTTP (`/completion`).
- Server starts on first LLM job and stops when the app quits (idle shutdown remains phase 14).
- Not used in CI: tests inject `FakeLLM` or HTTP fakes at protocol boundaries.

## Ollama HTTP client

`OllamaLLM` sends non-streaming generate requests. Errors surface as `OllamaError` and become failed job messages.

## Embeddings

- Pinned repo/revision in `models.lock` as **`embedding-minilm`**.
- The worker loads MiniLM via `sentence-transformers` from Hugging Face on first use; LexiFlow does not cache weights under `.app/models/`.
- Optional `huggingface_token` from settings is passed through for gated repos.
- Without `sentence-transformers` installed, the worker uses `FakeEmbedder` (CI and dev).

## CI and tests

- Tests use `FakeLLM`, HTTP fakes, or `UnavailableLLM` at protocol boundaries.
- No real Ollama, Hugging Face downloads, or llama-server in pytest.

## Worker entry

`lexiflow_worker.main` loads `SettingsStore`, calls `resolve_llm`, and passes the provider to `run_worker_loop`. Production never hardcodes `FakeLLM`.

See [common-language.md](../../../../common-language.md): **LLM provider**, **Provider mode**, **Native LLM**, **Ollama endpoint**, **Native LLM lifecycle**.
