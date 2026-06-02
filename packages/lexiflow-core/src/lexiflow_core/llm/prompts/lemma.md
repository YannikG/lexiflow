You are helping a language learner add a word to their personal vocabulary.

Target language: {target_language_label} ({target_language})
Native language: {native_language_label} ({native_language})
Surface form from the reader: {surface_form}
Context sentence (optional): {context}

Write translation and explanation in {native_language_label} only. Do not use {target_language_label} in translation or explanation.

Return JSON with:
- lemma: dictionary form in {target_language_label}. Follow target-language spelling rules (German nouns MUST start with a capital letter; verbs, adjectives, and other non-nouns use lowercase).
- translation: short meaning in {native_language_label} only
- explanation: one short sentence in {native_language_label} describing how the word is used. Write directly (for example "Used when greeting someone"), not meta phrasing such as "This word refers to..." or "This means...".
- category: one of noun, verb, adjective, adverb, pronoun, preposition, conjunction, interjection, other
