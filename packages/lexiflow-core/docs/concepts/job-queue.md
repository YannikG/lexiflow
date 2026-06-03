# Job queue

LexiFlow persists background work in `queue.sqlite` under the user library `.app/` folder so jobs survive crashes and clean shutdowns.

## States

| State | Meaning |
|-------|---------|
| Pending | Waiting for the worker |
| Running | Currently executing |
| Completed | Finished successfully; result stored |
| Failed | Error recorded; manual retry only |
| Cancelled | User cancelled while pending or running; terminal |

On startup, **Running** jobs return to **Pending** and are picked up automatically. `run_worker_loop` calls recovery before claiming work so direct callers get the same behaviour as the worker CLI. **Failed** and **Cancelled** jobs are not auto-retried. **Pending** jobs remain pending.

## Job types

| Type | Purpose |
|------|---------|
| `cleanup` | Markdown cleanup (LLM) |
| `translate` | Plain translation (LLM) |
| `simplify` | Simplified variant (LLM); payload `text_id`, `level` |
| `embed` | Embedding generation (translated text or vocabulary lemma) |
| `download_spacy` | spaCy language pack download (enqueued when a target language is added) |
| `lemma` | Lemma, translation, and explanation inference for highlight-add |

LLM job types share the one-at-a-time rule. `download_spacy` installs a spaCy pipeline under `{data_root}/.app/spacy/{iso}/` via the worker (requires spaCy installed in the worker environment).

### Lemma

Payload: `{language_code, surface_form, native_language, context?}`. Result: `{lemma, translation, explanation}`. Used when spaCy is not available for **lemma resolution**. See [vocabulary.md](vocabulary.md).

## One job at a time

Only one LLM job runs globally at a time. Additional requests stay **Pending** until the head job finishes. Claiming refuses a second **Running** job even if multiple worker processes are active.

## Worker process

The **worker process** consumes the queue headlessly. Phase 08 enqueues **cleanup** and **translate** jobs from the add-text flow; the UI spawns the worker via `WorkerSupervisor.ensure_running()`.

`run_worker_loop` dispatches `cleanup`, `translate`, `simplify`, `embed`, and `lemma` jobs to `lexiflow_core.jobs.handlers`. Jobs with a legacy `prompt` payload still use the phase 04 prompt-only path for tests. Other types without handlers are marked **Failed**.

### Simplify

User-triggered only (not staged generation). Payload: `text_id`, `level` (CEFR). Writes `simplified-{level}.md` and a suggestions sidecar. Invalid LLM JSON → **Failed** with no file write. See [simplify-and-word-mix.md](simplify-and-word-mix.md).

### Embed payloads

- `{text_id}` — embed translated variant body
- `{language_code, lemma}` — embed a vocabulary entry after add from **new words panel**

### Staged generation chain

On add-text save, only **cleanup** is enqueued initially. When cleanup completes:

- **Native-route** paste: writes `native.md`, enqueues `translate` (`phase: plain`).
- **Target-route** paste: enqueues `translate` (`phase: ensure_native` with cleaned body), then `plain` after native exists.

Handlers call `JobService.enqueue` for follow-up work; FIFO ordering preserves **one LLM job at a time**.

Job failure is isolated: the worker marks the job **Failed**, logs the error, and continues with the next **Pending** job.

## History retention

At most twenty **Completed** rows are kept. Pruning runs when a job transitions to **Completed**, not during `list_jobs`.

## Retry vs recovery

- **Recovery** (`recover_on_startup`): interrupted **Running** → **Pending** only.
- **Retry** (user action): **Failed** → **Pending**; does not run until the worker claims it.

See ADR-0002 (persistence) and ADR-0003 (UI + worker processes).
