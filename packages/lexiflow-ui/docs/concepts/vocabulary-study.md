# Vocabulary and study UI

## What this is

The toolbar has separate **Vocabulary** and **Study** navigation modes for the **active target language**.

## Vocabulary

`VocabularyWidget` is browse-only:

- `VocabularyBrowseTable`: lemma, translation, explanation, level, difficulty combo
- Right-click row context menu: **Edit word**, **Delete**
- Delete asks for confirmation
- Search filters lemma, translation, explanation
- Sort: recent, alphabetical, level, difficulty
- **Add word**, **Export**, **Import** vocabulary zip bundles

## Study

`StudyWidget` hosts flashcard practice:

- `VocabularyStudyCard`: lemma visible; **Translation** shows the native translation (same font); **Original** flips back
- **Got it** calls `VocabularyStore.promote_fluency` (hard → well → fluent → easy)
- **Got it** disabled until translation is shown; hidden when difficulty is easy
- **Next** advances the shuffled deck (mastered words excluded)

## Reader integration

- Context menu **Add word** on translated and simplified tabs
- `reader_add_word.open_highlight_add_dialog` enqueues `JobType.LEMMA` when spaCy is unavailable
- Successful add enqueues vocabulary embed and emits `vocabulary_changed`

## Related

- [vocabulary.md](../../../lexiflow-core/docs/concepts/vocabulary.md) (core)
- [application-shell.md](application-shell.md)
