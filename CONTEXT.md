# LexiFlow context map

Entry point for humans and agents. **Domain language** (glossary) lives in [common-language.md](common-language.md) — not here.

## What this repo is

**LexiFlow** is a desktop app for learning languages by reading real texts: local LLM translate and simplify, personal vocabulary, markdown on disk. See [common-language.md](common-language.md) **Product** and **Release bar**.

## Where to read what

| Document | Purpose |
|----------|---------|
| [common-language.md](common-language.md) | **Domain language** (common language) — canonical terms and behaviors |
| [docs/roadmap/README.md](docs/roadmap/README.md) | Phases; phase 00 on `main`, then one GitHub Issue + one PR per feature phase |
| [docs/architecture/overview.md](docs/architecture/overview.md) | Processes, packages, data layout |
| [docs/adr/](docs/adr/) | Irreversible architecture decisions |
| [docs/guides/documentation-strategy.md](docs/guides/documentation-strategy.md) | Concept docs vs code |
| [docs/guides/pr-plan-template.md](docs/guides/pr-plan-template.md) | Mandatory PR Plan |
| [docs/guides/mcp-setup.md](docs/guides/mcp-setup.md) | MCP: context7 + semble (see `.agents/`) |

## Rules

1. New or changed **domain term** → update [common-language.md](common-language.md).
2. New **irreversible decision** → add ADR in `docs/adr/`.
3. New **public capability** → concept doc in `packages/*/docs/concepts/`.
4. Do not duplicate glossary entries in `CONTEXT.md` or package READMEs.
5. Domain language is **`common-language.md` at repo root** — update there when terms change.
6. **Agents:** use **semble** then **context7** per [`.agents/rules/code-discovery.md`](.agents/rules/code-discovery.md) before grep or guessing APIs.

## Engineering bar (summary)

Three packages (core / ui / worker), TDD vertical slices, CI on every PR, mandatory PR Plan with concept documentation. Phase 00 bootstrap goes to `main`; feature phases 01+ use issues and PRs. Details in common-language **Release bar** and ADR-0001, ADR-0004.
