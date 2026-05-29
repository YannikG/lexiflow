# Code discovery (mandatory)

Agents **must** use MCP tools before exploring the codebase or library APIs from memory. Wire servers from [`.agents/mcp.json`](../mcp.json) ([setup](../../docs/guides/mcp-setup.md)).

## This repository (LexiFlow)

**Do not** start with Grep, Glob, or reading whole files for exploratory questions.

| Step | Tool | Action |
|------|------|--------|
| 1 | **semble** `search` | Natural-language or symbol query; `repo` = workspace root absolute path |
| 2 | **semble** `find_related` | After a strong hit; pass `file_path` + `line` from the result |
| 3 | Read | Only paths Semble surfaced; small ranges, not full-file dumps |
| 4 | Grep | **Only** exact literals, import paths, or after Semble found nothing useful |

Delegate broad exploration to the **semble-search** sub-agent ([`../agents/semble-search.md`](../agents/semble-search.md)) when the harness supports it.

### Shell fallback (MCP unavailable)

```bash
semble search "<query>" "<repo-root>"
semble find-related <file> <line> "<repo-root>"
```

If `semble` is missing: `uvx --from "semble[mcp]" semble search "..." .`

## External libraries

**Do not** guess APIs for dependencies (PySide6, uv, pytest, pytest-qt, sqlite, etc.).

| Step | Tool | Action |
|------|------|--------|
| 1 | **context7** `resolve-library-id` | Library name + what you need |
| 2 | **context7** `query-docs` | Specific task (setup, API, examples) |
| 3 | Implement | Match documented signatures and patterns |

Max **3** `query-docs` calls per question; then implement or ask the user.

## Exceptions (rare)

- Editing a file you **already** have open from the current task with a one-line obvious fix.
- User gave an **exact** file path and line to change.

State in the PR **Plan** if you skipped tools and why.

## PR checklist

Feature PRs must confirm in the Plan or PR checklist:

- [ ] Used **semble** for repo exploration (or documented exception)
- [ ] Used **context7** for new/changed third-party library usage (or documented exception)
