# Architecture — Code Structure & Data Models

## Python Builder Classes

### kzbuilder.py
- `SettingsManager` — Persists to `settings/kzbuilder_settings.json`
- `KzBuilder(ttb.Window)` — Main window: Welcome tab (bundle builder), Grids, Castbars, Timers, Stopwatch, DamageNumbers tabs
- `build()` → `_validate_build_prerequisites()`, `_get_build_configuration()`, `_execute_builds()`, `_display_build_summary()`
- `_open_live_tracker()` — Launches Live Tracker as independent window from Welcome screen

### Modules/ui_helpers.py

**Constants:**
- `FONT_TITLE`, `FONT_HEADING`, `FONT_SECTION`, `FONT_BODY`, `FONT_SMALL_BOLD`, `FONT_SMALL`
- `THEME_COLORS` — semantic foreground colors (heading, body, muted, accent, warning, danger, success, info_value)
- `TK_COLORS` — raw tk widget colors (bg, input_bg, input_fg, select_bg, select_fg, border)
- `MODULE_COLORS` — per-module accent colors for Welcome cards (grids=blue, castbars=green, timers=orange, damageinfo=red, stopwatch=purple)
- `AS2_COLORS` — hardcoded in-game SWF colors (border, bg, text, buttons, dots, shadow)
- Layout constants: `PAD_TAB`, `PAD_SECTION`, `PAD_INNER`, `PAD_ROW`, `BTN_SMALL`, `BTN_MEDIUM`, `BTN_LARGE`

**Functions:**
- `blend_alpha(fg, bg, alpha)` — simulate AS2 opacity on Canvas (no native transparency)
- `create_rounded_rect()` — draw rounded rectangles on Canvas
- `create_tip_bar()` — compact single-line tip bars
- `create_profile_info_bar()` — profile indicator bar used on all tabs (accent blue, bold)
- `fill_canvas_solid()` — fill canvas with solid color rectangle, immune to theme overrides
- `create_section_header()` — small bold label with optional colored accent dot
- `add_tooltip()` — hover tooltip via ttkbootstrap.tooltip.ToolTip
- `setup_custom_styles()` — custom ttk styles (TNotebook.Tab, StatusBar.TLabel, Card.TLabelframe)
- `style_tk_listbox()`, `style_tk_text()`, `style_tk_canvas()` — raw tk widget styling
- `apply_dark_titlebar()` — Windows 11 dark title bar via pywinstyles
- `init_settings()` / `get_setting()` / `set_setting()` — module-level settings access
- `clamp_to_screen()`, `save_window_position()`, `restore_window_position()`, `bind_window_position_save()` — window position persistence (withdraw/deiconify pattern, 300ms debounced save)
- `create_scrollable_frame()` — canvas + scrollbar + mousewheel binding; returns (outer, inner, canvas)
- `bind_canvas_mousewheel()` — registers canvas for global mousewheel handler (walks widget tree to find nearest scrollable canvas)
- `disable_mousewheel_on_inputs()` — remove ttkbootstrap's class-level `<MouseWheel>` from TSpinbox, TCombobox, TScale, Scale

**Reusable widget classes:**
- `ColorSwatch(tk.Canvas)` — rounded-rect color swatch with hover effect and click-to-pick; syncs with StringVar, handles RRGGBB/0xRRGGBB/#RRGGBB
- `CollapsibleSection(ttk.Frame)` — clickable header with arrow indicator, title, badge, summary; shows/hides content frame

### Modules/build_utils.py
- `find_compiler()` — locate MTASC executable (checks assets/compiler, app root)
- `compile_as2()` — run MTASC with timeout; supports multi-file and `extra_flags`
- `strip_marker_block()` — remove marker-delimited blocks from scripts
- `update_script_with_marker()` — update auto-login scripts with marker-delimited content

### Module Files

| Module | Tab UI | Generator | Settings |
|--------|--------|-----------|----------|
| KzGrids | `grids_tab.py` | `grids_generator.py` | (inline in tab/generator) |
| KzCastbars | `castbar_tab.py` | `castbar_generator.py` | `castbar_settings.py` |
| KzTimers | `timers_tab.py` | `timers_generator.py` | `timers_appearance.py` |
| KzStopwatch | `stopwatch_tab.py` | `stopwatch_generator.py` | `stopwatch_settings.py` |
| DamageInfo | `damageinfo_tab.py` | `damageinfo_generator.py` | `damageinfo_settings.py` |

