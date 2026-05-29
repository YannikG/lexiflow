# Job execution architecture (UI process + worker process)

LexiFlow runs as **two processes** from one install: a **UI process** (PySide6 only, no LLM/native imports) and a **worker process** (queue consumer, LLM subprocess, embeddings). Jobs persist in `queue.sqlite`; processes coordinate via sqlite plus Qt local socket events. One installer launches both. If the worker crashes, the UI stays open and offers **Restart worker**; queue state is preserved.

**Considered:** single-process QThread consumer (simpler but UI and worker share fate on native bugs); Huey/Celery (wrong fit); two unrelated executables (unnecessary packaging split).

**Consequences:** `lexiflow-core` owns `JobService` and queue schema; `lexiflow-ui` spawns and supervises worker lifecycle; LLM inference stays in a subprocess inside the worker for llama.cpp crash isolation; CI tests core queue headless and UI worker supervision with fakes.

**Worker lifecycle on UI exit:** Wait → worker drains per quit dialog then exits with UI. Quit anyway → worker killed immediately; running jobs become pending.

**Worker idle shutdown:** Worker spawns lazily on first AI job. After ~5 min with no running or queued jobs, worker exits and unloads embedded LLM + MiniLM (same idle window as model sleep). Next job respawns worker.

**Phase 05 stub:** `lexiflow-ui` introduces `WorkerSupervisor` and **Worker status** in the **status bar** (offline until spawned). The supervisor can spawn the worker via `ensure_running()`; the shell does not auto-spawn at startup. Job enqueue from the UI and lazy spawn on first AI job are wired in later phases; idle shutdown, crash restart, and quit-with-jobs dialog remain phase 14.
