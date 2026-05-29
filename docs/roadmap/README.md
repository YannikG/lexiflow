# LexiFlow roadmap

**Bootstrap:** Phase 00 commits **directly to `main`** (governance only, no PR).

**Rule (v1, phase 01+):** one phase = one GitHub Issue = one PR = one merge to `main`.

Until v1 ships, each feature phase has a **GitHub Issue** (minimal body: link + blockers) and a **phase README** (full spec). Issues use **blocked by** for order (01 → 15). After [phase 16](phases/phase-16-issue-migration-cleanup/), specs move into closed issues and phase folders leave the repo.

See [agent workflow](../guides/agent-workflow.md).

## Phase diagram

```mermaid
flowchart TB
  P00[Phase 00 Repo and docs governance]
  P01[Phase 01 Foundation]
  P02[Phase 02 Core paths and settings]
  P03[Phase 03 Library index and texts]
  P04[Phase 04 Job queue and worker]
  P05[Phase 05 UI shell]
  P06[Phase 06 Onboarding and languages]
  P07[Phase 07 Model bootstrap HF]
  P08[Phase 08 Add text and translate]
  P09[Phase 09 Reader and markdown]
  P10[Phase 10 Embeddings and sqlite-vec]
  P11[Phase 11 Simplify and new words]
  P12[Phase 12 Vocabulary]
  P13[Phase 13 Search and data management]
  P14[Phase 14 Settings jobs and polish]
  P15[Phase 15 Packaging and release]

  P00 --> P01 --> P02 --> P03 --> P04 --> P05
  P05 --> P06 --> P07 --> P08 --> P09
  P09 --> P10 --> P11 --> P12 --> P13
  P13 --> P14 --> P15
  P15 --> P16[Phase 16 Issue migration cleanup]
```

## Phase index

| Phase | Folder | Outcome (what you have after merge) |
|-------|--------|-------------------------------------|
| 00 | [phase-00-repo-governance](phases/phase-00-repo-governance/) | GitHub repo, AGENTS/CONTRIBUTING, CI skeleton, PR Plan rule |
| 01 | [phase-01-foundation](phases/phase-01-foundation/) | uv monorepo, hello window, CI green |
| 02 | [phase-02-core-paths-settings](phases/phase-02-core-paths-settings/) | **Data root**, **global settings**, **schema migration** |
| 03 | [phase-03-library-and-texts](phases/phase-03-library-and-texts/) | **Groups**, **text storage layout**, **library index** |
| 04 | [phase-04-job-queue-worker](phases/phase-04-job-queue-worker/) | **Job queue**, worker, **background jobs** |
| 05 | [phase-05-ui-shell](phases/phase-05-ui-shell/) | **Application shell**, **sidebar**, **single instance** |
| 06 | [phase-06-onboarding-languages](phases/phase-06-onboarding-languages/) | **Onboarding flow**, **language catalog** |
| 07 | [phase-07-model-bootstrap](phases/phase-07-model-bootstrap/) | **Model bootstrap**, **model pinning** |
| 08 | [phase-08-add-text-translate](phases/phase-08-add-text-translate/) | **Add text flow**, **staged generation** |
| 09 | [phase-09-reader-markdown](phases/phase-09-reader-markdown/) | **Reader tabs**, **read mode**, **edit mode** |
| 10 | [phase-10-embeddings](phases/phase-10-embeddings/) | **Vector storage**, **embedding queue** |
| 11 | [phase-11-simplify](phases/phase-11-simplify/) | **Simplify word mix**, **new word suggestions** |
| 12 | [phase-12-vocabulary](phases/phase-12-vocabulary/) | **Vocabulary study**, export/import |
| 13 | [phase-13-search-data](phases/phase-13-search-data/) | **Global search UI**, **trash**, **library backup** |
| 14 | [phase-14-settings-polish](phases/phase-14-settings-polish/) | **Jobs panel**, **settings**, **reset app** |
| 15 | [phase-15-packaging-release](phases/phase-15-packaging-release/) | **Packaging**, **installers**, **release process** |
| 16 | [phase-16-issue-migration-cleanup](phases/phase-16-issue-migration-cleanup/) | Specs copied into closed issues; roadmap phase folders removed; post-v1 issue-only workflow |

## GitHub issues (v1, phases 01–15)

Create after phase 00 is on `main`, from [phase issue template](../../.github/ISSUE_TEMPLATE/phase.yml) (or `phase.md`). No issue for phase 00.

Create labels **`phase`** and **`v1`** on GitHub before using the form (or add them manually per issue).

Each issue:

- **Title:** `Phase XX: <name>`
- **Body:** link to `docs/roadmap/phases/phase-XX-.../README.md` only
- **Blocked by:** previous phase issue (phase 01 has no blocker)

Enable branch protection on `main` before merging the first feature PR (phase 01).

## References

- [Context map](../../CONTEXT.md)
- [Domain language (common-language.md)](../../common-language.md)
- [Architecture overview](../architecture/overview.md)
- [ADRs](../adr/)
- [Agent workflow](../guides/agent-workflow.md)
- [Documentation strategy](../guides/documentation-strategy.md)
- [PR plan template](../guides/pr-plan-template.md)

## v1 scope reminder

Public-ready desktop app: full learning loop (texts → translate → simplify → vocabulary → search). Not a minimal throwaway prototype. See common-language **Release bar**.
