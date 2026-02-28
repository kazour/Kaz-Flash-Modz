# Kaz Flash Modz — Claude Code Instructions

## Current Work

**Version:** 3.3.6

**Phase:** Published on GitHub (MIT license). All features implemented, audited, and documented.

**DO NOT:**
- Refactor working code for "cleanliness" — stability over aesthetics
- Make changes without a clear purpose

---

## Project Overview

Kaz Flash Modz is a Python GUI that builds 5 SWF mods for **Age of Conan**: KzGrids (buff tracking), KzCastbars (cast bars), KzTimers (cooldown tracker), KzStopwatch (standalone timer), and DamageInfo (damage numbers).

---

## Tech Stack

- **Python 3.8+** with **ttkbootstrap** (darkly theme)
- **MTASC** compiler for AS2 → SWF (included in `assets/compiler/`)
- **Flash CS6** base.swf files (pre-built; not edited in this phase)
- **ActionScript 2.0** runtime code (generated from Python templates)

---

## User Preferences

- Write all required code — user is not a professional programmer
- **Be critical** of ideas, designs, and code quality — no sugar coating
- Prioritize safety, performance, stability
- Use minimal, efficient code
- Focus on macro-level planning before implementation
- Break projects into clear stages
- When reviewing UI: think like a user who has never seen this app

---

## File Stability

All modules are stable — avoid unnecessary refactoring. AS2 templates accept performance-only changes.

`base.swf` / `base.fla` files are **locked** — never modify Flash assets.

---

## Current UI Framework

**Base:** `ttkbootstrap.Window(themename="darkly")`

**Theme constants** (in `Modules/ui_helpers.py`):
- `THEME_COLORS` — semantic foreground: heading=#FFFFFF, body=#ADB5BD, muted=#888888, accent=#3498db, warning=#f39c12, danger=#e74c3c, success=#00bc8c, info_value=#3498db
- `TK_COLORS` — raw tk widgets: bg=#222222, input_bg=#2f2f2f, input_fg=#ffffff, select_bg=#555555, select_fg=#ffffff, border=#444444
- `AS2_COLORS` — KzTimers in-game colors (defaults/fallbacks). KzStopwatch button/shadow colors are now user-configurable via stopwatch_settings.py.
- `MODULE_COLORS` — per-module accent colors for Welcome cards: grids=#3498db, castbars=#00bc8c, timers=#f39c12, damageinfo=#e74c3c, stopwatch=#9b59b6
- `GRID_TYPE_COLORS` — player=#3498db (blue), target=#e67e22 (orange)
- Font constants: `FONT_TITLE`, `FONT_HEADING`, `FONT_SUBTITLE`, `FONT_SECTION`, `FONT_BODY`, `FONT_FORM_LABEL`, `FONT_SMALL_BOLD`, `FONT_SMALL`
- Layout constants: `PAD_TAB`, `PAD_SECTION`, `PAD_INNER`, `PAD_ROW`, `PAD_BUTTON_GAP`, `PAD_TIP_BAR`, `BTN_SMALL` (7), `BTN_MEDIUM` (12), `BTN_LARGE` (20)

