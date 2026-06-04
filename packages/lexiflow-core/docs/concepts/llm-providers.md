# LLM providers

LexiFlow routes translate, cleanup, and simplify jobs through a single **LLM provider** protocol. The worker resolves the active provider from **global settings** and runtime availability (llama-server binary or Ollama URL).

## Provider mode

There are exactly two LLM backends:

- **Native llama-server** (default): LexiFlow supervises a local `llama-server` process. The language model is pinned in `models.lock` as `llama_hf_model` and loaded by llama-server from Hugging Face via `-hf`. No torch or transformers in the Python environment.
- **Ollama endpoint** (advanced): when `ollama_url` is set in `settings.toml`, all LLM jobs use `OllamaLLM` (HTTP `POST /api/generate`). LexiFlow does not manage the Ollama process. Users must pull a compatible model locally (see Ollama docs for tags).

**Native path without llama-server binary**: `UnavailableLLM` with install guidance (`llama-server` on PATH or `LEXIFLOW_LLAMA_SERVER_BIN`).

`resolve_llm(settings)` in `lexiflow_core.llm.resolution` performs selection. It is a query: no queue writes.

## Native llama-server

- Pinned Hugging Face model spec in `models.lock` as **`native-llm`** (`llama_hf_model`, e.g. `repo:quantized-file`).
- LexiFlow does **not** download or cache LLM weights; llama-server fetches them on first use.
- The **UI process** supervises `llama-server` via `LlamaServerSupervisor`; the worker calls `LlamaServerLLM` over HTTP (`/v1/chat/completions`).
- Server starts on first LLM job and stops when the app quits (idle shutdown remains phase 14).
- Not used in CI: tests inject `FakeLLM` or HTTP fakes at protocol boundaries.

## Ollama HTTP client

`OllamaLLM` sends non-streaming generate requests. Errors surface as `OllamaError` and become failed job messages.

## Embeddings

- Pinned `llama_hf_model` in `models.lock` as **`native-embedding`** (384-d GGUF, same vector contract as phase 10).
- The **UI** supervises a second `llama-server` with `--embedding` on `llama_embed_server_url` (default port 8081).
- The worker calls `LlamaServerEmbedder` over HTTP (`/v1/embeddings`) when the embed server is healthy.
- Optional `huggingface_token` from settings is passed to llama-server for gated repos.
- When **Ollama endpoint** is set, embeddings still use `FakeEmbedder` until phase 10b (`OllamaEmbedder`).
- CI and dev without a running embed server use `FakeEmbedder`.

## CI and tests

- Tests use `FakeLLM`, HTTP fakes, or `UnavailableLLM` at protocol boundaries.
- No real Ollama, Hugging Face downloads, or llama-server in pytest.

## Worker entry

`resolve_embedder(settings)` in `lexiflow_core.embeddings.resolution` mirrors LLM selection.

`lexiflow_worker.main` loads `SettingsStore`, calls `resolve_llm` and `resolve_embedder`, and passes both to `run_worker_loop`. Production never hardcodes `FakeLLM` or `FakeEmbedder` when servers are healthy.

See [common-language.md](../../../../common-language.md): **LLM provider**, **Provider mode**, **Native LLM**, **Ollama endpoint**, **Native LLM lifecycle**.
