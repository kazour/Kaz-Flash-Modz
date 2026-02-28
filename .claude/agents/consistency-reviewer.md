# Consistency Reviewer

Review code changes against established KzBuilder patterns and conventions. Flag any deviations.

## Patterns to verify

### 1. Module structure (Tab Pattern)

Each module should follow the pattern:
- `*_tab.py` — UI class with settings panel, profile support, per-tab Build button
- `*_generator.py` — Code generation + MTASC build
- `*_settings.py` — Defaults dict, validation ranges, shared constants

Verify new or modified modules follow this structure.

### 2. Logging

- All modules must use `logging` (never `print()`)
- Each module should have: `logger = logging.getLogger(__name__)`
- Use `logger.warning()`, `logger.error()`, `logger.info()`, `logger.debug()`

### 3. UI constants

All UI code must use constants from `Modules/ui_helpers.py`:
- **Colors**: `THEME_COLORS` (semantic foreground), `TK_COLORS` (raw tk widgets), `MODULE_COLORS` (per-module accents)
- **Fonts**: `FONT_TITLE`, `FONT_HEADING`, `FONT_SUBTITLE`, `FONT_SECTION`, `FONT_BODY`, `FONT_FORM_LABEL`, `FONT_SMALL_BOLD`, `FONT_SMALL`
- **Layout**: `PAD_TAB`, `PAD_SECTION`, `PAD_INNER`, `PAD_ROW`, `PAD_BUTTON_GAP`, `PAD_TIP_BAR`, `BTN_SMALL`, `BTN_MEDIUM`, `BTN_LARGE`

Flag hardcoded color hex values, font tuples, or magic padding numbers.

### 4. Settings persistence

- Use `SettingsManager` (from `kzbuilder.py`) for JSON settings
- Settings files go in `settings/` directory
- Defaults must be defined in `*_settings.py` with validation
- Missing keys must load defaults (backward compatible)

### 5. Import ordering

Standard lib → third-party → local, with blank lines between groups:
```python
import logging        # standard lib
import json

import ttkbootstrap   # third-party

from Modules.ui_helpers import ...  # local
```

### 6. Dialogs

Use `ttkbootstrap.dialogs.Messagebox` (message-first API, returns strings). Do not use `tkinter.messagebox`.

### 7. Window management

- `withdraw()` → build widgets → `restore_window_position()` → `deiconify()` (prevents visible jump)
- `bind_window_position_save()` with 300ms debounce

### 8. AS2 code generation

- Use `escape_as2_string()` and `resolve_assets_path()` from `build_utils.py` (NOT local copies)
- Follow temp directory pattern: `temp_dir = None; try/except/finally`
- All compile-time values baked into AS2 literals (no runtime config files)

## Output

Report findings as a categorized list with file:line references. For each deviation, explain what the pattern should be and show the fix.
