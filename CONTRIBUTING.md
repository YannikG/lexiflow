# Contributing to LexiFlow

## Workflow

**Phase 00:** commit governance scaffold directly to `main` (see [phase 00](docs/roadmap/phases/phase-00-repo-governance/README.md)).

**Phase 01+:**

1. Pick the next open **GitHub Issue** ([roadmap index](docs/roadmap/README.md)); confirm **blocked by** dependencies are closed.
2. Read the **phase README** linked from the issue (full spec).
3. Branch: `phase/XX-short-name`
4. Read [CONTEXT.md](CONTEXT.md) and [common-language.md](common-language.md).
5. Follow [TDD vertical slices](docs/guides/agent-workflow.md).
6. Open PR to `main` with `Closes #NN` for the phase issue.

## PR Plan (mandatory)

Every PR must include a **Plan** in the PR description **or as the first comment**.

Use [docs/guides/pr-plan-template.md](docs/guides/pr-plan-template.md). The plan explains:

- Features and behavior (domain language)
- Architecture and boundaries (concepts, not code dumps)
- **Documentation delivered** — concept docs in `packages/*/docs/concepts/` or why none
- Testing approach
- Out of scope

Plans are **not** a line-by-line rewrite of the diff. Reviewers use the plan to judge intent.

See [documentation strategy](docs/guides/documentation-strategy.md) and [ADR-0004](docs/adr/0004-conceptual-docs-and-pr-plans.md).

## Quality gates

```bash
uv sync
uv run ruff check .
uv run ruff format --check .
uv run mypy packages/lexiflow-core
uv run pytest
```

All must pass before merge. Coverage floors: 80% core, 60% ui (see ADR-0001).

## Agents

Read [AGENTS.md](AGENTS.md) before automated contributions.

**Mandatory:** [`.agents/rules/code-discovery.md`](.agents/rules/code-discovery.md) — semble for this repo, context7 for library docs. Wire MCP from [`.agents/mcp.json`](.agents/mcp.json) ([setup](docs/guides/mcp-setup.md)).

## Security

See [SECURITY.md](SECURITY.md).
