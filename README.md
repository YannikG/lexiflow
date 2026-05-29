# LexiFlow

Desktop app for learning languages by reading real texts: local LLM translate and simplify, personal vocabulary, markdown on disk.

## Quick start

Requires [uv](https://docs.astral.sh/uv/) and Python 3.12+.

```bash
git clone https://github.com/YannikG/lexiflow.git
cd lexiflow
uv sync
uv run python -m lexiflow_ui
```

Close the window to quit.

## Development

```bash
uv sync
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy packages/lexiflow-core
pre-commit run --all-files
```

## Status

Phase 01 foundation: three-package uv monorepo, hello window, CI quality gates. See [roadmap](docs/roadmap/README.md).

## Contributing

- [CONTRIBUTING.md](CONTRIBUTING.md)
- [Roadmap](docs/roadmap/README.md)
- [Agent workflow](docs/guides/agent-workflow.md)

## Documentation

| Document | Purpose |
|----------|---------|
| [CONTEXT.md](CONTEXT.md) | Project index — start here |
| [common-language.md](common-language.md) | Domain language (canonical glossary) |
| [AGENTS.md](AGENTS.md) | Instructions for AI agents |
| [docs/architecture/overview.md](docs/architecture/overview.md) | Processes, packages, data layout |

## License

Apache License 2.0 — see [LICENSE](LICENSE).
