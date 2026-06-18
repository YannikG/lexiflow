Archived spike from phase 9-2. **Decision:** Fusion base + bundled `dark_theme.json` / `light_theme.json` tokens via `lexiflow_ui.theme_stylesheet`.

| Variant | Screenshot | Notes |
|---------|------------|-------|
| Fusion baseline | *(optional capture)* | Default PySide6 chrome before migration |
| Dark theme | [dark_theme.png](dark_theme.png) | Dark **UI theme** |
| Light theme | [light_theme.png](light_theme.png) | Light **UI theme** |

The one-off capture script (`scripts/theme_spike.py`) was removed after migration. Re-capture only if you change token/QSS design: launch the app with each **Theme** setting or a minimal pytest-qt window using `apply_app_theme` from `lexiflow_ui.theme_stylesheet`.
