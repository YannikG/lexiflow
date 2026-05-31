# Phase 15: Packaging and release

**Branch:** `phase/15-packaging-release`  
**PR title:** `Phase 15: PyInstaller bundle, installers, release workflow`

## Outcome

- **Packaging**: single installable bundle with UI and worker
- **Installers** for macOS, Windows, Linux
- **Release process**: version tag triggers CI build and GitHub Release
- **Release hygiene**: checksums published; install docs for unsigned v1 (**code signing roadmap** deferred)
- **App icon (v1)** placeholder assets
- First public release tag produces downloadable artifacts (models not bundled)

## References

- [ADR-0001](../../../adr/0001-split-packages-and-ci-quality-gates.md)
- [ADR-0006](../../../adr/0006-desktop-ui-theme-strategy.md) — bundle **UI theme** assets (`qt-material` QSS) in PyInstaller spec
- [common-language.md](../../../../common-language.md): **Packaging**, **Installers**, **Release process**, **Code signing roadmap**, **Release hygiene**
- [ui-theme.md](../../../../packages/lexiflow-ui/docs/concepts/ui-theme.md)

## TDD cycles

### Cycle 15.1 — PyInstaller spec builds locally

**Test:** CI job `build` artifact exists (smoke test unzip + run `--version`).

---

### Cycle 15.2 — Worker entry runs from bundle

**Test:** packaged binary `--worker` mode exits 0.

---

### Cycle 15.3 — UI entry runs headless smoke

**Test:** packaged binary with env QT_QPA_PLATFORM=offscreen (linux ci) or skip mac/windows agents.

---

### Cycle 15.4 — DMG/MSI/AppImage artifacts attached

**Test:** release workflow dry-run on `v0.0.0-test` tag (optional manual).

---

### Cycle 15.5 — Version matches pyproject

**Test:** `--version` prints tag version.

---

## Manual verification

1. Download artifact from CI
2. Install on Linux PC (user)
3. First run onboarding + model download

## PR checklist

- [ ] models NOT bundled in installer
- [ ] SHA256 published per asset
- [ ] SECURITY.md + CONTRIBUTING.md complete

## Post-v1

- Code signing (Apple / Authenticode)
- Nightly real-LLM smoke (optional)
