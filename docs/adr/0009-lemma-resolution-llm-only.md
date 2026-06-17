# ADR 0009: Lemma resolution is LLM-only (no spaCy)

## Status

Accepted (2026-06-17)

## Context

Phase 06 introduced optional spaCy language packs for fast local lemma and part-of-speech hints when adding vocabulary. The LLM `lemma` job already returns lemma, translation, explanation, and category.

Shipping spaCy in PyInstaller release bundles added large dependencies (spaCy, numpy, thinc) and fragile frozen-runtime model installs. Some catalog languages (e.g. Ukrainian) need extra wheels (`pymorphy3`, dictionaries) that `pip` handled in dev but not in packaged apps. Onboarding blocked on language pack download failures.

## Decision

**Lemma resolution is LLM-only in v1.** Remove spaCy from core dependencies and release bundles. Onboarding and add-language flows no longer download or install spaCy packs. Reader highlight-add and manual add word always enqueue the `lemma` background job (or wait on it in synchronous helpers).

## Consequences

- Smaller release installers; no per-language NLP pack download step.
- Add-word lemma fields appear after the LLM job completes (seconds, not instant).
- Users need a configured LLM for lemma inference (already required for translate/simplify).
- Legacy `{data_root}/.app/spacy/` directories are ignored; safe to delete manually.
- `download_spacy` queue rows remain obsolete and are pruned on queue open.

## Alternatives considered

1. **Keep spaCy, download model wheels at language install** — rejected: ongoing packaging complexity for a narrow optimization.
2. **Bundle spaCy + per-language extras** — rejected: inflates DMG size; Ukrainian needs pymorphy3 dicts anyway.

## References

- [common-language.md](../../common-language.md) — **Lemma resolution**
- [packages/lexiflow-core/docs/concepts/vocabulary.md](../../packages/lexiflow-core/docs/concepts/vocabulary.md)
- [packages/lexiflow-core/docs/concepts/job-queue.md](../../packages/lexiflow-core/docs/concepts/job-queue.md)
