# PR plan template

Copy this into the **PR description** or post as the **first comment** on the PR. Required for every phase PR and every contributor PR.

---

## Plan

### Summary

One paragraph: what this PR delivers and why.

### Features and behavior

Bullet list of **user-visible or system-visible** behaviors added or changed. Use [domain language](../../common-language.md) terms.

### Architecture

- Which packages are touched and why
- New or changed boundaries (UI / worker / core)
- Data or process flows affected (prose or mermaid; no file dumps)
- Dependencies on prior phases or ADRs

### Code discovery

- [ ] **Semble** used to explore this repo (or exception stated below)
- [ ] **Context7** used for new/changed third-party library APIs (or N/A / exception stated)

See [`.agents/rules/code-discovery.md`](../../.agents/rules/code-discovery.md).

### Documentation delivered

List **concept docs** added or updated (not a list of every edited file):

| Doc | What it explains |
|-----|------------------|
| e.g. `packages/lexiflow-core/docs/concepts/job-queue.md` | Persistent queue, states, recovery |

If no new concept doc is needed, state why (e.g. "internal refactor only, behavior unchanged").

### Testing approach

Which behaviors are covered by tests and how (integration vs UI smoke). No test code paste.

### Risks and follow-ups

Known gaps, deferred items, or phase N+1 dependencies.

### Out of scope

What this PR explicitly does **not** do (prevents scope creep).

---

**Rules:** No 1:1 code narration. No line-by-line walkthrough. Explain **concepts** so a reviewer understands intent without reading every diff hunk.
