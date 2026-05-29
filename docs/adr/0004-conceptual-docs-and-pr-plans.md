# Conceptual documentation and PR plans

Every PR includes a **Plan** (description or first comment) explaining features, architecture, and documentation delivered — conceptual prose, not a code walkthrough. Package docs live in `packages/*/docs/concepts/` and describe stable behavior; they are updated when capabilities change, not on every refactor. See [documentation-strategy.md](../guides/documentation-strategy.md) and [pr-plan-template.md](../guides/pr-plan-template.md).

**Considered:** inline comments only; auto-generated API docs; single giant `/docs` far from code.

**Consequences:** reviewers validate plan before deep diff review; agents must write concept docs as part of feature phases; `common-language.md` holds domain language; `CONTEXT.md` is index only.
