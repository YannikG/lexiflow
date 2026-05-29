# Documentation strategy

Conceptual docs live **next to the code they describe**. They explain **why** and **how things fit together**, not **what every line does**.

## Principles

1. **Concepts over code** — Describe behavior, boundaries, and trade-offs. No 1:1 rewrite of the implementation.
2. **Stable across refactors** — If renaming a function does not change user-visible behavior, docs should not need an update.
3. **Minimal code references** — Avoid file paths and line numbers. Name modules or public types only when necessary.
4. **Structured and scannable** — Headings, short paragraphs, diagrams where helpful.
5. **Two layers** — Domain language at repo root ([common-language.md](../../common-language.md)); project index ([CONTEXT.md](../../CONTEXT.md)); package concept docs under `packages/*/docs/concepts/`.

## Where docs live

```
lexiflow/
  CONTEXT.md                    ← index (where to read what)
  common-language.md            ← domain language (glossary)
  docs/
    adr/                        ← irreversible decisions
    roadmap/                    ← phase tickets (planning)
    architecture/               ← cross-cutting diagrams
    guides/                     ← contributor and agent guides
  packages/
    lexiflow-core/
      README.md                 ← package purpose and public surface
      docs/
        concepts/               ← e.g. job-queue.md, text-storage.md
    lexiflow-ui/
      README.md
      docs/
        concepts/
    lexiflow-worker/
      README.md
```

**Do not** document every private helper. **Do** document public capabilities and invariants agents must preserve.

## What belongs in package `docs/concepts/`

| Good | Bad |
|------|-----|
| "The job queue persists to sqlite so crashes do not lose work." | "`JobService._flush()` writes row 42 to `queue.sqlite`." |
| "One LLM job runs at a time to limit RAM." | Full paste of `handle_translate` body. |
| "Vocabulary level when learned is historical, not current skill." | Table column listing for every migration. |

## When to update docs

| Change | Update |
|--------|--------|
| New domain term or behavior change | `common-language.md` |
| New irreversible arch choice | New ADR |
| New public capability in a package | That package's `docs/concepts/` |
| Internal refactor, same behavior | Usually **no** doc change |
| Phase completes new feature area | PR plan + concept doc (see phase 00) |

## PR documentation requirement

Every PR must include a **Plan** (in the PR description or first comment). See [pr-plan-template.md](pr-plan-template.md).

The plan is **additional** to code and tests. Reviewers judge whether the change matches the plan.
