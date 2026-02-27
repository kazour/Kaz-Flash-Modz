# KzStopwatch Module Reference

## Architecture

```
KzStopwatch.as (single class, ~1330 lines)
    ├── m_Panel (MovieClip container)
    │   ├── border / bg (panel frame)
    │   ├── presetBtns[] (P1/P2/P3 buttons, standard only)
    │   ├── divider / divider2 (horizontal divider lines, standard only)
    │   ├── phaseText (phase name TextField, standard only)
    │   ├── shadowText / timerText (timer display)
    │   └── startBtn / pauseBtn / stopBtn (control buttons)
    ├── Preview overlay (created on rootClip at depth 9000)
    └── Key listener (Ctrl+Shift+Alt toggle)
```

Self-contained — no API signals, no helper classes. Standalone top-level tab (promoted from Timers sub-tab in v3.2.0).

---

## Configuration Model

28 compile-time placeholders injected via `%%KEY%%` replacement:

```javascript
// Appearance (24 placeholders)
{
    layout: "standard",         // "standard" | "compact"
    width: 220,                 // 120-400 px
    height: 120,                // 40-200 px
    font_size: 28,              // 12-48 px
    phase_font_size: 12,        // 8-24 px
    bg_opacity: 85,             // 0-100%
    colors: {
        background: "0D0D0D",   // 6-char hex
        text: "CCCCCC",
        border: "3A3A30",
    },
    border_width: 2,            // 1-4 px
    corner_radius: 0,           // 0-12 px
    font_family: "Arial",       // Hardcoded — only Arial is embedded in SWF
    shadow_enabled: true,
    shadow_color: "111111",
    button_shape: "rounded",    // "square" | "rounded" | "pill"
    button_colors: {
        bg: "1A1A18",
        border: "4A4A40",
        hover: "2A2A24",
        start: "99DD66",
        pause: "FFE066",
        stop: "FF7744",
        disabled: "555555",
    },
    pos_x: 400,                 // 0-3840
    pos_y: 300,                 // 0-2160
}

// Preset (4 placeholders)
{
    num_presets: 3,                     // Number of presets with phases
    presets_array: [{...}, ...],        // AS2 object literal array
    button_colors: {
        preset_active: "FF6666",        // Active preset label color
        preset_inactive: "CCCCCC",      // Inactive preset label color
    },
}
```

### Preset Data Format (baked into PRESETS_ARRAY)

Each preset is an AS2 object literal:
```actionscript
{label: "SC", endBehavior: "loop", countDir: "ascending", totalDur: 180000,
 phases: [{name: "Phase 1", dur: 60000, color: 0xFF6666}, ...]}
```

---

## Timer State Machine

```
idle ──Start──▶ running ──Pause──▶ paused
  ▲                │                  │
  └──Stop──────────┘──────Stop────────┘
```

- **idle**: Display "0:00:00", Start enabled (green), Pause/Stop disabled (grey)
- **running**: Timer counts up at 50ms interval, Pause enabled (yellow), Stop enabled (orange)
- **paused**: Timer frozen, Start re-enabled (green), Stop enabled (orange)

Display format: `H:MM:SS` always (unpadded hours, no tenths).

---

## Preset System

- 3 presets (P1/P2/P3), each with up to 10 phases
- Each phase: name (string), duration (seconds), color (hex)
- Per-preset settings: label (max 4 chars), end behavior, count direction
- **End behaviors**: loop (restart from phase 1), end (stop timer), continue (keep counting past total)
- **Count direction**: ascending (0 → total) or descending (total → 0)
- Clicking an active preset deactivates it and stops the timer
- Clicking an inactive preset activates it and starts immediately
- Phase text shows current phase name with phase color
- Timer text color matches current phase color when preset is active

---

## Preview Mode Design

Same pattern as KzGrids, KzCastbars, and KzTimers:

- **Toggle**: `Ctrl+Shift+Alt` (all three held simultaneously)
- **Overlay**: Created on `rootClip` (sibling of `m_Panel`, not child) at depth 9000
- **Appearance**: White 2px border (80% opacity), purple fill (0x9B59B6, 20% opacity)
- **Coordinates**: "KzStopwatch X:N Y:N" centered in overlay, updates live during drag
- **Drag**: Overlay background is draggable within screen bounds; `m_Panel` position syncs in `onMouseMove`
- **Visibility checkbox**: 12x12 toggle at bottom-right of overlay — green checkmark when enabled. Module is hidden by default; user must check the box to make it visible after exiting preview. State persisted via config archive (`"visible"` key).
- **Entry**: Panel becomes visible during preview regardless of hidden state
- **Exit**: Removes overlay, applies visibility based on checkbox, saves state to config

**Key listener**: Uses `Key.addListener(this)` with class methods `onKeyDown()`/`onKeyUp()` for duplicate-safe listening; `Key.removeListener(this)` in `cleanup()` prevents listener accumulation.

**Compiled position**: X/Y position is baked into the SWF at build time (clamped to screen bounds on init). No config archive persistence for position — user sets position in Python UI, rebuilds SWF. Visibility state is persisted via config archive.

---

## Layouts

### Standard
- Full-width panel with border, background, optional corner radius
- Layout constants: HEADER_HEIGHT=4, PRESET_ROW_HEIGHT=30, BTN_HEIGHT=20
- **Top**: Preset buttons (P1/P2/P3) centered, with top divider below
- **Middle**: Phase text + timer text centered as a block between top and bottom divider lines
- **Bottom**: Bottom divider, then control buttons (Start/Pause/Stop) row
- Shadow text at +1/+1 offset (when enabled)
- Button shapes: square (r=0), rounded (r=3), pill (r=half height)

### Compact
- Thin horizontal strip — simple stopwatch only (no preset/phase support)
- Timer text centered in available space left of control buttons
- 3 mini square buttons (S/P/X) on right side
- Button size: `min(22, floor(height * 0.55))` with minimum 12px

---

## Build

```bash
# Copy base.swf to temp, compile AS2 into it
mtasc.exe -cp "assets/common_stubs" -swf "KzStopwatch_temp.swf" \
  -version 8 "KzStopwatch.as"
```

Uses its own `base.swf` with embedded Arial font and frame 1 entry point (`new KzStopwatch(this)`). No `-main` flag — the base.swf frame script handles initialization, same pattern as KzTimers.

---

## Python Files

```
Modules/
├── stopwatch_tab.py           # Thin shell — per-tab Build button, profile support
├── stopwatch_editor.py        # Two-column editor (preview+appearance | presets+phases)
├── stopwatch_phase_dialog.py  # Modal dialog for add/edit phase (name, duration, color)
├── stopwatch_data.py          # StopwatchPhase, StopwatchPreset, StopwatchPresetSettings dataclasses
├── stopwatch_settings.py      # Appearance defaults, validation, I/O
└── stopwatch_generator.py     # Template loading, placeholder replacement, MTASC build

assets/flash_stopwatch/
├── KzStopwatch.as.template    # %%PLACEHOLDER%% markers (~1330 lines)
└── base.swf                   # Own base.swf with KzStopwatch frame 1 entry point
```
