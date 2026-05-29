# LexiFlow rules

Portable agent rules. Root [AGENTS.md](../AGENTS.md) is the primary entry.

**Mandatory:** [code-discovery.md](code-discovery.md) — semble + context7 before grep or guessing library APIs.

## Before coding

1. Read [CONTEXT.md](../../CONTEXT.md) and [common-language.md](../../common-language.md).
2. Phase 01+: pick the GitHub Issue, read the linked phase README in `docs/roadmap/phases/`.
3. Follow [AGENTS.md](../../AGENTS.md) and [docs/guides/agent-workflow.md](../../docs/guides/agent-workflow.md).

## Rules

- **Semble first** for repo exploration; **context7 first** for third-party libraries ([code-discovery.md](code-discovery.md)).
- TDD vertical slices only (one test → minimal code → refactor when green).
- Feature PRs require a **Plan** per `docs/guides/pr-plan-template.md`.
- Domain terms live in `common-language.md` only.
- `lexiflow-core` has no Qt; `lexiflow-ui` has no llama.cpp imports.
