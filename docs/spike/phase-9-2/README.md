# Phase 9-2 theme spike

Manual comparison on macOS. **Decision:** Fusion base + bundled `dark_theme.json` / `light_theme.json` tokens via `lexiflow_ui.theme_stylesheet`.

| Variant | Screenshot | Notes |
|---------|------------|-------|
| Fusion baseline | *(optional capture)* | Default PySide6 chrome before migration |
| Dark theme | [dark_theme.png](dark_theme.png) | Dark **UI theme** |
| Light theme | [light_theme.png](light_theme.png) | Light **UI theme** |

Re-run capture:

```bash
uv run python scripts/theme_spike.py fusion --screenshot docs/spike/phase-9-2/fusion.png
uv run python scripts/theme_spike.py dark_theme --screenshot docs/spike/phase-9-2/dark_theme.png
uv run python scripts/theme_spike.py light_theme --screenshot docs/spike/phase-9-2/light_theme.png
```

Spike script: [`scripts/theme_spike.py`](../../../scripts/theme_spike.py).
