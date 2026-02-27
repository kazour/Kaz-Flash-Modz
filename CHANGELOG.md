# Changelog

All notable changes to Kaz Flash Modz will be documented in this file.

---

## Post-Release Cleanup

### Changed
- Deduplicated `escape_as2_string()` and `resolve_assets_path()` into `build_utils.py` — removed identical copies from timers, stopwatch, and castbar generators
- Replaced C-style `while i < len()` loops with idiomatic Python (`for`, `enumerate`, `sum()`, list comprehensions) in stopwatch generator and data modules
- Flattened nested `try/try/finally/except` in damageinfo generator to match the `temp_dir = None; try/except/finally` pattern used by all other generators
- Removed unnecessary `.resolve()` calls from timers and stopwatch build functions for consistency with castbar, grids, and damageinfo generators
- Fixed PEP 8 blank line spacing in castbar generator

---

## v3.3.4 — Stopwatch Preset System

### Added
- **Programmable preset buttons (P1/P2/P3)** — each preset defines a phase-based sequence with name, duration, and color per phase
- **3 end behaviors per preset**: Loop (restart from phase 1), End (stop timer), Continue (keep counting past the end — negative time if descending, positive overflow if ascending)
- **Per-preset count direction**: ascending (0 → total) or descending (total → 0)
- **Default presets**: Kuth (200s countdown, 7 phases), SG (200s countdown, 7 phases), Seed (39s loop, 4 phases from boss_timer.py)
- **Phase Editor dialog** — modal form for adding/editing phases (name, duration, color with quick-pick swatches)
- **Stopwatch Editor panel** — two-column layout matching Timers Editor: preview + appearance (col 0), presets + phase list with CRUD (col 1)
- **Phase font size setting** (`phase_font_size`, range 8–24) — separate control for phase name text size
- Preset button appearance colors (active/inactive) added to stopwatch customization
- Separate `stopwatch_presets.json` for preset data persistence

### Changed
- Stopwatch tab rewritten as thin shell (816 → 340 lines) delegating to StopwatchEditorPanel
- Stopwatch generator updated to bake preset/phase data into AS2 literals at compile time
- KzStopwatch.as.template expanded with preset buttons, phase text display, and phase-driven update logic
- KzStopwatch AS2 template redesigned to match KzTimers design language (shared layout constants, button sizing, preset row height, divider lines)
- Stopwatch editor UI reorganized: layout radios above preview, position merged into Panel section, font sizes moved to text color section
- Stopwatch editor right column: "Preset" LabelFrame (Label, End Behavior, Direction rows) + "Phases" LabelFrame with CRUD buttons
- Stopwatch editor preview rewritten to match AS2 template exactly (BTN_HEIGHT=20, HEADER_HEIGHT=4, PRESET_ROW_HEIGHT=30, 1px background inset, phase text, divider)
- Stopwatch default dimensions updated (width 220, height 120); layout switch sets defaults (Standard: 220x120, Compact: 220x40)
- Equal column widths enforced in stopwatch editor via `uniform='col'`
- Profile format updated: `{"appearance": {...}, "presets": {...}}`
- Time format changed to `0:00:00` (unpadded hours) in AS2 template and Python preview
- Template system removed from editor UI — presets ship with real game-accurate defaults instead

