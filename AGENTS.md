# AGENTS.md

Instructions for AI agents working on LexiFlow.

## Before coding

1. Read [CONTEXT.md](CONTEXT.md) then [common-language.md](common-language.md) — domain language is law.
2. **Phase 00** is already on `main`. Pick the next **GitHub Issue** (phase 01+): confirm **blocked by** is clear, then read the linked **phase README** — **one phase = one issue = one PR**.
3. Read relevant [ADRs](docs/adr/).
4. Follow [agent workflow](docs/guides/agent-workflow.md) (bootstrap exception for phase 00; issues from phase 01).
5. Follow [code discovery](.agents/rules/code-discovery.md) — **semble** and **context7** are mandatory (see below).

## Code discovery (mandatory)

Full rules: [`.agents/rules/code-discovery.md`](.agents/rules/code-discovery.md). MCP config: [`.agents/mcp.json`](.agents/mcp.json) — merge into your tool's global MCP file ([setup](docs/guides/mcp-setup.md)). **No `.cursor/` folder in this repo;** Cursor uses `AGENTS.md` + `~/.cursor/mcp.json`.

### This repo

1. **semble** `search` → `find_related` → read surfaced chunks only.
2. **No** Grep/Glob-first exploration. **No** reading whole files before Semble.

### External libraries

1. **context7** `resolve-library-id` → `query-docs` before using PySide6, uv, pytest, or any dependency API.
2. **No** guessing signatures from training data.

### PR accountability

Feature PR Plan or checklist must state that semble/context7 were used, or document a rare exception.

Sub-agent: [`.agents/agents/semble-search.md`](.agents/agents/semble-search.md).

## PR Plan (mandatory)

Every PR: post a **Plan** in the description **or first comment**.

- [pr-plan-template.md](docs/guides/pr-plan-template.md)
- Explain features, architecture, documentation delivered — **not** a code walkthrough
- [documentation-strategy.md](docs/guides/documentation-strategy.md)

## TDD (mandatory)

- **Vertical slices only:** one test → one minimal implementation → refactor when green.
- Tests use **public interfaces**, not private methods.
- Use `FakeLLM`, `FakeEmbedder`, `FakeModelDownloader` in CI — no real Hugging Face downloads in PR tests.
- Do not mock internal collaborators; mock at protocol boundaries only.

## Single responsibility (mandatory)

Each module, class, and public function should have **one reason to change**. Enforce SRP in design and review; reject diffs that mix unrelated concerns.

### Rules

1. **One job per unit** — A function or class does one coherent thing. Name it after that job. If the name needs "and", split it.
2. **Callers own orchestration** — Composing steps (load settings → resolve paths → ensure layout) belongs in a thin coordinator or the caller. Do not hide unrelated side effects inside a low-level helper.
3. **No scope creep in helpers** — Utilities must not do work their name does not promise (e.g. a DB connector opens a connection; it does not create parent directories unless that is its documented job).
4. **Separate parsing from policy** — Lexing/parsing, I/O, persistence, and business rules live in different functions or modules. Do not embed fragile parsers inside orchestrators without tests targeted at the parser.
5. **Package boundaries reinforce SRP** — `lexiflow-core` holds domain and headless capabilities; `lexiflow-ui` wires Qt and process lifecycle; `lexiflow-worker` is entry only. Do not push UI concerns into core or domain logic into the worker stub.
6. **Type hints match responsibility** — Use `TYPE_CHECKING` and `from __future__ import annotations` to keep imports acyclic; do not weaken types to `object` to avoid fixing module layout.

### Examples (this repo)

| Prefer | Avoid |
|--------|-------|
| `connect_sqlite(path)` opens DB with pragmas only | `connect_sqlite` also `mkdir` parent dirs |
| `ensure_app_layout(data_root)` creates library dirs | `SettingsStore.save` also migrates databases |
| `ensure_database_parent(db_path)` prepares DB folder | `MigrationRunner` silently mkdirs without naming it |
| `MigrationLoader` discovers; `split_sql_script` parses; `SchemaMigrationJournal` tracks versions | One class that discovers, parses, tracks, and applies |
| `paths.py` pure calculations; `platform_dirs.py` OS config; `app_layout.py` mkdir | Path math mixed with OS detection and filesystem mutation |
| `settings.py` model; `settings_store.py` I/O; `settings_resolution.py` policy | One settings module that models, serializes, resolves, and persists |
| `bootstrap_runtime` in `bootstrap.py` | High-level orchestration mixed into path helpers |

### PR check

In the **Plan**, state when a new public type or module was introduced and what single responsibility it owns. If a change touches multiple concerns, split the PR or justify the exception.

## Package boundaries

| Package | Allowed |
|---------|---------|
| `lexiflow-core` | Domain, storage, jobs, LLM/embed protocols — **no Qt** |
| `lexiflow-ui` | PySide6, worker supervisor — **no llama.cpp imports** |
| `lexiflow-worker` | Thin entry → core worker loop |

## Documentation

- Domain terms → [common-language.md](common-language.md) only
- Project index → [CONTEXT.md](CONTEXT.md)
- Stable capabilities → `packages/*/docs/concepts/*.md` (concepts, minimal code refs)
- See ADR-0004

## Quality gate (must pass before PR)

```bash
uv sync
uv run ruff check .
uv run ruff format --check .
uv run mypy packages/lexiflow-core
uv run pytest
```

Coverage floors: **80% core**, **60% ui** (ADR-0001). Phase 01 enables real CI gates.

## PR format

- Title: `Phase XX: <outcome>`
- Body: link **GitHub Issue** + phase README + **Plan**; close issue with `Closes #NN`
- Do not start next phase in same PR

## Issues (phase 01+ until v1)

- Issue body: link to phase README only (spec stays in markdown until phase 16 migration)
- Use GitHub **blocked by** for phase order (01 → 15)
- Phase 00: no issue; committed directly to `main`
- After v1 + phase 16: specs live in issues; roadmap phase folders removed

## When to update docs

- Domain term change → `common-language.md`
- Hard-to-reverse arch choice → new ADR in `docs/adr/`
- New public capability → package `docs/concepts/`
