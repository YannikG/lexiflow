# Vocabulary

Per-target-language personal word collection stored in `vocabulary.sqlite` under `{data_root}/{language}/.data/`.

## Entry model

Each entry has lemma (primary key), **word category**, translation, explanation, **level when learned**, **difficulty rating**, and timestamps.

Lemma spelling follows target-language rules: German nouns are capitalized; other categories are lowercased. LLM prompts require translation and explanation in the user's **native language** only.

- **Duplicate lemma on add** is rejected in v1.
- Default difficulty on add: **hard**.

## Study and Browse

| Mode | Behavior |
|------|----------|
| **Study** | Shuffled flashcards; translation hidden until **Reveal**; **Got it** (**promote fluency**) enabled only after reveal; hidden at **mastered** (easy). |
| **Browse** | Full list with search, sort, inline difficulty edit, delete with confirmation and trash archive. |

Deleted entries are archived under `{data_root}/.trash/vocabulary/{language_code}/` for restore from **Library → Trash**. Restore queues a vocabulary embed job.

## Export and import

**Vocabulary export** writes a zip with `manifest.json` and `vocabulary.sqlite` (entries and word embeddings when present).

**Vocabulary import** merges into the active target language: skip duplicates by default, or overwrite translation and related fields.

## Lemma resolution

**Reader add word** and **manual add word** resolve the dictionary form via spaCy when a pack exists under `{data_root}/.app/spacy/{language_code}/`, otherwise a background `lemma` job runs the `lemma.md` prompt. Resolved **word category** is applied when the add dialog still has the default category.

## Word detail

Double-click a row in the vocabulary browse table or reader word panel to open a read-only modal with every stored field (`word_detail_dialog.py`).

## Public API

| Module | Role |
|--------|------|
| `lexiflow_core.vocabulary.store` | CRUD, promote, delete/restore |
| `lexiflow_core.vocabulary.export` | `export_vocabulary_zip` |
| `lexiflow_core.vocabulary.import_bundle` | `import_vocabulary_zip` |
| `lexiflow_core.vocabulary.lemma_form` | `normalize_lemma`, `parse_word_category` |
| `lexiflow_core.vocabulary.lemma_resolution` | spaCy sync path |
| `lexiflow_core.vocabulary.explanation_text` | `normalize_usage_explanation` |
| `lexiflow_core.jobs.lemma_queue` | `enqueue_lemma_job`, `find_active_lemma_job`, `cancel_lemma_job` |
| `lexiflow_core.languages.remove_target` | Wipe language folder |

## Package boundary

Vocabulary logic lives in **lexiflow-core**. **lexiflow-ui** provides Study/Browse widgets and the add-word dialog.