### Fixes
- AS2 timer text positioning: phase+timer block centered between divider lines (fixes ~2px preview/in-game parity offset)
- KzTimers panel width locked to 240px (no longer shrinks to 160px when empty)
- Loop end behavior: timer display now resets on cycle completion (was showing raw elapsed time instead of modulo'd display time)
- Button shape preview: "rounded" was visually indistinguishable from "square" — preview radius bumped from 3 to 5 in both Timers and Stopwatch editors (in-game AS2 unchanged)
- Compact layout: removed broken AS2 TextField mask (TextField.setMask() doesn't exist in AS2)

---

## v1.0.0 — Initial Public Release

### Features

**KzGrids — Buff/Debuff Tracking**
- Dynamic and static grid modes with player/target tracking
- Configurable icon size (24–64px), gap, fill direction, sort order, layout priority
- Timer text with flash threshold (0–11s), Y-offset, per-grid enable/disable
- Buff Discovery Console with pinnable mode and per-side logging toggles
- Up to 64 total slots across all grids
- Buff database with categories, stacking support, and multi-ID buffs

**KzCastbars — Custom Cast Bars**
- 6 visual frame styles with per-bar color settings
- Separate font customization for spell name and timer text
- Optional elapsed/total timer estimation
- Text positioning offsets
- Automatic hiding of the game's default castbar

**KzTimers — Cooldown Tracker**
- Cooldown Editor with named timers, trigger conditions, and bar appearance
- 3 trigger types: Buff Added, Buff Removed, Cast Success (with fuzzy spell name matching)
- Per-timer bar color, warning color, fill direction (fill/drain), count direction (ascending/descending), retrigger mode (restart/ignore)
- Up to 3 presets with up to 10 simultaneous countdown bars
- Full panel appearance customization: colors, fonts, bold, decimals toggle, text offset, border, corner radius, shadow, opacity, button shape
- Optimized AS2 runtime: single `getTimer()` per update, `_xscale` bar fills, pooled state objects, cached panel resize, diffed TextField updates, pre-compiled color Numbers

**KzStopwatch — Standalone Timer**
- Start/Pause/Stop with HH:MM:SS format
- Standard and Compact layouts
- 3 programmable preset buttons with phase-based sequences (name, duration, color per phase)
- Per-preset end behavior (loop/end/continue) and count direction (ascending/descending)
- 25 customizable settings: dimensions, fonts, colors, border, button shape, opacity, preset button colors

**DamageInfo — Damage Number Customization**
- 19 settings as offsets from game defaults across 6 categories
- 3 animation presets (Default, Performance, Beauty)
- Per-damage-type color customization via TextColors.xml generation

**Builder Application**
- ttkbootstrap darkly theme with Windows 11 dark title bars
- Per-tab Build buttons for individual module compilation
- Build All with atomic two-phase compile+install (staging → game directory)
- Global and per-tab profile system with JSON import/export
- Preview Mode (Ctrl+Shift+Alt) for all modules with drag-to-reposition
- AoC module system support with config archive persistence (position, visibility)
- Fallback `/loadclip` script mode for users without the module system
- Live Tracker window with Ethram-Fal boss timer and combat log monitor

---

## Development History

*The following entries document internal development prior to the public release.*

### v3.3.2 — Cooldown Editor Overhaul

#### Changed
- Manual trigger type removed — only buff_add, buff_remove, cast_success remain
- Preset click arms timers for listening (no immediate-start behavior)
- Fuzzy spell name matching with case-insensitive + trailing rank stripping
- In-game header removed — preset buttons sit at top of panel
- MAX_BARS / MAX_ACTIVE increased to 10
- Fixed side-by-side layout (260px left panel, no PanedWindow)
- Browse button restyled from emoji to ttk.Button
- Color presets replaced with Canvas swatches
- Preview canvas enlarged to 280px

#### Added
- "+ Add Timer" button in preset section
- Multi-ID buff warning dialog
- Preset button divider line
- Trigger collision validation
- Warning threshold validation (reject threshold >= duration)

#### Fixed
- Empty presets no longer generate useless in-game buttons
- Preview dimensions match AS2 template exactly
- Preview font sizes hardcoded to match AS2

### v3.3.1 — Console Enhancements

#### Added
- Pinnable console with "Keep Open" checkbox
- Per-side logging toggles (player/target)
- Console state persistence via config archive

#### Changed
- Buff logging gated on console.isActive() instead of previewMode

#### Fixed
- AS2 reserved keyword collision (lt → clp/clt)

#### UI Polish
- Card hover highlight with debounced enter/leave
- Card click-to-toggle on Welcome tab
- bind_card_events() utility in ui_helpers.py
- Child window positioning centered on main app
- Child window withdraw/deiconify jump prevention

### v3.3.0 — Cooldown Tracker Rewrite

#### Added
- Flat CooldownTimer data model replacing loop/step/action
- TimerManager.as engine with trigger maps and countdown bars
- Cooldown Editor UI with timer list, detail panel, preset checkboxes
- Bar-based in-game UI (fill/drain bars instead of text lines)
- Per-timer appearance: bar color, warning color, direction, retrigger mode
- v1→v2 migration for old loop editor profiles
- ColorSwatch reusable widget
- Scrollable frame helper

#### Changed
- Two-class AS2 architecture: KzTimers.as (shell) + TimerManager.as (engine)
- Global mousewheel handler rewritten (walks widget tree)
- Window position withdraw/deiconify pattern
- Debounced position save (300ms)

#### Removed
- Dot colors, loop/step/action model, old KzLoopEngine architecture

### v3.2.0 — Tab Restructure & Timers Customization

#### Added
- KzTimers visual customization sub-tab (colors, fonts, shadow, border, opacity)
- KzTimers preview mode with orange overlay and bounded drag
- Per-tab Build buttons for individual module compilation
- Standalone Stopwatch tab (promoted from Timers sub-tab)
- Live Tracker as independent window from Welcome screen
- Module visibility toggle with config archive persistence
- 17 compile-time AS2 placeholders for timers appearance
- Global status bar

#### Changed
- Tab order: Welcome, Grids, Castbars, Timers, Stopwatch, DamageNumbers
- Welcome screen absorbed Build tab functionality
- Normal-mode drag removed from KzTimers (preview only)

#### Removed
- Build tab (functionality moved to Welcome + per-tab buttons)
- Live Tracker tab (replaced by independent window)

### v3.1.0 — Raid Leader Toolkit

#### Added
- KzStopwatch SWF — self-contained stopwatch with 23 compile-time placeholders, two layouts, preview mode
- Multi-loop engine — KzTimers split into shell + KzLoopEngine (replaced by cooldown tracker in v3.3.0)
- Loop Editor redesign with select-to-edit presets and 3 slot combos (replaced in v3.3.0)
- Live Tracker tab extracted from Timers
- Buff database picker for Loop Editor
- AS2-accurate preview canvases for stopwatch and timers
- Clickable color swatches across all tabs

#### Changed
- Preset model: label + slots list (max 3 presets, 3 loops each)
- Two-template code generation (KzTimers.as + KzLoopEngine.as)
- compile_as2() multi-file support

### v3.0.0 — Safety & Consistency

#### Changed
- Atomic builds — compile to staging, install only on full success
- Honest build summary with per-module status
- Save errors visible via Messagebox (replaced silent print())
- Compiler validation before any build work
- Unified tab patterns: all extend ttk.Frame, consistent method names
- Profile label encapsulation and shared profile bar helper
- Pre-v3.0 migration code removed

#### Fixed
- Profile load safety — JSON parsed before discarding unsaved changes
- DamageInfo color validation on FocusOut/Return
- Double console guard in KzGrids
- Threshold 0 support (disables flash entirely)

### v2.9.2 — Darkly Theme & Global Profiles

#### Added
- ttkbootstrap darkly theme migration (~106 color replacements)
- Theme system: THEME_COLORS, TK_COLORS, style helpers
- Alt-toggle menu bar, ColorChooserDialog, dark title bars
- Global profile system (all tabs + module enable flags)
- Disabled module cleanup during Build All
- XML backup and restore
- Profile indicator bar on all tabs

### v2.9.1 — Kaz Flash Modz Rebrand

- Renamed from KzGrids Builder to Kaz Flash Modz
- Welcome tab with module overview cards
- Unified build pipeline for all modules
- ui_helpers.py extraction with shared constants
- Major duplication removal (~350+ lines)
- Function decomposition across build pipeline
- Error handling improvements (specific exception types)

### v2.8.0 — Castbars Module

- KzCastbars tab with per-bar colors, font customization, timer estimation
- 6 bar styles, text positioning, default castbar hiding
- Preview mode with independent overlay

### v2.7.0 — DamageInfo Module

- DamageInfo tab with 19 offset-based settings
- Per-type color customization and TextColors.xml generation
- 3 animation presets

### v2.6.x — Grid Enhancements

- Grid enable/disable toggle, stack counter display
- Database v2 format with ids array and type field
- Text shadow system, misc type priority in layout

### v2.5.x — Timer & Preview Polish

- Configurable timer flash threshold, timer Y-offset
- Preview overlay improvements, MiscSlot support

### v2.4.0 — Foundation

- Multi-ID buff support, Add Grid wizard redesign
- Removed grid count limits
