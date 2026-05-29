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
