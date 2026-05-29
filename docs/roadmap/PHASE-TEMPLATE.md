# Phase ticket template

Copy sections into new phase README when splitting phases.

## Header

- **Branch:** `phase/XX-name`
- **PR title:** `Phase XX: …`

## Outcome

What exists after merge (demo-able / testable). Write **Outcome** in domain language from [common-language.md](../../common-language.md). TDD cycles, tests, and public interfaces may use technical detail.

## Scope In / Out

## References

- [common-language.md](../../common-language.md) — **Term1**, **Term2**, …
- Relevant [ADRs](../../adr/)
- Prior phases / architecture docs as needed

## Public interfaces

Python protocols / classes agents must implement.

## TDD cycles

For each cycle:

1. **Behavior** — user-observable sentence (domain language)
2. **Test** — file + assertion description (implementation detail OK)
3. **Green** — minimal implementation
4. **Edge cases**

## Manual verification

## PR checklist

- [ ] All cycles completed
- [ ] **Plan posted** per [pr-plan-template.md](../../guides/pr-plan-template.md)
- [ ] Concept docs in `packages/*/docs/concepts/` if new capability
- [ ] Domain changes in [common-language.md](../../common-language.md) if any

---

**Anti-pattern:** listing 20 tests then implementing — write cycles sequentially.  
**Anti-pattern:** PR without Plan or Plan that only narrates the diff.
