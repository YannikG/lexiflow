---
name: semble-search
description: Mandatory first step for exploring LexiFlow code. Use before Grep, Glob, or wide file reads. Delegate semantic questions and "where is X" to this agent.
---

You **must** use Semble before grep or blind file reads in this repo.

## MCP (preferred)

Server: **semble**

| Tool | When |
|------|------|
| `search` | First step for any exploratory or how-does-this-work question |
| `find_related` | After a good `search` hit; pass that `file_path` and `line` |

Always set `repo` to the LexiFlow workspace root (absolute path).

## CLI fallback

```bash
semble search "job queue persistence" .
semble search "FakeLLM" . --top-k 10
semble find-related packages/lexiflow-core/jobs.py 42 .
```

If `semble` is not on `$PATH`: `uvx --from "semble[mcp]" semble search "..." .`

## Workflow

1. `semble search` (or MCP equivalent).
2. `find_related` if adjacent code matters.
3. Read **only** files or line ranges Semble identified.
4. Grep **only** for exact strings or to confirm a single literal.

## Do not

- Grep the tree first for semantic questions.
- Read large files without Semble narrowing scope.
- Skip Semble because the repo looks small; index includes docs (`--content all`).

Full policy: [`.agents/rules/code-discovery.md`](../rules/code-discovery.md).
