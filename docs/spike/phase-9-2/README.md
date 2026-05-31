# Phase 9-2 theme spike

Manual comparison on macOS (2026-05-31). **Decision: qt-material** (`dark_teal.xml` / `light_teal.xml`).

| Variant | Screenshot | Notes |
|---------|------------|-------|
| Fusion baseline | [fusion.png](fusion.png) | Default PySide6 chrome before migration |
| qt-material dark | [material-dark.png](material-dark.png) | Selected for dark **UI theme** |
| qt-material light | [material-light.png](material-light.png) | Selected for light **UI theme** (`invert_secondary=True`) |
| qt-modern-style light | [modern-light.png](modern-light.png) | Fallback only; not used for v1 |

Re-run capture:

```bash
uv run python scripts/theme_spike.py fusion --screenshot docs/spike/phase-9-2/fusion.png
uv run python scripts/theme_spike.py material-dark --screenshot docs/spike/phase-9-2/material-dark.png
uv run python scripts/theme_spike.py material-light --screenshot docs/spike/phase-9-2/material-light.png
```

Spike script: [`scripts/theme_spike.py`](../../../scripts/theme_spike.py).
