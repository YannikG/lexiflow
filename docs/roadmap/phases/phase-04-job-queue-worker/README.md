# Phase 04: Job queue and worker

**Branch:** `phase/04-job-queue-worker`  
**PR title:** `Phase 04: Persistent job queue, worker process, FakeLLM`

## Outcome

- Persisted **job queue** survives restart; states include Pending, Running, Completed, Failed, Cancelled
- **One LLM job at a time**; additional work waits in queue
- Interrupted Running jobs recover as Pending on startup
- Worker process consumes queue headlessly; job failure does not crash worker
- **Process architecture** foundation: UI enqueues, worker executes

## References

- [ADR-0002](../../adr/0002-persistent-job-queue-and-single-instance.md)
- [ADR-0003](../../adr/0003-job-execution-architecture.md)
- [common-language.md](../../../../common-language.md): **Job queue**, **LLM job UX**, **Job cancelled state**, **Process architecture**

## Public interfaces

```python
# lexiflow_core.jobs
class JobType(Enum): CLEANUP, TRANSLATE, SIMPLIFY, EMBED, ...

class JobService:
    def enqueue(self, job: JobRequest) -> JobId: ...
    def list_jobs(self, limit: int = 50) -> list[JobRecord]: ...
    def cancel(self, job_id: JobId) -> None: ...
    def retry(self, job_id: JobId) -> None: ...
    def recover_on_startup(self) -> None: ...

# lexiflow_core.llm
class LLMProvider(Protocol):
    def complete(self, prompt: str, *, json_schema: dict | None = None) -> str: ...

class FakeLLM(LLMProvider): ...

# lexiflow_worker.runner
def run_worker_loop(job_service: JobService, llm: LLMProvider) -> None: ...
```

## TDD cycles

### Cycle 4.1 — Enqueue persists pending job

**Test:** enqueue → row in queue.sqlite status pending.

---

### Cycle 4.2 — Worker completes job

**Test:** FakeLLM returns fixed string; job → completed; result stored.

---

### Cycle 4.3 — One job at a time

**Test:** enqueue 2; only one running until first completes.

---

### Cycle 4.4 — Failure marks failed not crash

**Test:** FakeLLM raises; job failed with error message; worker alive for next job.

---

### Cycle 4.5 — Cancel pending

**Test:** cancel pending → cancelled; never runs.

---

### Cycle 4.6 — Startup recovery running→pending

**Test:** insert running job; `recover_on_startup()` → pending.

---

### Cycle 4.7 — Prune completed >20

**Test:** 25 completed; list keeps 20 newest.

---

### Cycle 4.8 — Manual retry failed

**Test:** failed job → retry → pending → completes on next tick.

**Edge:** retry does not auto-run on startup (only pending from recovery).

---

## Manual verification

- Run worker CLI against temp queue with FakeLLM.

## PR checklist

- [ ] No Qt in worker package imports from core jobs
- [ ] Migrations for queue.sqlite in `migrations/queue/`
