# Worker supervision

## What this is

The UI process spawns and supervises a separate **worker process** that consumes the persistent **job queue**. **Worker status** in the **status bar** reflects supervisor state.

## Process model

- Dev and CI: `python -m lexiflow_worker --data-root <path>`
- Release: same PyInstaller bundle, worker entry module (phase 15)
- UI package has no LLM or heavy ML imports

## Worker states (phase 05)

| State | Meaning |
|-------|---------|
| **offline** | No worker process spawned |
| **idle** | Worker process running (stub: no IPC yet) |

Phase 14 adds **running** job counts on the status bar, **crash restart** prompt, and **idle shutdown** after a timeout when the queue is empty (ADR-0003).

## API

`WorkerSupervisor` in **lexiflow-ui**:

- `ensure_running()` — spawn worker once if offline
- `shutdown(wait=…)` — stop worker on app quit
- `state` — current `WorkerState`

Phase 05 does not auto-spawn at startup; lazy spawn on first AI job is wired when the UI enqueues jobs.

## Phase 14

- `WorkerSupervisor` stops the worker after idle timeout when no pending or running jobs remain
- Unexpected worker exit shows a **restart worker** dialog
- Application quit with active jobs uses `confirm_application_quit` (wait or quit anyway)

## Package boundary

| Package | Role |
|---------|------|
| **lexiflow-ui** | Spawn, supervise, status display |
| **lexiflow-worker** | Thin entry → core job runner |
| **lexiflow-core** | Queue persistence and consumption |
