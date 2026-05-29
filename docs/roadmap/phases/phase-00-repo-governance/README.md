# Phase 00: Repo and docs governance

**Delivery:** commit **directly to `main`** (bootstrap). No PR, no GitHub Issue.  
**Commit message:** `Phase 00: GitHub repo, agent rules, CI skeleton, and documentation governance`

## Outcome

After phase 00 is on `main`, the repo is governed and ready for feature work (phase 01+):

- **Domain language** and context map at repo root (`common-language.md`, `CONTEXT.md`)
- Contributor workflow: **PR Plan** required on every feature PR, **concept doc** scaffolding per package
- **CI quality gates** skeleton (full green in phase 01)
- ADRs, roadmap, agent rules
- **Agent config** in `.agents/` (MCP, rules, sub-agents); tool-specific symlinks optional
- **GitHub Issues** for phases **01–15** (link-only bodies, **blocked by** chain); issue templates in `.github/ISSUE_TEMPLATE/`
- Branch protection enabled on `main` before the first feature PR (phase 01)
- No application code yet — governance and docs only

**Prerequisite for phase 01:** phase 00 on `main`, issues 01–15 created, branch protection on.

## Scope

### In

- Repo hygiene and contributor workflow
- CI workflow files (may use placeholder job until phase 01 adds pytest)
- Documentation strategy ADR-0004 and guides
- PR plan requirement in CONTRIBUTING + template
- Project agent config in `.agents/` (MCP context7 + semble) + [mcp-setup.md](../../guides/mcp-setup.md)

### Out

- Python application code, uv workspace, tests (phase 01)
- PyInstaller, release workflow (phase 15)
- Enabling branch protection on GitHub (owner applies in UI after first push; not a repo file)

## References

- [ADR-0001](../../adr/0001-split-packages-and-ci-quality-gates.md)
- [ADR-0004](../../adr/0004-conceptual-docs-and-pr-plans.md)
- [Documentation strategy](../../guides/documentation-strategy.md)
- [PR plan template](../../guides/pr-plan-template.md)
- [MCP setup](../../guides/mcp-setup.md)
- [common-language.md](../../../../common-language.md): **Domain language**, **PR Plan**, **Concept doc**, **ADR**, **CI quality gates**, **TDD vertical slice**, **lexiflow-core**, **lexiflow-ui**, **lexiflow-worker**
- Root [CONTEXT.md](../../../../CONTEXT.md) and [common-language.md](../../../../common-language.md)

## Governance files (deployed in repo)

| Path | Purpose |
|------|---------|
| `CONTRIBUTING.md` | Contributor workflow |
| `.github/pull_request_template.md` | PR Plan + checklist |
| `.github/workflows/ci.yml` | CI skeleton (`lint`, `test` jobs) |
| `.github/dependabot.yml` | GitHub Actions updates (pip/uv in phase 01) |
| `.github/ISSUE_TEMPLATE/phase.yml` | Phase issue form |
| `.github/ISSUE_TEMPLATE/phase.md` | Phase issue markdown fallback |
| `.agents/mcp.json` | MCP servers (context7, semble) |
| `.agents/agents/semble-search.md` | Semble search sub-agent |
| `.agents/rules/lexiflow.md` | Portable project rules |

## Deliverables checklist

### `.agents/`

| File | Purpose |
|------|---------|
| `README.md` | Index + wire MCP to your tool |
| `mcp.json` | MCP: context7 + semble |
| `rules/lexiflow.md` | Agent guardrails |
| `rules/code-discovery.md` | Mandatory semble + context7 |
| `agents/semble-search.md` | Semble search sub-agent |

### Repository root

| File | Purpose |
|------|---------|
| `CONTEXT.md` | Context map (index to docs) |
| `common-language.md` | Domain language (canonical glossary) |
| `AGENTS.md` | Agent instructions |
| `CONTRIBUTING.md` | Human + agent contribution rules |
| `SECURITY.md` | Vulnerability reporting |
| `LICENSE` | Apache-2.0 |
| `README.md` | Project intro, link to CONTRIBUTING and roadmap |

### `.github/`

| File | Purpose |
|------|---------|
| `pull_request_template.md` | Plan section + checklist |
| `workflows/ci.yml` | Lint/test gates (skeleton) |
| `dependabot.yml` | Weekly deps |
| `ISSUE_TEMPLATE/phase.yml` | v1 phase issues (link to phase README, blocked-by) |
| `ISSUE_TEMPLATE/phase.md` | Fallback markdown template for phase issues |

### `docs/`

