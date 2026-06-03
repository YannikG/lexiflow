You are simplifying foreign-language reading text for a language learner.

Target language level: {target_level}
Target language: {target_language_label} ({target_language})
Native language (for glosses and explanations): {native_language_label} ({native_language})

Use vocabulary words from this list where they fit naturally:
{vocabulary_words}

Source text (translated variant):
{source_markdown}

Rewrite the source as simplified reading text at the target level. This is not a summary: keep the same topics and roughly similar length as the source. Shorten sentences and choose simpler words; do not compress the piece into a brief recap or outline.

The body must be regular prose for reading aloud or silently: markdown paragraphs separated by blank lines. Do not use bullet points, numbered lists, or dash lists. Do not use section headings except when the source already relied on them for structure.

Respond with JSON only. Fields:
- title: target-language document title (single line, no markdown heading)
- body: simplified markdown body without a top-level heading (paragraph prose only; no bullet or numbered lists)
- new_words: array of objects with:
  - lemma: dictionary form in {target_language_label} with correct target-language spelling (German nouns MUST be capitalized)
  - gloss: short meaning in {native_language_label} only
  - explanation: one short sentence in {native_language_label} describing how the word is used. Write directly, not meta phrasing such as "This word refers to..." or "This means...".
  - level: CEFR band (A1, A2, B1, B2, C1, C2)
  - category: one of noun, verb, adjective, adverb, pronoun, preposition, conjunction, interjection, other

Keep meaning faithful to the source. Match complexity to the target level. Preserve paragraph breaks from the source where reasonable.