**Additional files:**
- `grids_tab.py` — `AddGridWizard`, `BuffSelectorDialog`, `SlotAssignmentDialog`, `GridEditorPanel`, `GridsTab`
- `database_editor.py` — `BuffDatabase`, `BuffEditDialog`, `DatabaseEditorTab`
- `as2_template.py` — KzGrids AS2 runtime template (`CORE_METHODS_TEMPLATE`)
- `timers_data.py` — CooldownTimer, CooldownPreset, CooldownSettings dataclasses + validation; `MAX_TIMERS_PER_PRESET = 10`
- `timers_editor.py` — Cooldown Editor panel UI (2-column: preview+appearance | presets+timer list; add/edit via modal dialog)
- `timers_editor_dialog.py` — Cooldown Editor dialog (add/edit timer form)
- `stopwatch_editor.py` — Stopwatch Editor panel UI (2-column: preview+appearance | presets+phase list)
- `stopwatch_phase_dialog.py` — Phase Editor dialog (add/edit phase: name, duration, color)
- `stopwatch_data.py` — StopwatchPhase, StopwatchPreset, StopwatchPresetSettings dataclasses + built-in templates; `MAX_PHASES_PER_PRESET = 10`
- `live_tracker_settings.py` — Live Tracker overlay defaults, validation
- `damageinfo_xml.py` — TextColors.xml parsing/generation
- `live_tracker_tab.py` — Boss timer, combat log monitoring, overlay (independent window)
- `boss_timer.py`, `combat_monitor.py`, `timer_overlay.py` — Live Tracker components

---

## Code Generation Flow (KzGrids)

1. `CodeGenerator.__init__()` receives grids + database
2. `generate()` assembles full AS2 class
3. `_init_config()` generates: grid configs, whitelists, `ISDEB[id]`, `BUFFTYPE[id]`, `STACK_LEVEL[id]`
4. `_core_methods()` returns template from `as2_template.py`

---

## Signal Connections (AoC API)

```actionscript
// Player buffs
m_Player.SignalBuffAdded.Connect(SlotPBuffAdd, this);
m_Player.SignalBuffUpdated.Connect(SlotPBuffAdd, this);
m_Player.SignalBuffRemoved.Connect(SlotPBuffRem, this);
m_Player.SignalOffensiveTargetChanged.Connect(SlotTargetChanged, this);

// Target buffs
m_Target.SignalBuffAdded.Connect(SlotTBuffAdd, this);
m_Target.SignalBuffUpdated.Connect(SlotTBuffAdd, this);
m_Target.SignalBuffRemoved.Connect(SlotTBuffRem, this);
```

---

## Icon Loading Pattern

```actionscript
com.Utils.ImageLoader.RequestRDBImage(
    new com.Utils.ID32(1010008, iconInstance), obj, "cb" + si
);

function createCB(obj, si):Function {
    var self:KzGrids = this;
    return function(url:String, ok:Boolean):Void {
        self.onIconLoad(obj, si, url, ok);
    };
}
```

---

## Profile Format

```json
{
    "version": "3.3.4",
    "grids": [/* grid config objects */],
    "castbars": {/* castbar settings */},
    "damageinfo": {/* damage number settings */},
    "timers": {
        "timers": {/* timer configs + presets */},
        "appearance": {/* visual customization settings */}
    },
    "stopwatch": {
        "appearance": {/* stopwatch appearance settings */},
        "presets": {/* preset configs: labels, phases, end behavior, direction */}
    },
    "live_tracker": {/* boss timer + overlay settings */},
    "build": {
        "grids": true,
        "castbars": true,
        "timers": true,
        "damageinfo": true,
        "stopwatch": true
    }
}
```

Missing keys get filled with defaults from their respective settings modules.

---

## Developer Workflows

### Adding New Grid Options
1. Add to `create_default_grid()` in `grids_tab.py`
2. Add UI control in `GridEditorPanel.create_widgets()`
3. Load/save in `load_from_config()` / `save_to_config()`
4. Generate in `CodeGenerator._generate_grid_config()` (`grids_generator.py`)
5. Use in AS2 template (`as2_template.py`)

### Adding New Helper Class
1. Create `KzGridsNewFeature.as`
2. Copy to `stubs/` folder
3. Add member variable: `private var newFeature:KzGridsNewFeature;`
4. Initialize: `newFeature = new KzGridsNewFeature(this, rootClip);`
5. Call: `newFeature.doSomething();`

### Testing Workflow
1. Edit Python code → Run builder → Configure → "Build & Install All" (or per-tab Build)
2. In-game: `/reloadui` then `/reloadgrids`
3. `Ctrl+Shift+Alt` for Preview Mode

---

## Future Improvements

### Remove Redundant ISDEB Lookup
**Priority:** Low | **Impact:** Reduced generated code size

`ISDEB` is redundant since `BUFFTYPE` contains type info. To remove:
1. Python (`grids_generator.py`): Remove ISDEB generation in `_init_config()`
2. AS2 (`as2_template.py`): Replace `ISDEB[bid]` with `BUFFTYPE[bid] == "debuff"`
3. AS2: Change `mkEntry()` to derive `isD` from `BUFFTYPE`

Saves ~400 lines in generated .as for heavy profiles.
