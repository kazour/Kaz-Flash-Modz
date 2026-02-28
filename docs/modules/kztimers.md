# KzTimers Module Reference

## Architecture

```
Python Editor (Timers Tab — sub-notebook)
    ├── Cooldown Editor sub-tab
    │   ├── TimersEditorPanel (UI) — 2-column layout:
    │   │   ├── Col 0: Preview canvas + Appearance settings (no scrollbar)
    │   │   └── Col 1: Presets + Timer list (Add/Edit/Delete/Delete All + Database)
    │   ├── TimerEditorDialog — modal dialog for adding/editing individual timers
    │   ├── timers_data.py — CooldownTimer, CooldownPreset, CooldownSettings
    │   └── timers_generator.py — Generates KzTimers.as + TimerManager.as + MTASC compile
    ├── Customization sub-tab
    │   └── timers_appearance.py — Appearance settings, defaults, validation, I/O
    └── Per-tab Build button (compiles to game directory)

KzTimers (In-Game)
    ├── KzTimers.as — Shell: UI, bar pool, preset buttons, preview mode, lifecycle
    ├── TimerManager.as — Engine: trigger maps, active timer tracking, countdown state
    ├── Preset buttons (up to 3)
    └── Buff/cast signal hooks (player + target)
```

---

## Cooldown Timer Data Model

Each timer is a flat `CooldownTimer` — one tracked ability cooldown:

```javascript
{
    id: "rune_of_aggression",
    name: "Rune of Aggression",
    enabled: true,
    triggerType: "cast_success",        // buff_add | buff_remove | cast_success
    triggerSource: "player",            // "player" or "target"
    triggerBuffId: null,                // For buff_add / buff_remove triggers
    triggerBuffName: null,              // Display name from database (display-only, optional)
    triggerSpellName: "Rune of Aggression",  // For cast_success triggers
    duration: 40,                       // Cooldown duration in seconds
    warningThreshold: 5,                // Seconds remaining → switch to warning color
    barColor: 0x99DD66,                 // Main bar fill color (compiled as Number)
    warningColor: 0xFF7744,             // Bar color when warning active (compiled as Number)
    barDirection: "empty",              // "empty" = drain, "fill" = fill up
    countDirection: "descending",       // "descending" = N→0, "ascending" = 0→N
    retrigger: "restart"                // "restart" = reset timer, "ignore" = no-op
}
```

## Trigger Types

| Type | Description | Use Case |
|------|-------------|----------|
| `buff_add` | Buff ID appears on player/target | Track buff durations |
| `buff_remove` | Buff ID removed from player/target | Start cooldown when buff fades |
| `cast_success` | Spell completes casting | Track ability cooldowns |

### Spell Name Fuzzy Matching (cast_success)

Cast success triggers use fuzzy matching — both the configured spell name and the incoming game spell name are normalized before comparison:
- Lowercased
- Trailing rank stripped: Roman numerals (I–X) and Arabic numbers (1–10)

Example: User types `"slow death strike"`, game sends `"Slow Death Strike IV"` → both normalize to `"slow death strike"` → match.

Normalization is done in both Python (`_normalize_spell_name()` in `timers_generator.py`) and AS2 (`normalizeSpell()` in `TimerManager.as`).

### Buff ID — Single ID Only

Each timer accepts a single buff ID. When the buff database picker returns a stacking buff with multiple IDs, the user is warned and only the first ID is used.

## Presets

Presets are named groups of timers activated together:

```javascript
{ label: "Default", timerIds: ["rune_of_aggression", "steadfast_faith"] }
```

Up to 3 presets, max 10 timers per preset, labels max 4 characters. Clicking a preset button in-game **arms** its assigned timers for listening — they start counting down only when their trigger event fires (buff add/remove, cast success). There is no immediate-start behavior.

---

## Timers Customization

The Customization sub-tab provides visual customization of the in-game panel. Settings are injected as compile-time `%%PLACEHOLDER%%` values into `KzTimers.as.template`.

### Appearance Settings (from `timers_appearance.py`)

