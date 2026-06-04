# Packaging and release

## What this is

**Packaging** is the single installable bundle that contains the LexiFlow UI and worker. End users do not install Python separately. The UI spawns the worker from the same executable using the `--worker` flag when running from a PyInstaller bundle.

**Installers** wrap the bundle for each platform: macOS disk image (DMG), Windows installer package (MSI), Linux AppImage (x86_64). v1 installers are unsigned.

**Release process** — pushing a version tag (`v*`) triggers CI to build platform installers and publish a GitHub Release with downloadable artifacts.

See [ADR-0008](../../../../docs/adr/0008-pyinstaller-release-bundle.md) and [common-language.md](../../../../common-language.md) **Packaging**, **Installers**, **Release process**, **Release hygiene**.

## Package boundary

| Area | Package / path | Role |
|------|----------------|------|
| CLI dispatch | `lexiflow_ui.launcher` | `--version`, `--worker`, default UI |
| Worker argv | `lexiflow_ui.worker_command` | frozen vs dev spawn command |
| llama-server path | `lexiflow_core.llm.llama_server` | bundled binary, env override, PATH |
| Build scripts | `packaging/` | spec, fetch llama-server, installers — no domain logic |

## Bundled vs downloaded

| Shipped in installer | Downloaded on first use |
|----------------------|-------------------------|
| PySide6 UI, worker code | Hugging Face LLM weights (via bundled llama-server) |
| UI theme JSON tokens | MiniLM embedding weights (sentence-transformers) |
| `models.lock`, migrations, prompts | spaCy language packs when adding a target language |
| llama-server binary | Ollama models when using Ollama endpoint |

Model weights are **not** bundled in the installer ([common-language.md](../../../../common-language.md)).

## Version

Build-time script `packaging/scripts/sync_version.py` sets `lexiflow_core.__version__` from the release tag or root `pyproject.toml`. The **About dialog** and `lexiflow --version` read that value. In-app update checks (phase 14) compare it against the latest GitHub Release tag.

## Local build (maintainers)

```bash
uv sync --group release
uv run python packaging/scripts/sync_version.py
uv run python packaging/scripts/fetch_llama_server.py --platform linux
uv run pyinstaller packaging/lexiflow.spec --noconfirm
bash packaging/scripts/smoke_bundle.sh
```

Platform installers: `bash packaging/scripts/build_installer.sh linux|macos-arm64|windows`

## CI

- **PR / main:** `build-linux` job in `.github/workflows/ci.yml` builds and smokes the Linux onedir bundle.
- **Release tag:** `.github/workflows/release.yml` builds DMG, MSI, and AppImage; publishes SHA256 checksums.

## Out of scope (v1)

- Code signing, notarization, Authenticode
- Silent in-app auto-update install
- Bundling Hugging Face model weights or spaCy packs