**Style helpers** (for raw tk widgets that ttkbootstrap doesn't theme):
- `style_tk_listbox()`, `style_tk_text()`, `style_tk_canvas()`
- `apply_dark_titlebar()` — Windows 11 dark title bar via pywinstyles
- `blend_alpha(fg, bg, alpha)` — simulate AS2 opacity on tkinter Canvas (no native transparency)
- `setup_custom_styles()` — custom ttk styles (`TNotebook.Tab`, `StatusBar.TLabel`, `Card.TLabelframe`)
- `add_tooltip(widget, text)` — "?" badge with muted hint text

**Reusable widgets** (in `Modules/ui_helpers.py`):
- `ColorSwatch(tk.Canvas)` — rounded-rect color swatch with hover effect and click-to-pick via `ColorChooserDialog`. Accepts `color_var` (StringVar sync) and `on_change` callback. Handles `RRGGBB`, `#RRGGBB`, `0xRRGGBB` formats.
- `CollapsibleSection(ttk.Frame)` — clickable header with arrow indicator, title, badge, summary text; shows/hides content frame.
- `create_scrollable_frame(parent)` — returns `(outer, inner, canvas)` with canvas + scrollbar + mousewheel binding.

**Established UI patterns:**
- Alt-toggle menu bar (hidden by default)
- Profile indicator bar on all tabs via `create_profile_info_bar()` (accent blue, bold)
- LabelFrame padding via `.configure(padding=N)` after construction (Python 3.14 compat)
- `bind_card_events(card_border, color, var=None)` — debounced hover highlight + optional click-to-toggle
- Window position: `withdraw()` → build widgets → `restore_window_position()` → `deiconify()` (prevents visible jump). `bind_window_position_save()` uses 300ms debounce.
- `create_scrollable_frame()` for scrollable panels; global mousewheel handler walks widget tree to find nearest scrollable canvas
- `disable_mousewheel_on_inputs()` strips ttkbootstrap's class-level `<MouseWheel>` from TSpinbox, TCombobox, TScale, Scale
- `ttkbootstrap.dialogs.Messagebox` (message-first API, returns strings)
- Per-tab Build buttons for single-module SWF compilation
- Live Tracker as independent window launched from Welcome screen

---

## File Structure

```
Kaz Flash Modz/
├── kzbuilder.py              # Main GUI entry point (Welcome + all tabs)
├── build.py                  # PyInstaller build script
├── Modules/
│   ├── __init__.py
│   ├── ui_helpers.py         # Theme, fonts, AS2_COLORS, ColorSwatch, CollapsibleSection, scrollable frames, window utils, mousewheel, dark titlebar
│   ├── build_utils.py        # MTASC compilation, script management
│   ├── as2_template.py       # KzGrids AS2 runtime template
│   ├── grids_tab.py          # Grids tab UI
│   ├── grids_generator.py    # KzGrids code generation + build
│   ├── database_editor.py    # Buff database editor (child window)
│   ├── castbar_tab.py        # Castbars tab UI
│   ├── castbar_generator.py  # KzCastbars code generation + build
│   ├── castbar_settings.py   # Castbar defaults, validation, shared constants
│   ├── damageinfo_tab.py     # DamageInfo tab UI
│   ├── damageinfo_generator.py # DamageInfo code generation
│   ├── damageinfo_settings.py  # DamageInfo defaults, validation
│   ├── damageinfo_xml.py     # TextColors.xml parsing/generation
│   ├── timers_tab.py         # Timers tab: Cooldown Editor + Customization sub-tabs
│   ├── timers_appearance.py  # Timers appearance defaults, validation
│   ├── live_tracker_settings.py # Live Tracker overlay defaults, validation
│   ├── stopwatch_tab.py      # Stopwatch tab UI (thin shell with editor panel)
│   ├── stopwatch_editor.py   # Stopwatch Editor (2-column: preview+appearance | presets+phase list)
│   ├── stopwatch_phase_dialog.py # Phase Editor dialog (add/edit phase form)
│   ├── stopwatch_data.py     # StopwatchPhase, StopwatchPreset, StopwatchPresetSettings + templates
│   ├── stopwatch_settings.py # Stopwatch appearance defaults, validation
│   ├── stopwatch_generator.py # KzStopwatch code generation + build
│   ├── live_tracker_tab.py   # Live Tracker (independent window, boss timer + overlay)
│   ├── boss_timer.py         # Ethram-Fal seed cycle timer
│   ├── combat_monitor.py     # Combat log monitoring thread
│   ├── timer_overlay.py      # Timer overlay window
│   ├── timers_data.py        # CooldownTimer, CooldownPreset, CooldownSettings + validation
│   ├── timers_editor.py      # Cooldown Editor UI (2-column: preview+appearance | presets+timer list)
│   ├── timers_editor_dialog.py # Cooldown Editor dialog (add/edit timer form)
│   └── timers_generator.py   # KzTimers + TimerManager code generation + build
├── assets/                   # Compiler, base SWFs, stubs, templates
├── profiles/                 # User grid configurations
├── settings/                 # All app settings (JSON files)
├── temp/                     # Build artifacts
├── docs/                     # Reference documentation (see below)
├── README.md
├── CHANGELOG.md
└── CLAUDE.md                 # This file
```

---

## Key Classes

**kzbuilder.py:**
- `SettingsManager` — JSON settings persistence
- `KzBuilder(ttb.Window)` — Main window: Welcome, Grids, Castbars, Timers, Stopwatch, DamageNumbers tabs

**Tab pattern** (each module follows):
- `*_tab.py` — UI class with settings panel, profile support, per-tab Build button
- `*_generator.py` — Code generation + MTASC build
- `*_settings.py` — Defaults dict, validation, shared constants

**Shared utilities:**
- `ui_helpers.py` — Theme/font/layout constants, AS2_COLORS, MODULE_COLORS, ColorSwatch, CollapsibleSection, create_scrollable_frame, add_tooltip, blend_alpha, window position, global mousewheel, dark titlebar
- `build_utils.py` — `find_compiler()`, `compile_as2()` (supports multi-file), `update_script_with_marker()`, `escape_as2_string()`, `resolve_assets_path()`

**Logging:** All modules use `logging` (not `print()`). Configure via `logging.basicConfig()` in `kzbuilder.py`.

---

## Patterns & Conventions

- **Dataclass + serialization:** `@dataclass` with `to_dict()`/`from_dict()` methods for JSON persistence. Used in `timers_data.py` (CooldownTimer, CooldownPreset, CooldownSettings), `stopwatch_data.py` (StopwatchPhase, StopwatchPreset, StopwatchPresetSettings), `damageinfo_xml.py` (DamageType).
- **Enum types:** Type-safe constants in `timers_data.py` — `TriggerType` (buff_add, buff_remove, cast_success), `BarDirection` (fill, drain), `CountDirection` (ascending, descending), `RetriggerMode` (restart, ignore).
- **Settings pattern:** `*_settings.py` files export a `DEFAULTS` dict and a `validate()` function. Generators read settings and apply them to AS2 templates via string replacement placeholders.
- **DamageInfo is unique:** Decompiled game file modified via regex — not a class-based MTASC module like the other 4. No module system integration, no config archive.

---

## Build Pipeline

**Per-tab Build** (single module): Each module tab has a Build button that compiles directly to the game directory.

**Build All** (from Welcome screen):
1. Validate prerequisites (game path, compiler)
2. **Phase 1 — Compile:** All enabled modules compile to temp staging directory
3. If ANY module fails → error shown, game directory untouched, staging cleaned up
4. **Phase 2 — Install:** Copy SWFs from staging to game dir, run side effects (XML, scripts)
5. Disabled modules get artifacts cleaned up automatically

**Output:** `{AoC}/Data/Gui/Default/Flash/*.swf`

---

## Profile System

- **Global profiles** (File > Save/Open): ALL tabs + Welcome screen module enable flags
- **Per-tab Import/Export**: Individual tab data only
- **Auto-persist** to `settings/*.json` on change
- Format: JSON with keys `grids`, `castbars`, `damageinfo`, `timers`, `stopwatch`, `live_tracker`, `build`
- Backward compatible: missing keys load defaults

---

## AS2 Constraints (DO NOT change AS2 patterns)

- **32KB bytecode limit** per MTASC class
- No `for...in` on arrays — use `while` with index
- No `var` redefinition in same scope
- Explicit null comparison (`obj == null`, not `!obj`)
- No string literal keys in object literals — use bracket notation
- Closures need `var self = this` capture
- Masks applied AFTER content loads (`onLoadInit`)

Full details: `docs/as2-reference.md`

---

## Reference Docs

| Doc | Contents |
|-----|----------|
| `docs/architecture.md` | Data models, code generation flow, class relationships |
| `docs/as2-reference.md` | AS2 syntax rules, MTASC gotchas, all code patterns |
| `docs/build-system.md` | Compile commands, file requirements, AoC directory map |
| `docs/modules/kzgrids.md` | Grid config, database format, slot types, signals |
| `docs/modules/kzcastbars.md` | Castbar config, preview mode, XML hiding |
| `docs/modules/kztimers.md` | Cooldown editor, triggers, presets, lifecycle |
| `docs/modules/kzstopwatch.md` | Stopwatch config, preview mode, layouts, state machine |
| `docs/modules/damageinfo.md` | Settings, architecture, optimization history |
| `docs/module-system.md` | AoC module system, config archive, lifecycle, Aoc.exe bypass |
| `docs/default-settings.md` | All default values and ranges for every module |
| `CHANGELOG.md` | Full version history |

---

## Testing

1. Run app: `python kzbuilder.py`
2. Click through each tab — verify all controls respond
3. Build a single module via per-tab Build button
4. Build All from Welcome screen
5. In-game: `/reloadui` then `/reloadgrids`
6. `Ctrl+Shift+Alt` for Preview Mode
7. PyInstaller build: `python build.py`

**Cannot run automated tests** — UI is manual verification only. In-game testing requires AoC client.
