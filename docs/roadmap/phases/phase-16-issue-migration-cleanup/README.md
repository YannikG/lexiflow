# Phase 16: Issue migration and roadmap cleanup

**Branch:** `phase/16-issue-migration-cleanup`  
**PR title:** `Phase 16: Migrate phase specs into GitHub Issues, remove roadmap phases`

## Outcome

- Each closed phase issue (00–15) updated with full spec content copied from its phase README (outcome, scope, TDD cycles, checklists)
- `docs/roadmap/phases/` removed from repo (or reduced to a short pointer doc)
- [roadmap/README.md](../README.md) updated: v1 complete; future work is issue-driven with content in issues
- [agent workflow](../../guides/agent-workflow.md) updated for post-v1 issue-only specs
- Agents and contributors no longer open phase markdown for new work

## Scope

### In

- Script or documented manual steps to paste phase README into matching closed GitHub Issues
- Verify all phase issues #… have body content self-contained
- Remove `docs/roadmap/phases/phase-00` … `phase-15` directories
- Keep [roadmap/README.md](../README.md) as high-level history / phase diagram archive (optional slim version)
- Update CONTRIBUTING, AGENTS, issue templates for post-v1 workflow

### Out

- Rewriting history of merged PRs
- Deleting closed issues

## References

- [agent-workflow.md](../../guides/agent-workflow.md) (v1 → post-v1 transition)
- Phase 15 must be merged and v1 tag released first

## TDD cycles

### Cycle 16.1 — Migration checklist per phase issue

**Behavior:** for each phase 00–15, closed issue body contains former README sections (Outcome, Scope, TDD, checklist).

**Test:** checklist doc or script output: 16/16 issues updated.

---

### Cycle 16.2 — Repo no longer depends on phase folders

**Behavior:** `docs/roadmap/phases/` deleted; links from CONTRIBUTING/AGENTS point to issues workflow only.

**Test:** `rg 'roadmap/phases/phase-'` only hits changelog/archive if any.

---

### Cycle 16.3 — New issue template expects full spec in body

**Behavior:** `.github/ISSUE_TEMPLATE/` updated; no “link only” template for features.

---

## Manual verification

1. Open a migrated issue on GitHub — readable without repo checkout
2. Clone repo — no phase-XX README paths required for onboarding

## PR checklist

- [ ] All phase issues 00–15 bodies updated on GitHub
- [ ] Phase folders removed
- [ ] Agent workflow documents post-v1 process
- [ ] README states v1 roadmap complete
