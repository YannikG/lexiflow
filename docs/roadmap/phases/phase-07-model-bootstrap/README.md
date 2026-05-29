# Phase 07: Model bootstrap (Hugging Face)

**Branch:** `phase/07-model-bootstrap`  
**PR title:** `Phase 07: models.lock, HF downloader, bootstrap in onboarding`

## Outcome

- **Model bootstrap** downloads pinned models on first use with progress UI
- **Model pinning** manifest defines exact revisions for embedded model, **embedding model**, spaCy packs
- Optional **Hugging Face token** in **settings**
- **Onboarding LLM setup** completes embedding model; embedded path queues LLM unless **Ollama endpoint** configured
- **Model updates** check in settings compares installed vs pinned revision
- **Bootstrap network retry** on failure during onboarding

## References

- [common-language.md](../../../../common-language.md): **Model bootstrap**, **Model pinning**, **Hugging Face token**, **Network requirement**, **Bootstrap network retry**

## Public interfaces

```python
# lexiflow_core.models.lockfile
def load_models_lock() -> ModelsLock: ...

# lexiflow_core.models.download
class ModelDownloader(Protocol):
    def download(self, artifact: ModelArtifact, dest: Path, *, token: str | None) -> None: ...

class FakeModelDownloader(ModelDownloader): ...

# lexiflow_core.models.store
class ModelStore:
    def is_installed(self, artifact_id: str) -> bool: ...
    def ensure_installed(self, artifact_id: str, on_progress: Callable) -> Path: ...
    def check_for_updates(self) -> list[UpdateAvailable]: ...
```

## TDD cycles

### Cycle 7.1 — Parse models.lock

**Test:** fixture lock → two artifacts with revisions.

---

### Cycle 7.2 — Fake downloader writes marker file

**Test:** ensure_installed → file exists in models dir.

---

### Cycle 7.3 — Skip Gemma download when Ollama configured

**Test:** settings ollama set → Gemma not required for onboarding complete.

---

### Cycle 7.4 — MiniLM required always

**Test:** Ollama path still downloads MiniLM.

Until [phase 10b](../phase-10b-ollama-embeddings/README.md) ([ADR 0005](../../../adr/0005-ollama-embedding-provider-deferred.md)).

---

### Cycle 7.5 — HF token passed to downloader

**Test:** token in settings → fake downloader receives it.

---

### Cycle 7.6 — Update check detects newer revision

**Test:** installed rev older than lock → UpdateAvailable.

---

### Cycle 7.7 — Offline blocks bootstrap

**Test:** downloader raises NetworkError → wizard shows error, retry btn.

---

## Manual verification

- Onboarding with fake downloader injected in dev menu (optional).

## PR checklist

- [ ] No real HF calls in CI
- [ ] README note: first install network required
