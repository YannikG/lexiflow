# LexiFlow

Desktop app for learning languages by reading real texts: local LLM translate and simplify, personal vocabulary, markdown on disk.

## Install (end users)

Download the latest release for your platform from [GitHub Releases](https://github.com/YannikG/lexiflow/releases):

| Platform | Artifact |
|----------|----------|
| macOS (Apple Silicon) | `.dmg` |
| Windows 10+ (x64) | `.msi` |
| Windows 10+ (ARM64) | `-arm64.msi` |
| Linux x86_64 | `.AppImage` |

Verify downloads with the `checksums.txt` SHA256 file attached to each release.

**First run:** an internet connection may be required for Hugging Face model weights (native LLM and embeddings via bundled llama-server, spaCy when adding a language). Model weights are not included in the installer. See [model bootstrap](packages/lexiflow-core/docs/concepts/model-bootstrap.md).

**System requirements:** see **About LexiFlow** in the app for RAM and disk guidance. Recommended: 16 GB RAM for the native LLM path.

### Platform notes (unsigned v1)

- **macOS:** Gatekeeper may block the app because it is not notarized. Right-click → Open, or allow in **System Settings → Privacy & Security**.
- **Windows:** SmartScreen may warn on first launch because the installer is not Authenticode-signed. Choose **More info → Run anyway** if you trust the download and checksum.
- **Linux:** AppImage may need `chmod +x`. Some distros require `libfuse2` for AppImage.

## Quick start (developers)

Requires [uv](https://docs.astral.sh/uv/) and Python 3.12+.

```bash
git clone https://github.com/YannikG/lexiflow.git
cd lexiflow
uv sync
uv run python -m lexiflow_ui
```

Close the window to quit.

**First run:** an internet connection may be required on first use (LLM and embeddings via llama-server from Hugging Face unless you configure Ollama for chat). See [model bootstrap](packages/lexiflow-core/docs/concepts/model-bootstrap.md).

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

Phase 15 packaging: PyInstaller bundle, platform installers, tag-triggered releases. See [roadmap](docs/roadmap/README.md).

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
| [packaging.md](packages/lexiflow-ui/docs/concepts/packaging.md) | Installers and release workflow |

## License

Apache License 2.0 — see [LICENSE](LICENSE).
