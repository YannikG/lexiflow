## Plan

**Required.** Follow [docs/guides/pr-plan-template.md](docs/guides/pr-plan-template.md). Post in this description or as the **first PR comment**.

- [ ] Summary, features/behavior, architecture (concepts — not code walkthrough)
- [ ] **Semble** used for repo exploration; **context7** for library APIs (or exception stated)
- [ ] Documentation delivered (concept docs or explicit "none needed")
- [ ] Testing approach
- [ ] Out of scope stated

## Phase checklist

- [ ] GitHub Issue linked (`Closes #NN`)
- [ ] Phase README linked (e.g. `docs/roadmap/phases/phase-XX-.../README.md`)
- [ ] All TDD cycles in phase README completed
- [ ] `uv run ruff check` / `ruff format --check` pass (when applicable)
- [ ] `uv run pytest` pass (when applicable)
- [ ] [common-language.md](common-language.md) updated if domain terms changed
- [ ] New ADR if hard-to-reverse decision
- [ ] Package `docs/concepts/` updated if new public capability
