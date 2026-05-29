# Job queue

LexiFlow persists background work in `queue.sqlite` under the user library `.app/` folder so jobs survive crashes and clean shutdowns.

## States

| State | Meaning |
|-------|---------|
| Pending | Waiting for the worker |
| Running | Currently executing |
| Completed | Finished successfully; result stored |
| Failed | Error recorded; manual retry only |
| Cancelled | User cancelled while pending; terminal |

On startup, **Running** jobs return to **Pending** and are picked up automatically. `run_worker_loop` calls recovery before claiming work so direct callers get the same behaviour as the worker CLI. **Failed** and **Cancelled** jobs are not auto-retried. **Pending** jobs remain pending.

## Job types

| Type | Purpose |
|------|---------|
| `cleanup` | Markdown cleanup (LLM) |
| `translate` | Plain translation (LLM) |
| `simplify` | Simplified variant (LLM) |
| `embed` | Embedding generation |
| `download_spacy` | spaCy language pack download (enqueued when a target language is added) |

LLM job types share the one-at-a-time rule. `download_spacy` is persisted in phase 06; worker handling arrives in a later phase.

## One job at a time

Only one LLM job runs globally at a time. Additional requests stay **Pending** until the head job finishes. Claiming refuses a second **Running** job even if multiple worker processes are active.

## Worker process

The **worker process** consumes the queue headlessly. The UI process enqueues work later (phase 14+); phase 04 establishes core persistence and `run_worker_loop` in `lexiflow-core`.

Job failure is isolated: the worker marks the job **Failed**, logs the error, and continues with the next **Pending** job.

## History retention

At most twenty **Completed** rows are kept. Pruning runs when a job transitions to **Completed**, not during `list_jobs`.

## Retry vs recovery

- **Recovery** (`recover_on_startup`): interrupted **Running** → **Pending** only.
- **Retry** (user action): **Failed** → **Pending**; does not run until the worker claims it.

See ADR-0002 (persistence) and ADR-0003 (UI + worker processes).
