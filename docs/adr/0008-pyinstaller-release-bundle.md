# PyInstaller release bundle

**Status:** Accepted  
**Date:** 2026-06-03  
**Supersedes:** none  
**Implementation:** [phase 15 — packaging and release](../roadmap/phases/phase-15-packaging-release/README.md)

## Context

LexiFlow ships as a desktop app for macOS, Windows, and Linux. End users must not install Python separately. Phase 11-1 deferred bundling `llama-server`; phase 14 added in-app update checks against GitHub Releases. ADR-0001 and [architecture overview](../architecture/overview.md) require one PyInstaller bundle where the UI spawns the worker from the same binary.

PySide6, optional `sentence-transformers` (embeddings), and a native `llama-server` binary must coexist in a single onedir layout without bundling Hugging Face model weights.

## Decision

1. **Onedir PyInstaller layout** — `COLLECT` onedir, not onefile. Qt and torch startup time and plugin discovery favor onedir.
2. **Unified launcher** — `lexiflow_ui.launcher` dispatches default UI, `--worker`, and `--version`. PyInstaller entry point is the launcher module.
3. **Frozen worker spawn** — `build_worker_command` uses `[executable, "--worker", ...]` when `sys.frozen`; dev keeps `python -m lexiflow_worker`.
4. **Bundled llama-server** — CI downloads pinned llama.cpp prebuilts into `packaging/bin/<platform>/`; spec copies to `bin/` in the bundle; `llama_server_binary()` resolves `{sys._MEIPASS}/bin/llama-server` before PATH.
5. **Release dependency group** — root `pyproject.toml` `[dependency-groups] release` adds `pyinstaller`, `sentence-transformers` (+ torch transitively). PR pytest stays fake-only; no real models in CI unit tests.
6. **Version sync** — `packaging/scripts/sync_version.py` writes `lexiflow_core.__version__` from the release tag, an automatic CI dev suffix on PR builds, or `pyproject.toml` locally. Release workflow syncs `pyproject.toml` back to `main` after publish.
7. **Installers** — Linux AppImage, macOS DMG, Windows MSI (WiX + heat harvest). Unsigned in v1.
8. **Release CI** — tag `v*` triggers `.github/workflows/release.yml`; SHA256 checksums published per asset.

## Evaluated alternatives

| Option | Verdict |
|--------|---------|
| Onefile PyInstaller | **Rejected** — slow cold start; fragile with PySide6 plugins and torch |
| Separate UI/worker binaries | **Rejected** — conflicts with ADR-0001 single-bundle model |
| Build llama.cpp from source in CI | **Rejected** — slow, toolchain-heavy; prebuilts sufficient for v1 |
| Zip-only Windows artifact | **Rejected** — [common-language.md](../../common-language.md) specifies MSI |

## Consequences

- README documents end-user install, Gatekeeper/SmartScreen friction, and first-run model download (weights not bundled).
- `packaging/bin/` and `dist/` are gitignored; CI fetches llama-server per job.
- macOS/Windows full installer builds run on tag only; PR CI builds and smokes Linux bundle only.
- Code signing and notarization remain post-v1 ([common-language.md](../../common-language.md) **Code signing roadmap**).

## References

- [ADR-0001](0001-split-packages-and-ci-quality-gates.md)
- [ADR-0006](0006-desktop-ui-theme-strategy.md) — theme JSON bundled in spec
- [ADR-0007](0007-native-llama-server-llm.md)