```javascript
{
    bar_height: 20,             // 14-28 px
    font_size: 11,              // 8-20
    font_bold: true,
    show_decimals: true,        // Show .N tenths in countdown
    text_offset_x: 0,           // -10 to 10 px
    text_offset_y: 0,           // -10 to 10 px
    shadow_enabled: false,
    shadow_color: "111111",
    bg_opacity: 85,             // 0-100%
    colors: {
        background: "0D0D0D",  // Panel background
        text: "FFFFFF",        // Default text color
        border: "3A3A30",      // Panel border
    },
    border_width: 2,            // 1-4 px
    corner_radius: 0,           // 0-12 px
    pos_x: 100,                 // 0-3840
    pos_y: 100,                 // 0-2160
    button_shape: "rounded",    // "square" / "rounded" / "pill"
    button_colors: {
        bg: "1A1A18",          // Preset button background
        border: "4A4A40",      // Preset button border
        hover: "2A2A24",       // Preset button hover
        active_text: "FF6666", // Active preset text color
        inactive: "CCCCCC",    // Inactive preset text color
    },
}
```

### Compile-Time Placeholders

#### KzTimers.as Placeholders

| Placeholder | Source |
|-------------|--------|
| `%%PRESETS_ARRAY%%` | Preset object literals |
| `%%NEEDS_PLAYER_SIGNALS%%` | Whether any timer needs player signals |
| `%%NEEDS_TARGET_SIGNALS%%` | Whether any timer needs target signals |
| `%%PANEL_WIDTH%%` | Panel width (fixed 240px) |
| `%%BAR_HEIGHT%%` | `bar_height` |
| `%%GROW_DIRECTION%%` | "down" or "up" |
| `%%MAX_BARS%%` | `MAX_TIMERS_PER_PRESET` (bar pool size) |
| `%%BG_OPACITY%%` | `bg_opacity` |
| `%%COLOR_BG%%` | `colors.background` |
| `%%COLOR_TEXT%%` | `colors.text` |
| `%%COLOR_BORDER%%` | `colors.border` |
| `%%BORDER_WIDTH%%` | `border_width` |
| `%%CORNER_RADIUS%%` | `corner_radius` |
| `%%FONT_SIZE%%` | `font_size` |
| `%%FONT_BOLD%%` | `font_bold` (true/false) |
| `%%SHADOW_ENABLED%%` | `shadow_enabled` (true/false) |
| `%%SHADOW_COLOR%%` | `shadow_color` |
| `%%TEXT_OFFSET_X%%` | `text_offset_x` |
| `%%TEXT_OFFSET_Y%%` | `text_offset_y` |
| `%%POS_X%%` | `pos_x` |
| `%%POS_Y%%` | `pos_y` |
| `%%BUTTON_SHAPE%%` | `button_shape` |
| `%%COLOR_BUTTON_BG%%` | `button_colors.bg` |
| `%%COLOR_BUTTON_BORDER%%` | `button_colors.border` |
| `%%COLOR_BUTTON_HOVER%%` | `button_colors.hover` |
| `%%COLOR_BUTTON_ACTIVE%%` | `button_colors.active_text` |
| `%%COLOR_BUTTON_INACTIVE%%` | `button_colors.inactive` |

#### TimerManager.as Placeholders

| Placeholder | Source |
|-------------|--------|
| `%%TIMERS_ARRAY%%` | Timer config object literals |
| `%%COLOR_TEXT%%` | `colors.text` (default text color) |
| `%%MAX_ACTIVE%%` | `MAX_TIMERS_PER_PRESET` (active timer cap) |
| `%%SHOW_DECIMALS%%` | `show_decimals` (true/false) |

---

## In-Game Architecture

### TimerManager.as (Engine)

- Holds all timer configs in `allTimers` array (compiled-in)
- Timer colors (`barColor`, `warningColor`) are pre-parsed to Number at compile time (e.g. `0x99DD66`) — no runtime string-to-hex conversion
- Builds trigger maps on init: `buffAddMap[buffId]`, `buffRemMap[buffId]`, `castMap[normalizedSpellName]`
- `normalizeSpell(s)` — lowercases and strips trailing rank (Roman I–X, Arabic 1–10) for fuzzy cast matching
- `onBuffAdded(id, source)` / `onBuffRemoved(id, source)` / `onCastEnded(spell, source)` — check trigger maps, start timers
- `startOrRetrigger(cfg)` — if timer already running: restart or ignore based on `retrigger` mode
- `update(now)` — removes expired timers (swap-with-last removal), receives timestamp from caller
- `getTimerState(index, now)` — returns `{label, timeStr, progress, color, id}` from pooled state objects (zero allocation per call)
- `setEnabledTimers(timerIds)` / `restoreOriginalEnabled()` — preset support
- `MAX_ACTIVE = 10` — up to 10 simultaneous countdown bars

