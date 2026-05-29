# Agent configuration (portable)

Vendor-neutral agent config for LexiFlow. **Commit `.agents/` and root `AGENTS.md`.** No `.cursor/` folder in this repo.

| Path | Purpose |
|------|---------|
| [mcp.json](mcp.json) | Canonical MCP servers: **context7**, **semble** |
| [rules/lexiflow.md](rules/lexiflow.md) | Project guardrails |
| [rules/code-discovery.md](rules/code-discovery.md) | **Mandatory** semble + context7 workflow |
| [agents/semble-search.md](agents/semble-search.md) | Semble search sub-agent profile |

## How agents find this

| What | How |
|------|-----|
| **Instructions** | [AGENTS.md](../AGENTS.md) at repo root (Cursor, Claude Code, Copilot, and others read it) |
| **Rules & policy** | Linked from `AGENTS.md` → `.agents/rules/` |
| **MCP server definitions** | [mcp.json](mcp.json) — canonical JSON; each tool loads it from its own path (see below) |

Cursor does **not** need a `.cursor/` directory for instructions: it uses `AGENTS.md` plus the rules you link from there.

## MCP (tool-specific paths)

Cursor does **not** auto-load `.agents/mcp.json`. It only reads MCP from:

- **Global:** `~/.cursor/mcp.json` (all projects), or
- **Project:** `.cursor/mcp.json` (we do **not** commit this; use global or copy once)

Copy the `mcpServers` block from [mcp.json](mcp.json) into your global config, or merge with existing servers. Restart Cursor.

| Tool | MCP config path |
|------|-----------------|
| Cursor | `~/.cursor/mcp.json` (recommended) or `.cursor/mcp.json` (local, optional) |
| Claude Code | `.claude/mcp.json` or user config |
| VS Code / Copilot | `.vscode/mcp.json` or `.github/mcp.json` |

Setup: [docs/guides/mcp-setup.md](../docs/guides/mcp-setup.md).

**Agents must** follow [rules/code-discovery.md](rules/code-discovery.md) regardless of editor.
