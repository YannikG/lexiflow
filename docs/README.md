# LexiFlow documentation

Planning, architecture, and agent guides for the LexiFlow desktop app.

## Index

| Document | Purpose |
|----------|---------|
| [CONTEXT.md](../CONTEXT.md) | Project context map (start here) |
| [common-language.md](../common-language.md) | **Domain language** (common language) — canonical terms |
| [roadmap/README.md](roadmap/README.md) | Phase overview; GitHub Issues + PR rules (v1) |
| [roadmap/phases/](roadmap/phases/) | Phase README = full spec until phase 16 migration |
| [adr/](adr/) | Architecture decision records |
| [architecture/overview.md](architecture/overview.md) | Processes, packages, data layout |
| [guides/agent-workflow.md](guides/agent-workflow.md) | GitHub Issues, blockers, PR Plan, TDD |
| [guides/mcp-setup.md](guides/mcp-setup.md) | MCP wiring (semble + context7 required) |
| [../.agents/rules/code-discovery.md](../.agents/rules/code-discovery.md) | Mandatory agent search/docs policy |
| [../.agents/README.md](../.agents/README.md) | Portable agent config index |
| [guides/documentation-strategy.md](guides/documentation-strategy.md) | Concept docs vs code; when to update |
| [guides/pr-plan-template.md](guides/pr-plan-template.md) | Mandatory PR Plan structure |
| [../.github/ISSUE_TEMPLATE/](../.github/ISSUE_TEMPLATE/) | Phase issue templates (v1) |

## Rules for agents

1. **Phase 00** → direct commit to `main`. **Phase 01+** → one GitHub Issue, one PR per phase. Issue links phase README; use **blocked by** for order. Branch: `phase/XX-short-name`.
2. Read [CONTEXT.md](../CONTEXT.md) then [common-language.md](../common-language.md); linked ADRs before coding.
3. Post a **PR Plan** per [guides/pr-plan-template.md](guides/pr-plan-template.md).
4. Follow the phase README **TDD cycles in order** (vertical slices only).
5. Do not start phase N+1 until phase N issue is closed and CI is green.
6. Update [common-language.md](../common-language.md) when domain terms change; add ADR when decision meets ADR criteria in [adr/README.md](adr/README.md).

## Repo layout (target)

```
lexiflow/
  CONTEXT.md         ← context map (index)
  common-language.md ← domain language (common language glossary)
  packages/
    lexiflow-core/
    lexiflow-ui/
    lexiflow-worker/
  docs/              ← planning, ADRs, roadmap
  models.lock        ← phase 07+
  pyproject.toml     ← phase 01+
  uv.lock            ← phase 01+
  AGENTS.md
  .github/
```
