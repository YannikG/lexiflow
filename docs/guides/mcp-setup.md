# MCP setup

LexiFlow **requires** agents to use **semble** (this repo) and **context7** (libraries). Policy: [`.agents/rules/code-discovery.md`](../../.agents/rules/code-discovery.md).

Canonical server definitions: [`.agents/mcp.json`](../../.agents/mcp.json). **No `.cursor/` folder in the repo.**

## Cursor (no project `.cursor/` required)

1. Cursor reads **[AGENTS.md](../../AGENTS.md)** and linked `.agents/rules/` for behavior.
2. For MCP tools, merge [`.agents/mcp.json`](../../.agents/mcp.json) into **`~/.cursor/mcp.json`** (global). Restart Cursor.
3. If semble and context7 are already in your global config, you are done.

Cursor does not discover `.agents/mcp.json` by path; only `AGENTS.md` + your global/project MCP file.

## Prerequisites

| Server | Requires |
|--------|----------|
| **context7** | Optional `CONTEXT7_API_KEY` in your environment ([free key](https://context7.com/dashboard)) |
| **semble** | [uv](https://docs.astral.sh/uv/) (`uvx` on PATH). Phase 01 adds uv to the repo workflow. |

## One-time setup (your machine)

### Context7

Add to `~/.zshrc` (or equivalent):

```bash
export CONTEXT7_API_KEY="your-key-here"
```

Restart your agent client so `${env:CONTEXT7_API_KEY}` resolves. Works without a key at lower rate limits.

### Semble

After [uv](https://docs.astral.sh/uv/getting-started/installation/) is installed:

```bash
uvx --from "semble[mcp]" semble --help
```

If `uvx` is unavailable, install the CLI and use `"command": "semble"`, `"args": ["--content", "all"]` in your MCP config.

### Other tools

See the table in [`.agents/README.md`](../../.agents/README.md). Copy `mcpServers` from `.agents/mcp.json` into that tool's config path.

## Agent usage

| Tool | When |
|------|------|
| **context7** `resolve-library-id` + `query-docs` | PySide6, uv, pytest, sqlite-vec, library APIs |
| **semble** `search` | Explore this repo before grep; set `repo` to workspace root |
| **semble** `find_related` | Follow-up after a strong search hit |

See [AGENTS.md](../../AGENTS.md) and [`.agents/agents/semble-search.md`](../../.agents/agents/semble-search.md).

## References

- [Context7 docs](https://context7.com/docs)
- [Semble](https://github.com/MinishLab/semble)
