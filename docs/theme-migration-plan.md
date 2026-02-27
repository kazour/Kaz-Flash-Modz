# Kaz Flash Modz — ttkbootstrap "darkly" Theme Migration (Completed)

## Status: COMPLETE

This migration was fully implemented. Kaz Flash Modz now uses ttkbootstrap's **darkly** theme with dark title bars, themed messageboxes, and color pickers. This document is retained as a historical reference.

**Dependencies added:**
- `ttkbootstrap` — theme engine
- `pywinstyles` — dark title bars on Windows 11

---

## What Was Done

### Phase 1: Foundation — `Modules/ui_helpers.py`
- Added `THEME_COLORS` dict (8 semantic foreground colors)
- Added `TK_COLORS` dict (6 raw tk widget colors)
- Added `AS2_COLORS` dict (13 in-game SWF colors)
- Added `MODULE_COLORS` dict (5 per-module accent colors)
- Added 3 style helpers: `style_tk_listbox()`, `style_tk_text()`, `style_tk_canvas()`
- Added `blend_alpha()` for simulating AS2 opacity on Canvas

### Phase 2: Entry Point — `kzbuilder.py`
- Changed `tk.Tk` → `ttb.Window(themename="darkly")`
- Replaced ~24 hardcoded foreground colors with `THEME_COLORS` constants

### Phase 3: Module Tabs (6 files)
- `grids_tab.py` — ~15 color replacements, Canvas/Listbox styling, font standardization
- `damageinfo_tab.py` — ~40 color replacements, Canvas border styling
- `castbar_tab.py` — ~12 color replacements, preview canvas + button styling
- `timers_tab.py` — ~10 color replacements (status label colors)
- `timers_editor.py` — 1 color + Listbox styling
- `database_editor.py` — 4 colors + Text widget styling

### Phase 4: Themed Dialogs
- Replaced all `tkinter.messagebox` calls with `ttkbootstrap.dialogs.Messagebox` across all files
- Migrated return value checks: `True/False` → `"Yes"/"No"` string comparisons
- Replaced `colorchooser.askcolor()` with `ttkbootstrap.dialogs.ColorChooserDialog`
- File dialogs (`filedialog.*`) left as native OS dialogs (cannot be themed)

### Phase 5: Dark Title Bars
- Added `apply_dark_titlebar()` using pywinstyles
- Applied to main window + all Toplevel dialogs

### Phase 6: No-Change Files
These files correctly required zero changes:
- `timer_overlay.py` — has its own dark color scheme
- All generator files, settings files, data files — no UI widgets
- `build_utils.py`, `boss_timer.py`, `combat_monitor.py` — no UI widgets

---

## API Reference (for future development)

### Messagebox (ttkbootstrap)
```python
from ttkbootstrap.dialogs import Messagebox

# Parameter order: message first, title as keyword
Messagebox.show_info("Message", title="Title")
Messagebox.show_error("Message", title="Title")
Messagebox.show_warning("Message", title="Title")

# Yes/No returns STRINGS, not booleans
if Messagebox.yesno("Delete this?", title="Confirm") == "No":
    return

# Yes/No/Cancel returns "Yes", "No", or "Cancel"
result = Messagebox.yesnocancel("Save changes?", title="Unsaved")
if result == "Cancel":
    return
```

### ColorChooserDialog (ttkbootstrap)
```python
from ttkbootstrap.dialogs import ColorChooserDialog

dialog = ColorChooserDialog(parent=self, title="Choose Color", initialcolor=current_hex)
dialog.show()
if dialog.result:
    hex_val = dialog.result.hex  # e.g. "#FF0000"
```

---

## Python 3.14 Compatibility Note

`LabelFrame(padding=N)` in the constructor crashes with ttkbootstrap on Python 3.14. Use `.configure(padding=N)` after construction instead.
