You are simplifying foreign-language reading text for a language learner.

Target language level: {target_level}
Native language (for glosses): {native_language}
Target language: {target_language}

Use vocabulary words from this list where they fit naturally:
{vocabulary_words}

Source text (translated variant):
{source_markdown}

Respond with JSON only. Fields:
- title: target-language document title (single line, no markdown heading)
- body: simplified markdown body without a top-level heading
- new_words: array of objects with lemma, gloss (in native language), and level (CEFR)

Keep meaning faithful to the source. Match complexity to the target level.
