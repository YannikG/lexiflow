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
| Build scripts | `packaging/` | spec, fetch llama-server, fetch sqlite-vec, installers — no domain logic |
| sqlite-vec loadable | `packaging/vendor/sqlite_vec/` | vendored path dependency; platform `vec0` binary fetched or compiled at build time |

## Bundled vs downloaded

| Shipped in installer | Downloaded on first use |
|----------------------|-------------------------|
| PySide6 UI, worker code | Hugging Face LLM weights (via bundled llama-server) |
| UI theme JSON tokens | Embedding GGUF (llama-server, not bundled) |
| `models.lock`, migrations, prompts | spaCy language packs when adding a target language |
| llama-server binary | Ollama models when using Ollama endpoint |
| sqlite-vec `vec0` extension (per platform) | — (fetched at CI/build; Windows ARM64 compiled from upstream amalgamation) |

Model weights are **not** bundled in the installer ([common-language.md](../../../../common-language.md)).

## Version

Build-time script `packaging/scripts/sync_version.py` sets `lexiflow_core.__version__`:

- **Release tag** (`vX.Y.Z`) → exact tag version
- **Local dev** → root `pyproject.toml`

Before tagging a release, bump `pyproject.toml` on `main` via PR; the release build reads the tag version at CI time and does not push back to `main`.

## Local build (maintainers)

Fetch the vendored sqlite-vec loadable for your host before `uv sync` (binaries are not committed):

```bash
python packaging/scripts/fetch_sqlite_vec.py --platform macos-arm64  # or linux / windows
uv sync --group release
uv run python packaging/scripts/sync_version.py
uv run python packaging/scripts/fetch_llama_server.py --platform linux
uv run pyinstaller packaging/lexiflow.spec --noconfirm
bash packaging/scripts/smoke_bundle.sh
```

On **Windows ARM64**, compile the extension first: `prepare_sqlite_vec_windows_arm64.py` downloads the official sqlite-vec amalgamation plus SQLite `sqlite3ext.h`, then `build_sqlite_vec_windows.ps1` builds `vec0.arm64.dll` with MSVC arm64. The fetch step is a no-op for the DLL stem.

**Windows MSI** uses WiX with a four-part product version from `packaging/scripts/wix_version.py` (invoked from `build_msi.ps1`).

Platform installers: `bash packaging/scripts/build_installer.sh linux|macos-arm64|windows|windows-arm64`

## CI

- **PR / main:** lint, mypy, and pytest (`.github/workflows/ci.yml`). Linux test job runs `fetch_sqlite_vec.py --platform linux` before `uv sync`. No PyInstaller build on every PR.
- **Release tag:** `.github/workflows/release.yml` builds Linux AppImage, macOS DMG, and Windows x64 MSI (Windows ARM64 MSI temporarily disabled; see issue #40). Publishes SHA256 checksums.

## Out of scope (v1)

- Code signing, notarization, Authenticode
- Silent in-app auto-update install
- Bundling Hugging Face model weights or spaCy packs