### KzTimers.as (Shell/UI)

- Creates panel with border, background, preset buttons (no title header)
- `HEADER_HEIGHT = 4` (small top padding), preset buttons sit at the top of the panel
- Bar pool: creates bar MovieClips on demand (`createBarInPool`), `MAX_BARS = 10`
- Each bar has: track background, fill (scaled via `_xscale`), label + time TextFields, optional shadow
- `updateDisplay()` — called every ~33ms when active via `setInterval`; single `getTimer()` call shared across all operations
- Bar fill uses `_xscale` for smooth progress — only redraws on color change (warning threshold)
- Label TextFields only updated when timer identity changes at that bar slot
- Time TextFields only updated when the formatted string changes
- `resizePanel(barCount)` — cached, only redraws when active timer count changes
- Preset click arms timers for listening (calls `setEnabledTimers()` only, no immediate start)
- Signal system: connects to player/target buff and cast signals via AoC API

---

## KzTimers Lifecycle

1. **Frame script** creates `new KzTimers(this)` → calls `m_Module.onLoad()`
2. `onLoad()` → `initialize()` → creates timer UI immediately
3. AoC may call `OnModuleActivated(archive)` → restores saved position + visibility + active preset
4. `OnModuleDeactivated()` → saves position to config archive

`onLoad()` calls `initialize()` as fallback so timer is visible even without `OnModuleActivated`.

---

## Preview Mode

Same pattern as KzStopwatch, KzGrids, and KzCastbars:

- **Toggle**: `Ctrl+Shift+Alt` (all three held simultaneously)
- **Overlay**: Created on `rootClip` at depth 9000
- **Appearance**: White 2px border (80% opacity), orange fill (0xF39C12, 20% opacity)
- **Coordinates**: "KzTimers X:N Y:N" centered in overlay, updates live during drag
- **Drag**: Overlay is draggable within screen bounds; `m_Timer` position syncs
- **Visibility checkbox**: 12x12 toggle at bottom-right — module hidden by default
- **No normal-mode drag**: Panel only movable in preview mode

---

## Build Process

1. User configures timers in Cooldown Editor, appearance in Customization sub-tab
2. `timers_generator.py` generates `KzTimers.as` (shell) and `TimerManager.as` (engine)
3. Appearance placeholders replaced in `KzTimers.as.template`
4. Timer configs and presets injected into `TimerManager.as.template`
5. MTASC compiles both `.as` files into one SWF (multi-file compilation)
6. Output: `KzTimers.swf` → game Flash folder
7. In-game: `/reloadui`

---

## Default Settings

Default settings start with an **empty timer list** — no sample timer is included. Users add timers via the Add button, which opens the `TimerEditorDialog`.

---

## Files

```
Modules/
├── timers_tab.py               # Timers tab with sub-notebook (Cooldown Editor + Customization)
├── timers_appearance.py        # Appearance defaults, validation, settings I/O
├── live_tracker_settings.py    # Live Tracker overlay settings (separate from appearance)
├── timers_data.py              # CooldownTimer, CooldownPreset, CooldownSettings + validation
├── timers_editor.py            # Cooldown Editor panel UI (2-column: preview+appearance | presets+timers)
├── timers_editor_dialog.py     # Cooldown Editor dialog (add/edit timer form)
└── timers_generator.py         # KzTimers + TimerManager code generation + MTASC build

assets/flash_timer/
├── base.swf                    # Embedded Arial font, frame 1 entry point
├── base.fla                    # Flash CS6 source (binary)
├── KzTimers.as.template        # Shell: bar UI, preset buttons, preview, lifecycle
├── TimerManager.as.template    # Engine: trigger maps, active timers, countdown state
└── README.md
```
