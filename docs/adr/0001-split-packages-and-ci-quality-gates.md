# Split packages (core/ui) and CI quality gates

LexiFlow uses a monorepo with three Python packages: **lexiflow-core** (domain, storage, LLM, embeddings, job queue — no Qt), **lexiflow-ui** (PySide6 shell), and **lexiflow-worker** (thin queue consumer entrypoint). Every PR must pass automated quality gates so agent-generated changes cannot merge broken code: Ruff lint + format check, pytest (unit + integration), and pytest-qt smoke tests for critical UI paths. Release builds (DMG/MSI/AppImage) run on version tags only. **One PyInstaller bundle** ships all three; UI spawns worker via same binary with worker entrypoint.

**Considered:** single `src/lexiflow` package (simpler, but couples UI to testable core and makes agent refactors riskier).

**Consequences:** UI depends on core via explicit public APIs; core must stay Qt-free and fully testable headless. CI is the merge gate for humans and agents alike.

**CI PR gate (`ci.yml`):** Ruff lint, Ruff format check, mypy on core, pytest with coverage floors (**80% lexiflow-core**, **60% lexiflow-ui**), pytest-qt smoke tests for critical UI paths. All checks required; no merge on failure. **Phase 00** ships a CI skeleton only: jobs named `lint` and `test` run placeholder steps until **phase 01** wires real Ruff, mypy, and pytest. **Dependency management:** `uv` workspace with committed `uv.lock` (from phase 01); CI installs via uv. **lexiflow-worker** covered by core integration tests; no separate coverage floor.

**LLM in tests:** `LLMProvider` interface in core; unit/integration tests use `FakeLLM` with canned responses. No real Gemma download in PR CI.

**Pre-commit:** Local hooks run Ruff lint + format (fast subset aligned with CI). Full test suite runs in CI only.

**Agent instructions:** Root `AGENTS.md` plus `.agents/` (MCP, rules, sub-agents). **Mandatory:** [code-discovery.md](.agents/rules/code-discovery.md) — semble for repo search, context7 for library docs before implementation.

**Python version:** 3.12 (`requires-python = ">=3.12,<3.14"`).

**Git workflow:** Phase 00 commits governance directly to `main`. After that, `main` is protected; all changes via PR with required CI checks. Version tags on `main` trigger release builds. Self-merge permitted when CI is green (solo/small team).

**Dependabot:** Weekly PRs for GitHub Actions (from phase 00). Python/uv dependency updates start in **phase 01** when `pyproject.toml` exists; merge only after CI passes.

**GitHub repo hygiene:** `CONTRIBUTING.md`, PR template (tests, CI, common-language/ADR updates), issue templates, and `SECURITY.md`.
