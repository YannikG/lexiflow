# Domain language

Shared vocabulary for LexiFlow — also called **common language** in contributor docs. Use these terms in code, UI copy, PR Plans, and concept docs. [CONTEXT.md](CONTEXT.md) is the index only; do not duplicate glossary entries here.

> Roadmap: [docs/roadmap/README.md](docs/roadmap/README.md)

## About this document

**Domain language** — Agreed LexiFlow terminology: canonical names, definitions, and behavioral rules for product and architecture. Single source of truth for humans and agents. Not the user's **native language** or **target language**, and not **App UI language** (English chrome in v1).

**Common language** — Synonym for **domain language** (this document).

## Contents

| Section | Topics |
|---------|--------|
| [About](#about-this-document) | Domain language, common language |
| [Product](#product) | Release bar, distribution, packaging |
| [Platform](#platform) | Desktop shell, supported platforms |
| [User languages](#user-languages) | Native and target language, catalog |
| [Content hierarchy](#content-hierarchy) | Level, group, text, variants, reader |
| [Text processing](#text-processing) | Add text, jobs, simplify |
| [Embeddings](#embeddings) | Embedding model, vectors, search index |
| [UI](#ui) | Navigation, settings, search, theme |
| [Vocabulary](#vocabulary) | Study, difficulty, export |
| [Storage](#storage) | Data root, library, trash, backup |
| [LLM](#llm) | Providers, bootstrap, model lifecycle |
| [Engineering](#engineering) | Packages, contribution vocabulary |

## Product

**Language Learn App** — Desktop cross-platform tool for reading foreign texts with local LLM translation, level-aware simplification, and personal vocabulary tracking per target language. Product name: **LexiFlow**.

**Release bar** — v1 targets general users, not a personal prototype. Onboarding, settings UI, error states, and **core learning loop** should be complete and polished before release. Day-one usability means any learner can pick it up without manual configuration hacks.

**Core learning loop** — End-to-end v1 product path: add and read texts, translate, simplify at level, grow **Vocabulary**, then search and **find in texts**. **Release bar** requires this loop complete and polished, not a partial prototype.

**Platform scope** — Desktop first. No accounts, no live sync, no cloud dependency for core features. Mobile is out of scope for v1.

**Privacy** — Zero telemetry in v1. No analytics, crash reporting, or usage tracking. All data stays local on the user's machine.

**Local logging** — Rotating log files in the app data area. Settings: open logs folder, optional verbose debug mode (off by default). User may attach logs to GitHub issues manually; no automatic upload.

**Network requirement** — First install requires network to complete **model bootstrap** unless the user already has a configured local Ollama instance with the LLM. After required artifacts are cached, the app runs fully offline for reading, vocabulary, translate, simplify, and embed. Adding a new target language offline is blocked until its spaCy pack can download.

**Distribution** — GitHub Releases with CI-built artifacts. Open-source license: Apache 2.0. Product name: LexiFlow.

**Release process** — Pushing a version tag triggers CI to build platform installers and publish a GitHub Release. App version shown in **About dialog** matches the release tag.

**In-app updates** — On startup, app compares its version against the latest GitHub Release. If a newer version exists, notify the user with a link to download. No silent auto-install in v1.

**Packaging** — Single installable bundle contains UI and worker. End users do not install Python separately. Release artifact excludes model weights; models download on first use. UI spawns the worker from the same bundle.

**Installers** — macOS disk image, Windows installer package, Linux AppImage (x86_64). Unsigned in v1.

**App icon (v1)** — Simple placeholder motif. Professional rebrand post-launch.

**Release hygiene** — CI publishes checksums per artifact. README documents first-run model download, RAM requirements, and platform-specific install friction (Gatekeeper, SmartScreen).

**System requirements** — **About dialog** lists minimum RAM and disk for embedded model and cached artifacts. Onboarding warns if RAM is below recommended; user may continue anyway.

**Code signing roadmap** — v1 ships unsigned on macOS and Windows. Notarization and Windows signing are post-v1 if needed.

## Platform

**Desktop shell** — Native OS widgets. Not Electron, not in-app web UI.

**Supported platforms** — macOS (Apple Silicon and Intel), Windows 10+, Linux x86_64. No mobile, no web client in v1.

## User languages

**Native language** — User's first language. Used for explanations and auto-translation of foreign input. Chosen at onboarding; changeable in **settings**.

**Target language** — A language the user is learning. Display name and flag emoji. Each target language has its own **user language level**, **groups**, **texts**, and **Vocabulary**.

**Language catalog** — Built-in searchable list of roughly thirty predefined languages. Includes Ukrainian; excludes Russian. No free-form language code entry in v1.

**App UI language** — English only in v1. All application chrome is English; no localization framework in v1.

## Content hierarchy

**Level** — Fixed CEFR bands: A1, A2, B1, B2, C1, C2. **CEFR** is the Common European Framework of Reference. Ordered and immutable in v1. Simplify buckets "below" and "above" mean adjacent CEFR steps. **Level is not a folder or sidebar grouping**; it is a per-language proficiency setting and a parameter for simplification.

**User language level** — Per target language, the user's self-assessed CEFR level. Stored as **language metadata**, not on groups or texts. Set when adding a target language; changeable in language **settings** or at simplify time. Default for **simplify level picker**.

**Group** — Named collection within a target language (e.g. news, podcasts). User-chosen label. Holds **texts**. **Groups have no CEFR level.** User can create, rename, and delete empty groups from the **sidebar**. **Adding a text requires selecting or creating a group**; no default inbox. On disk, each group uses a **group folder slug** derived from the display label; **text metadata** and the **library index** store the display name.

**Group folder slug** — Filesystem-safe folder name for a **group** under a **language data root**. Derived from the user-facing group label (unsafe characters sanitized). Mapped to the display name in `{lang}/.data/groups.json`. **Sidebar** and **text metadata** use the display name, not the slug.

**Group rename** — User renames a group from the **sidebar**; app updates storage, **text metadata**, and **library index**. Non-empty groups cannot be deleted until empty.

**Sidebar** — Primary navigation in **Texts** mode: tree of **group** then **text** for the **active target language**. Shows **target-language title** per text. Supports group management, moving texts between groups, and **empty state** when no texts exist.

**Text** — A learning unit (e.g. newspaper excerpt). Stored on disk as markdown. **Variants:** native, translated, and zero or more simplified levels. Each text has a stable identifier in **text metadata**. **Texts have no single level field**; level appears only in simplified variants and vocabulary entries.

**Text slug** — Short folder name derived from title plus random suffix. Combined with **group** forms **text storage layout**. Collisions resolved by regenerating suffix.

**Text metadata** — Structured record per text: identifier, title, **group** (display name), source and native language, optional source URL, timestamps, and list of available **variants**. No level field on text. At create time the title is provisional until **plain translation** sets the **target-language title** (see **document title**). Source URL can be entered in **add text dialog**.

**Document title** — Each **variant** has a title in that variant's language. The title is the document's top heading, not a duplicate heading inside the body. LLM proposes title on cleanup and translate; user can edit in preview or **properties panel**. After **plain translation**, **text metadata** stores the **target-language title** for **sidebar** display.

**Text metadata editing** — User edits title, group, and source URL via **properties panel**. Drag-and-drop in **sidebar** moves text between **groups** only. Source URL opens in the system browser when clicked.

**Text variant** — One representation of a **text**: **native variant**, **translated variant**, or **simplified variant** at a specific CEFR level. Multiple simplified levels may coexist. Content is fixed after generation until the user explicitly regenerates it.

**Native variant** — Source or cleaned-up text in the **native language** (or declared input language).

**Translated variant** — **Plain translation** in the **target language**.

**Simplified variant** — Level-adjusted rewrite in the **target language** for a chosen CEFR level.

**Simplified variants** — User can generate and keep simplified versions at different CEFR levels simultaneously. **Re-simplify** targets the active simplified tab's level only.

**Reader tabs** — Core tabs: Native and Translated. If exactly one simplified level exists, show a flat Simplified tab with level label. If multiple simplified levels exist, show a Simplified menu listing each level. **Default tab on open:** **last viewed tab** per text; first open defaults to Translated.

**Read mode** — Default reader state: rendered markdown in the reading pane. No source editor visible.

**Edit mode** — Markdown source editor on the active tab. Save writes the variant; Cancel discards. Entered from **read mode** only.

**Last viewed tab** — Per text, persisted choice of Native, Translated, or a specific simplified level. Restored when reopening that text.

**Markdown editing** — User toggles **edit mode** on any variant. Does not trigger **re-translate** or **re-simplify**. Edits to **translated variant** enqueue background re-embedding.

**Simplify level picker** — On simplify, default to **user language level** for that target language. User may choose another CEFR level before running.

## Text processing

**Add text dialog** — Modal for creating a **text**. User picks **group** (required), optional source URL, **input tab** (Native or Target), and pastes content. **No automatic clipboard read.** Submit starts **staged generation**.

**Staged generation** — On add-text save, background steps run in order: **markdown cleanup**, ensure **native variant**, then **plain translation**. **Simplify is not part of this chain.** User may browse the library while work runs.

**Plain translation** — Full-complexity **target-language** rendering of the source. Distinct from **simplified variants**.

**Content fingerprint** — Normalized fingerprint of pasted body text. Used for **duplicate detection** when source URL is absent.

**Duplicate warning** — Shown when source URL or **content fingerprint** matches an existing text. User chooses open existing or save anyway.

**Large paste warning** — Soft guard at roughly fifty thousand characters in add-text: continue or cancel; no hard block in v1.

**Add text flow** — Umbrella for add-text UX: **add text dialog**, **staged generation**, duplicate and size warnings, and background enqueue rules. Simplify is manual after save.

**Markdown cleanup** — Format plus light cleanup on paste: readable structure, strip ads and navigation junk, preserve article wording verbatim. Output uses a single title heading at the top; body follows without a second top heading.

**Prompt templates** — Versioned LLM instruction documents for cleanup, translate, simplify, and lemma inference. Changes require review.

**LLM structured output** — Multi-field LLM responses (e.g. simplified body plus new word list) use a strict structured format validated before save.

**Re-translate** — Explicit user action to regenerate **plain translation** from the native or source variant.

**Re-simplify** — Explicit user action to regenerate a **simplified variant**. Uses vocabulary vectors at time of run. Does not auto-update when vocabulary changes later.

**Background job** — Unit of async work: cleanup, translate, simplify, embed, model download, spaCy download, lemma inference. User-visible types include translate, simplify, embed, and download jobs.

**LLM job UX** — Long-running translate, simplify, and cleanup jobs run in the background. User can continue browsing. Status indicator shows active jobs with cancel support. Notification on complete or fail; partial outputs discarded on cancel. **One LLM job at a time**; additional requests queue globally.

**Job queue** — Persisted work queue surviving crash and shutdown. **Job states:** Pending, Running, Completed, Failed, Cancelled. On startup, interrupted Running jobs return to Pending and auto-run; Pending and Failed remain; Cancelled stays terminal. One failure must not crash the app. Manual retry from **jobs panel**. **One LLM job at a time** globally.

**Job cancelled state** — Terminal state when user cancels a job. Partial output discarded. Not retried automatically.

**Restart worker** — Recovery after worker crash. UI stays open; queue preserved. User confirms to spawn a new worker and resume Pending jobs.

**Process architecture** — Separate UI process and worker process. UI has no heavy ML imports. Worker consumes queue, runs LLM and embeddings. Worker spawns lazily on first AI job. Worker crash shows restart dialog without closing UI.

**Worker idle lifecycle** — After five minutes with no running or queued jobs, worker shuts down and unloads models from memory. Manual model-off forces immediate unload. Next job respawns worker. Ollama server lifecycle remains external.

**Shutdown with active jobs** — On quit while jobs run or queue, dialog shows counts. **Wait** finishes current work then exits cleanly. **Quit anyway** stops worker immediately; running job becomes Pending for next launch.

**Job history UI** — **Status bar** entry for active queue; opens **jobs panel** with Pending, Running, Failed, and recently Completed jobs (last twenty kept). Error details; Retry and Cancel where applicable. Failed jobs are not auto-retried.

**Jobs panel** — Full list and controls for **background jobs**.

**Worker status** — **Status bar** shows worker state (idle, running, loading models, offline), active job count, and **LLM toggle**.

**Single instance** — Only one app instance per user session. Second launch offers open existing window or close. Prevents database and file contention. **Stale single-instance recovery** clears ghost locks after crash if needed.

**Input tab** — In **add text dialog**, declares paste source language: Native tab for first language, Target tab for language being learned. The other variant is produced by translation.

**Language auto-detect** — On paste, app detects language. If it conflicts with selected **input tab**, app silently corrects routing without blocking the user.

**Simplify word mix** — Simplification pulls vocabulary by semantic similarity to source text, then fills level buckets from that ranked list. **Easy** words are deprioritized in ranking but still used when they fit naturally.

**Level bucket quotas** — While simplifying at level L: roughly thirty percent from vocabulary at L, twenty percent one level below, ten percent new words one level above. Remainder is general target-language prose. If buckets underfill, use available matches and let the LLM fill gaps.

**New word suggestions** — After simplify, curated word list (lemma, gloss, suggested level) shown in **new words panel** for one-click add to **Vocabulary**. Post-filter removes existing vocabulary, duplicates, and junk.

**New words panel** — UI below the Simplified reader listing filtered **new word suggestions** with add actions.

**Reader add word** — Highlight text in reading pane, then add to **Vocabulary**. Available on target-language tabs only. Dialog prefills surface form; LLM proposes lemma, translation, explanation, and level. User confirms before save.

## Embeddings

**Embedding model** — Local MiniLM-class model, separate from the LLM. Same model for vocabulary word vectors and translated-text vectors.

**Embedding queue** — Background embedding when vocabulary or translated text changes. UI does not block.

**Vector storage** — Per-language vector store for similarity search. Vocabulary vectors and text vectors are stored separately.

**Library index** — Fast metadata cache for **sidebar** and search. Full-text search over titles and all **variants** in the active target language. Prefix and case-insensitive match first; fuzzy fallback if no hits. Same search behavior in **Vocabulary** mode. Updated on app writes; **rebuild library index** rescans disk after external edits.

**Rebuild library index** — Settings action to rescan all text files and metadata into **library index**.

**Schema migration** — Versioned database schema upgrades applied automatically on startup.

## UI

**Application shell** — Main window: toolbar, **sidebar**, content area, **status bar**, **navigation modes**.

**Settings** — Post-onboarding configuration: languages, Ollama, Hugging Face token, data root, theme, appearance, models, backup, trash, logs, **about dialog**, **reset app**. Distinct from **onboarding flow**.

**About dialog** — App version, **system requirements**, open logs, project and license info.

**Properties panel** — Edit text metadata and variant titles. Title changes sync to active variant and **text metadata**.

**Navigation modes** — **Texts** and **Vocabulary**. Texts: **sidebar** tree plus reader. Vocabulary: searchable list for active target language.

**Empty state** — Placeholder when a view has no content, with guidance and primary action.

**Markdown reader** — Native markdown rendering. Reading-first: headings, bold, italic, tables. User-adjustable font size in appearance **settings**.

**Theme** — System (default), Light, or Dark.

**Active target language** — Toolbar switcher shows flag, name, and **user language level**. **Sidebar**, library, and **Vocabulary** scope to this language only.

**Keyboard shortcuts (v1)** — Minimal set: search, new text, cancel active job. New text opens **add text dialog** empty; user pastes manually. **No automatic clipboard read.** Search opens **global search UI** with last query prefilled.

**Global search UI** — Toolbar and **sidebar** search open the same spotlight-style overlay with keyboard navigation. Shows **target-language title** and snippet per hit. Fresh query each open. **Search hit navigation** opens text on the variant where the match occurred when known.

## Vocabulary

**Vocabulary** — Per-target-language personal word collection (not "Wörterbuch"). Each entry tracks lemma, translation, native-language explanation, **level when learned**, and **difficulty rating**. Sort: recently added (default), alphabetical, level when learned, difficulty.

**Lemma** — Dictionary form of a word. Canonical dedup key. Resolved via **lemma resolution**.

**Surface form** — Exact word form seen in text. Optional; does not affect dedup.

**Level when learned** — Historical CEFR band when the word entered **Vocabulary**. Defaults: from simplified tab → active simplified level; from translated tab or highlight-add → **user language level**. User may override in add dialog.

**Vocabulary entry** — One lemma per target language with translation, explanation, **level when learned**, **difficulty rating**, optional **surface form**, stable identifier, optional import source (local or imported). No per-text backlink list. Lemma change triggers re-embed. Delete requires confirmation, then brief **delete undo window** to restore. **Duplicate lemma on add** is rejected in v1.

**Manual add word** — Create vocabulary without highlighting text; user enters fields manually.

**Difficulty rating** — Current familiarity: hard, well, fluent, easy. Independent of **level when learned**. User **promotes** via **promote fluency** after card reveal. At easy, word is **mastered**. Easy words deprioritized in simplify retrieval. Default on add: hard.

**Mastered** — Vocabulary at difficulty easy; no further promotion in Study.

**Promote fluency** — Study action (Got it) after reveal; steps difficulty up one notch.

**Vocabulary study** — **Study** (default) and **Browse**. Study: shuffled flashcards; translation hidden until flip; **promote fluency** only after reveal. Browse: full fields for search, edit, export; direct difficulty edit.

**Vocabulary import** — Merge exported vocabulary into active target language. Duplicate lemmas skipped by default; optional overwrite.

**Vocabulary export** — Handoff bundle or database export for another user. Pairs with **vocabulary import**. No server sync in v1.

**Find in texts** — Locate a word across all texts in the active target language. Same search rules as **library index**. Opens text at match when possible.

**Lemma resolution** — spaCy when language pack installed; otherwise LLM inference. Same for highlight-add, **manual add word**, and **new word suggestions**.

**spaCy language packs** — Downloaded per target language when added. All model and pack downloads go through Hugging Face in v1.

## Storage

**Data root** — User content root (default under home directory). Contains per-language folders, runtime app data (`.app/`), and trash. Overridable in **global settings**; portable via **library backup** zip.

**App data name** — LexiFlow. Default folder name for user content.

**App config directory** — Machine-local directory resolved at startup before **data root**. Holds `settings.toml` (**global settings**). Uses OS conventions (Application Support on macOS, AppData on Windows, XDG config on Linux).

**Global settings** — Machine-local preferences in `settings.toml` under **app config directory**: native language, Ollama endpoint, **data root** pointer, LLM toggle, onboarding flags, theme. Read before opening the user library so **data root** override has no bootstrap chicken-and-egg.

**Library backup** — Export entire **data root** as zip. Does not include **global settings** (machine-local). Restore to new folder or replace current library with **strong confirmation**.

**Language metadata** — Per target language: **user language level** and language-specific settings.

**Strong confirmation** — Destructive actions require typing a confirmation phrase (language name, reset phrase, etc.).

**Remove target language** — Optional vocabulary export first, then wipe entire language folder (texts, groups, databases, metadata). **Strong confirmation** required.

**Trash** — Deleted texts moved to trash area; restore or empty from **settings**. Vocabulary entries are never deleted when a text is removed.

**Language data root** — Per target language folder on disk. Contains group and text content plus per-language databases. CEFR level is not encoded in folder paths; **sidebar** tree comes from metadata.

**Text storage layout** — Per text: folder under group with metadata file and markdown **variants**. Level exists only in simplified variant files.

**External markdown import** — Bulk folder import out of scope v1. Nice-to-have: single markdown file drop to create text in chosen **group**.

**Vocabulary database** — Per target language store for vocabulary entries and word embeddings. Intended shareable unit.

**Text vector database** — Per target language store for text embeddings. Not included in **vocabulary export**.

## LLM

**LLM provider** — Pluggable backend for translate, simplify, and cleanup. Optional **Ollama endpoint**. No runtime lock-in.

**Provider mode** — Embedded default; Ollama overrides when configured. Same prompts for both paths.

**Embedded model** — Default in-app model: Gemma 4 E2B, run locally. Loaded on demand, unloaded when idle.

**Ollama endpoint** — Optional external LLM server. Replaces embedded for all LLM tasks when set. App does not manage Ollama lifecycle.

**Model bootstrap** — First-use download of LLM and embedding models from Hugging Face with progress UI. Cached locally. **Manual weight import** available as offline LLM fallback.

**Bootstrap network retry** — On download failure during onboarding, wizard shows error with Retry; does not skip the gate silently.

**Model pinning** — Shipped manifest pins exact model revisions. Settings can check for updates. No floating latest-only pins in v1. Hugging Face is the single download source for models and spaCy packs in v1.

**Onboarding LLM setup** — Detect local Ollama; offer one-click setup or embedded path with size and RAM expectations. Wizard blocks main UI until bootstrap completes (embedding model always; LLM unless Ollama configured).

**Onboarding flow** — Welcome and RAM check, native language, LLM mode (Hugging Face download, Ollama, or manual import), model bootstrap when required, add first target language with level (required), then main UI. First launch only; later via **settings**. `onboarding_complete` in **global settings** is set only after the full wizard finishes (including LLM setup and **model bootstrap** where applicable).

**Reset app** — Wipes all local data including cached models and re-runs **onboarding flow**. **Strong confirmation** required.

**Gemma Terms of Use** — Embedded Gemma weights subject to Google's Gemma license in addition to app Apache 2.0. Accepted via Hugging Face download.

**LLM toggle** — Force embedded model off or allow auto-load from **status bar** or **settings**.

**Model updates** — User-initiated check for newer pinned revisions. No silent auto-upgrade in v1.

**Hugging Face token** — Optional token in **settings** for rate limits and gated repos. Anonymous download works without token.

**Ollama and embeddings** — Until [phase 10b](docs/roadmap/phases/phase-10b-ollama-embeddings/README.md) ([ADR 0005](docs/adr/0005-ollama-embedding-provider-deferred.md)): Ollama replaces embedded LLM only; embedding model always runs in-app from Hugging Face. After 10b: when **Ollama endpoint** is set, embeddings may use Ollama HTTP instead of MiniLM (pinned embed model; same vector contract as phase 10).

**Embedded model lifecycle** — Manual on/off; auto-unload after idle when on. Ollama path: HTTP client only, no in-app model load.

**Worker-linked model lifecycle** — Embedded LLM and embedding model load in worker. **Worker idle lifecycle** unloads both. Manual off forces immediate shutdown.

## Engineering

Vocabulary for repo structure and contribution. Not user-facing UI copy.

**lexiflow-core** — Domain logic, storage, jobs, LLM and embedding abstractions. No UI framework. Headless-testable.

**lexiflow-ui** — Application shell, onboarding, worker supervision, single-instance guard. Depends on core public APIs only.

**lexiflow-worker** — Worker entrypoint delegating to core job runner. Same install bundle as UI.

**PR Plan** — Mandatory PR description or first comment: features, architecture impact, documentation delivered.

**Concept doc** — Stable capability documentation per package. Behavior and rules, not code layout.

**ADR** — Architecture Decision Record for irreversible choices. Supersede with new record; do not silently rewrite history.

**TDD vertical slice** — One failing test, minimal implementation, refactor when green. Mandatory per development phase.

**CI quality gates** — Required automated checks on every pull request. No merge on failure.

## Term index

Canonical terms (alphabetical):

- ADR
- About dialog
- Active target language
- Add text dialog
- Add text flow
- App UI language
- App config directory
- App data name
- App icon (v1)
- Application shell
- Background job
- Bootstrap network retry
- CI quality gates
- Code signing roadmap
- Common language
- Concept doc
- Content fingerprint
- Core learning loop
- Data root
- Desktop shell
- Difficulty rating
- Distribution
- Document title
- Domain language
- Duplicate warning
- Edit mode
- Embedded model
- Embedded model lifecycle
- Embedding model
- Embedding queue
- Empty state
- External markdown import
- Find in texts
- Gemma Terms of Use
- Global search UI
- Global settings
- Group
- Group folder slug
- Group rename
- Hugging Face token
- In-app updates
- Input tab
- Installers
- Job cancelled state
- Job history UI
- Job queue
- Jobs panel
- Keyboard shortcuts (v1)
- LLM job UX
- LLM provider
- LLM structured output
- LLM toggle
- Language Learn App
- Language auto-detect
- Language catalog
- Language data root
- Language metadata
- Large paste warning
- Last viewed tab
- Lemma
- Lemma resolution
- Level
- Level bucket quotas
- Level when learned
- Library backup
- Library index
- Local logging
- Manual add word
- Markdown cleanup
- Markdown editing
- Markdown reader
- Mastered
- Model bootstrap
- Model pinning
- Model updates
- Native language
- Native variant
- Navigation modes
- Network requirement
- New word suggestions
- New words panel
- Ollama and embeddings
- Ollama endpoint
- Onboarding LLM setup
- Onboarding flow
- PR Plan
- Packaging
- Plain translation
- Platform scope
- Privacy
- Process architecture
- Promote fluency
- Prompt templates
- Properties panel
- Provider mode
- Re-simplify
- Re-translate
- Read mode
- Reader add word
- Reader tabs
- Rebuild library index
- Release bar
- Release hygiene
- Release process
- Remove target language
- Reset app
- Restart worker
- Schema migration
- Settings
- Shutdown with active jobs
- Sidebar
- Simplified variant
- Simplified variants
- Simplify level picker
- Simplify word mix
- Single instance
- Staged generation
- Strong confirmation
- Supported platforms
- Surface form
- System requirements
- TDD vertical slice
- Target language
- Text
- Text metadata
- Text metadata editing
- Text slug
- Text storage layout
- Text variant
- Text vector database
- Theme
- Translated variant
- Trash
- User language level
- Vector storage
- Vocabulary
- Vocabulary database
- Vocabulary entry
- Vocabulary export
- Vocabulary import
- Vocabulary study
- Worker idle lifecycle
- Worker status
- Worker-linked model lifecycle
- lexiflow-core
- lexiflow-ui
- lexiflow-worker
- spaCy language packs
