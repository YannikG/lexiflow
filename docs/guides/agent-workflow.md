# Agent workflow

## Bootstrap: phase 00 on `main`

**Phase 00 is the only exception:** commit governance scaffold **directly to `main`** (repo already exists on disk). No PR, no GitHub Issue for phase 00.

After phase 00 is on `main`, enable branch protection, create GitHub Issues for **phases 01–15**, then **all further work is feature phases only** via issue + PR.

## v1 workflow: GitHub issues + phase markdown (phase 01+)

From phase 01 onward until v1 ships, **work is tracked in GitHub Issues**, not duplicated in the issue body.

| Where | What lives there |
|-------|------------------|
| **GitHub Issue** | Title, link to phase README, blocked-by links, status |
| **Phase README** | Full planning: outcome, scope, TDD cycles, interfaces, checklist |
| **PR** | Implementation + **Plan**; closes the issue |

After v1, phase 16 migrates spec content into closed issues and removes `docs/roadmap/phases/` from the repo. See [phase 16](../roadmap/phases/phase-16-issue-migration-cleanup/README.md).

### Picking up work (phase 01+)

1. Open the GitHub Issue for the next phase (or the issue assigned to you).
2. Confirm **blocked by** dependencies are closed (previous phase issue merged).
3. Read the linked phase README — that file is the ticket spec (e.g. `docs/roadmap/phases/phase-08-add-text-translate/README.md`).
4. Read [CONTEXT.md](../../CONTEXT.md), [common-language.md](../../common-language.md), and ADRs referenced in the phase README.
5. Create branch `phase/XX-short-name` (match phase README).

## Code discovery (mandatory)

Before implementing or answering how the codebase works:

1. **[semble](https://github.com/MinishLab/semble)** — `search` / `find_related` on this repo (`repo` = workspace root). No Grep-first exploration.
2. **[context7](https://context7.com)** — `resolve-library-id` + `query-docs` for any third-party library API.

Full policy: [`.agents/rules/code-discovery.md`](../../.agents/rules/code-discovery.md). Sub-agent: [`.agents/agents/semble-search.md`](../../.agents/agents/semble-search.md).

### Issue rules (v1, phases 01–15)

- **Minimal issue body:** link to phase README only; optional one-line outcome reminder. Do not copy TDD cycles or scope into the issue.
- **Title:** `Phase XX: <short name>` (align with phase README PR title).
- **Blocked by:** set GitHub **blocked by** to the previous phase issue (linear chain 01 → 02 → … → 15). Phase 01 has no blocker (phase 00 is already on `main`).
- **Labels:** e.g. `phase`, `v1` (project convention).
- **Closing:** merge PR with `Closes #NN` (or `Fixes #NN`) so the issue closes when the phase lands on `main`.

### Example issue body

```markdown
## Spec

[docs/roadmap/phases/phase-08-add-text-translate/README.md](docs/roadmap/phases/phase-08-add-text-translate/README.md)

## Blocked by

- #7
```

Replace `#7` with the actual previous-phase issue number.

### PR ↔ issue (phase 01+)

- PR title matches phase README: `Phase XX: <outcome>`
- PR description: link **issue** + link **phase README** + **Plan** (mandatory)
- One issue → one PR → one merge. Do not combine phases.
- Do not open PRs for phase 00 (already on `main`).

## PR Plan (mandatory, phase 01+)

Every **feature phase PR** includes a **Plan** in the description **or as the first comment**. Phase 00 bootstrap commits to `main` without a PR.

- Template: [pr-plan-template.md](pr-plan-template.md)
- Strategy: [documentation-strategy.md](documentation-strategy.md)
- ADR: [0004-conceptual-docs-and-pr-plans.md](../adr/0004-conceptual-docs-and-pr-plans.md)

The plan covers features, architecture, and **documentation delivered** — conceptual text, not a 1:1 code rewrite.

## TDD rules (mandatory)

From the TDD skill — **vertical slices only:**

```
RED   → one test for one behavior → fails
GREEN → minimal code → passes
REFACTOR → only when green
```

Do **not** write all tests then all code. Each cycle in the phase README is one PR-sized chunk of work within the phase.

Technical detail in phase README TDD sections is intentional — follow it there, not in the issue.

## Definition of done

### Phase 00 (bootstrap on `main`)

- [ ] All verification cycles in [phase 00 README](../roadmap/phases/phase-00-repo-governance/README.md) completed
- [ ] Pushed to `main`; branch protection enabled before phase 01
- [ ] GitHub Issues created for phases **01–15** (link-only bodies, **blocked by** chain)
- [ ] No application code beyond empty package READMEs

### Every feature phase (01–15)

- [ ] **Semble** used for repo exploration (or exception noted in Plan)
- [ ] **Context7** used for new/changed library APIs (or exception noted in Plan)
- [ ] GitHub Issue **blocked by** chain satisfied; issue linked in PR
- [ ] All TDD / verification cycles in phase README completed
- [ ] **Plan posted** (description or first comment)
- [ ] Concept docs updated in `packages/*/docs/concepts/` when public capability changes
- [ ] `uv run ruff check` / `ruff format --check` pass (when code exists)
- [ ] `uv run pytest` pass with coverage floors (ADR-0001)
- [ ] mypy pass on `lexiflow-core`
- [ ] Phase **Outcome** manually verified
- [ ] Domain changes reflected in [common-language.md](../../common-language.md) if any
- [ ] Issue closed via merge (`Closes #NN`)

## PR title format

```
Phase XX: <short outcome statement>
```

Example: `Phase 00: GitHub repo, agent rules, and documentation governance`

## After v1 (phase 16)

Do not create new `docs/roadmap/phases/` tickets. New work uses **issue body as spec**. Phase 16 copies each phase README into its closed GitHub Issue, then removes phase folders from the repo. Historical content remains in GitHub, not in `docs/roadmap/phases/`.
