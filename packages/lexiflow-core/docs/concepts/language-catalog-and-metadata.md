# Language catalog and metadata

LexiFlow ships a built-in **language catalog** and stores per-target-language **language metadata** on disk.

## Catalog

- Module: `lexiflow_core.languages.catalog`
- `list_languages()` returns roughly thirty predefined languages (ISO 639-1 code, display name, flag emoji).
- `get_language(iso)` returns one entry or raises `KeyError`.
- Ukrainian (`uk`) is included; Russian (`ru`) is excluded (v1 product rule).

The catalog is static data in core; UI filters it for search but does not allow free-form language codes.

## User language level

`CEFRLevel` is the fixed A1–C2 enum used for **user language level** per target language.

## Language metadata file

Each target language folder has metadata at `{data_root}/{iso}/.data/language.json`:

```json
{
  "user_level": "A2"
}
```

CEFR level is not encoded in folder paths. **Level** on groups or texts is forbidden; level lives here and in simplified variants only.

## LanguageStore

`LanguageStore(data_root)` commands:

| Method | Role |
|--------|------|
| `add_target(iso, level)` | Create `.data/` and write `language.json` |
| `get_user_level(iso)` | Read stored CEFR level |
| `list_targets()` | List ISO codes with metadata on disk |

`add_target` validates against the catalog and rejects duplicates. It does not enqueue jobs; use `add_target_with_spacy_download()` or `complete_language_onboarding()` in `setup.py` for first-run setup with rollback on failure.

## spaCy download job

Adding a target language from onboarding enqueues `JobType.DOWNLOAD_SPACY` with payload `{"iso": "<code>"}`. The worker handler is wired in a later phase; persistence is established in phase 06.

See [common-language.md](../../../../common-language.md): **Language catalog**, **Language metadata**, **User language level**, **spaCy language packs**.
