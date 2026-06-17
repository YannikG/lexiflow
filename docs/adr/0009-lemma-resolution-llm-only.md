# ADR 0009: Lemma resolution is LLM-only (no spaCy)

## Status

Accepted (2026-06-17)

## Context

Early phase specs described optional spaCy language packs for fast local lemma and part-of-speech hints when adding vocabulary. In practice the LLM `lemma` job already returns lemma, translation, explanation, and category, and LexiFlow already requires a configured LLM for translate and simplify.

Attempting to ship spaCy in PyInstaller release bundles surfaced problems that are not worth solving for v1:

- Large transitive dependencies (spaCy, numpy, thinc) in the installer
- Frozen apps cannot rely on `pip` to install per-language model wheels at runtime
- Some catalog languages need extra wheels (e.g. Ukrainian: `pymorphy3`, dictionaries)
- Onboarding blocked when pack download failed, even though the LLM path already worked

## Decision

**LexiFlow does not use spaCy.** Lemma resolution is **LLM-only**:

- No `spacy` dependency in `lexiflow-core`
- No spaCy collection in `packaging/lexiflow.spec`
- No language-pack download step in onboarding or **Switch language**
- Reader highlight-add and manual add word always use the `lemma` background job

Treat spaCy as **out of product scope**, not as a missing optional install. Documentation and tests describe lemma inference via the job queue only; we do not assert that spaCy is absent from packaging (same as we do not assert other libraries we never adopted).

## Consequences

- Smaller release installers; simpler onboarding and add-language flows
- Add-word lemma fields appear after the LLM job completes (seconds, not instant)
- Users need a configured LLM for lemma inference (already required for core workflows)
- **Migration only:** legacy `{data_root}/.app/spacy/` directories and `download_spacy` queue rows from older builds are ignored or pruned; no code reads them

## Alternatives considered

1. **Keep spaCy, download model wheels when adding a language** — rejected: ongoing packaging and per-language dependency complexity for a narrow speed-up
2. **Bundle spaCy and all per-language extras in the installer** — rejected: inflates DMG size; does not scale across the catalog

## References

- [common-language.md](../../common-language.md) — **Lemma resolution**
- [packages/lexiflow-core/docs/concepts/vocabulary.md](../../packages/lexiflow-core/docs/concepts/vocabulary.md)
- [packages/lexiflow-core/docs/concepts/job-queue.md](../../packages/lexiflow-core/docs/concepts/job-queue.md)