Planning, ADRs, roadmap, guides (including `guides/mcp-setup.md`). No duplicate `AGENTS.md` under `docs/`.

### Package scaffolding (no implementation)

```
packages/
  lexiflow-core/README.md
  lexiflow-core/docs/concepts/.gitkeep
  lexiflow-ui/README.md
  lexiflow-ui/docs/concepts/.gitkeep
  lexiflow-worker/README.md
  lexiflow-worker/docs/concepts/.gitkeep
```

Each package README: one paragraph purpose + link to `docs/concepts/`.

## TDD / verification cycles

Phase 00 is governance-heavy. Use **verification cycles** instead of pytest.

---

### Cycle 0.1 — PR template enforces Plan

**Behavior:** Opening a PR shows Plan section and link to pr-plan-template.

**Verify:** `.github/pull_request_template.md` contains `## Plan` and checklist items.

---

### Cycle 0.2 — CONTRIBUTING documents Plan rule

**Behavior:** CONTRIBUTING states Plan is mandatory in PR body or first comment.

**Verify:** Read CONTRIBUTING; rule explicit for humans and agents.

---

### Cycle 0.3 — Documentation strategy committed

**Behavior:** `docs/guides/documentation-strategy.md` defines concept docs vs code.

**Verify:** File exists; ADR-0004 references it.

---

### Cycle 0.4 — CI workflow present

**Behavior:** `ci.yml` runs on `pull_request` to `main`.

**Verify:** YAML valid; jobs named `lint`, `test` (test may be placeholder `echo` until phase 01).

---

### Cycle 0.5 — CI check names for GitHub branch protection

**Behavior:** `ci.yml` exposes jobs named `lint` and `test` so GitHub can require them after the first push.

**Verify:** YAML valid; job names match what you enable under Settings → Branches (manual, not in repo).

---

### Cycle 0.6 — Agent rules in `.agents/`

**Behavior:** `.agents/rules/lexiflow.md` points to AGENTS.md, CONTEXT.md, common-language.md, and phase README workflow.

**Verify:** File exists; [AGENTS.md](../../../../AGENTS.md) references `.agents/`.

---

### Cycle 0.7 — Package concept doc placeholders

**Behavior:** Each package has `docs/concepts/` directory.

**Verify:** Tree exists; README explains where concepts go.

---

### Cycle 0.8 — Plan template committed (dogfood starts phase 01)

**Behavior:** PR plan template and PR template exist so phase 01 PR demonstrates the Plan.

**Verify:** `docs/guides/pr-plan-template.md` and `.github/pull_request_template.md` present.

**Edge:** Phase 00 does not open a PR; first Plan appears on phase 01 PR.

---

### Cycle 0.9 — Phase issues and blocked-by chain (01–15)

**Behavior:** GitHub issues exist for phases **01–15** with link-only bodies pointing at `docs/roadmap/phases/.../README.md`; each issue after 01 is **blocked by** the previous phase issue. No issue for phase 00.

**Verify:** Issue template in `.github/ISSUE_TEMPLATE/phase.yml`; CONTRIBUTING and [agent-workflow.md](../../guides/agent-workflow.md) document feature-phase issue workflow.

---

### Cycle 0.10 — MCP servers (context7 + semble)

**Behavior:** `.agents/mcp.json` configures context7 and semble; [code-discovery.md](../../../../.agents/rules/code-discovery.md) **mandates** their use before grep or API guesses.

**Verify:** Files exist; AGENTS.md and CONTRIBUTING reference code-discovery; PR template includes semble/context7 checklist.

---

## Manual verification

1. Clone scaffold repo
2. Open PR → template appears
3. `actionlint` or manual YAML review on workflows
4. After first push: enable branch protection on `main` in GitHub (require PR, `lint` + `test`, no force push)

## PR checklist

Phase 00 has no PR. Before starting phase 01:

- [ ] Cycles 0.1–0.10 verified on `main`
- [ ] Branch protection enabled on `main`
- [ ] Issues created for phases 01–15 with **blocked by** chain
- [ ] No Python app logic beyond empty package READMEs
- [ ] `CONTEXT.md` and `common-language.md` at repo root only

## Phase 01 Plan example (for agents)

The **first PR** (phase 01) should include a Plan like:

> **Summary:** Establishes LexiFlow monorepo with green CI and hello window.  
> **Features:** Minimal application shell.  
> **Architecture:** Three-package uv workspace; pytest-qt smoke.  
> **Documentation:** `application-shell.md` concept doc.  
> **Testing:** TDD cycles 1.1–1.7.
