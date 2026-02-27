# KzGrids Module Reference

## Grid Configuration Model

```javascript
{
    id: "GridName",
    enabled: true,
    type: "player" | "target",
    rows: 1-64,
    cols: 1-64,
    iconSize: 24-64,
    gap: -5 to 10,
    x: 0-2560,
    y: 0-1440,
    slotMode: "dynamic" | "static",
    showTimers: true,
    timerFontSize: 8-24,
    timerFlashThreshold: 0-11,
    timerYOffset: -10 to +10,
    enableFlashing: true,
    fillDirection: "LR" | "RL" | "TB" | "BT" | "TL-BR" | etc.,
    sortOrder: "shortest" | "longest" | "application",
    layout: "buffFirst" | "debuffFirst" | "mixed",  // misc always first
    whitelist: [buffId1, buffId2, ...],
    slotAssignments: {0: [id1, id2], ...}
}
```

**Limits:** Max 64 total slots across all grids. Icon scale 24-64px.

---

## Tab UI

- **CollapsibleSection** per grid — clickable header with summary display (source, size, mode), expands to full editor
- **Profile info bar** at top — shows profile name, grid count, total slot count
- **Per-tab Build button** — compiles KzGrids.swf directly to game directory
- **Import/Export** — individual grid import/export buttons
- **Dialogs**: AddGridWizard, BuffSelectorDialog (dual listbox), SlotAssignmentDialog

---

## Buff Entry Structure

```actionscript
{
    buff: Object,    // Game's buff object
    id: Number,      // Buff ID
    exp: Number,     // Expiry time (getTimer() + remaining)
    isD: Boolean,    // Is debuff
    type: String,    // "buff" | "debuff" | "misc"
    at: Number       // When added (getTimer())
}
```

## Slot Type Determination

```actionscript
var slotType:String = "BuffSlot";
if (entry.type == "misc") slotType = "MiscSlot";
else if (entry.isD) slotType = "DebuffSlot";
```

---

## Database Format (v2)

```json
{
    "version": 2,
    "buffs": [
        {
            "name": "Born from the Dragon's Spine",
            "ids": [5052177],
            "category": "#BossT6",
            "type": "buff"
        },
        {
            "name": "Ethereal Lash",
            "ids": [4281285, 4281287, 4281288, 4281289],
            "category": "#BossT3",
            "type": "debuff",
            "stacking": true
        }
    ]
}
```

**Fields:** `ids` (always array), `type` (buff/debuff/misc), optional `stacking`, `stackStart`, `stackEnd`

**Categories:** `#BossT3`, `#BossT3.5`, `#BossT4`, `#BossT5`, `#BossT6`, `#Global`, class names

**Types:** `buff` (gray border), `debuff` (red border), `misc` (golden border)

---

## Preview Mode

- **Activate:** `Ctrl+Shift+Alt` in-game
- **Features:** Grid dragging, coordinate display, buff ID console
- **Boundaries:** Grids constrained to screen edges
- **Vertical bars:** When `cols == 1` and `rows > 1`, overlay text rotates 90°

## Console Features (v3.3.1)

### Pinnable Console
- **"Keep Open" checkbox** (bottom-left of console title bar) — when checked, the console persists outside Preview Mode
- Pinned console auto-reopens on module activation if previously pinned
- State saved via config archive key `console_pin` (boolean)

### Logging Toggles
- **Player / Target column checkboxes** in console header — enable/disable buff logging per side
- Useful for filtering noise when discovering buff IDs for one side only
- States saved via config archive keys `clp` (player), `clt` (target)

### `KzGridsConsole.isActive()`
- Returns `true` when `consoleClip` exists (console is visible)
- `SlotPBuffAdd` / `SlotTBuffAdd` signal handlers check `console.isActive()` instead of `previewMode` to decide whether to log
- This enables buff logging whenever the console is visible (pinned or in preview)

### Console Checkbox Pattern
- Reuses the KzTimers/KzStopwatch checkbox visual: 12x12 box, green checkmark, transparent hit area
- Drag handle created at lower depth so checkboxes receive clicks in title bar area

## Timer Flash

Both timer text color AND icon flash use `timerFlashThreshold` (default 6s, configurable 0-11s per grid). Setting threshold to 0 disables both colored timer text and icon flashing.

---

## Files

```
Modules/
├── grids_tab.py            # UI (CollapsibleSection per grid, per-tab Build button)
├── grids_generator.py      # CodeGenerator class + build_grids()
├── as2_template.py         # KzGrids AS2 runtime template
└── database_editor.py      # Buff database editor (BuffDatabase, BuffEditDialog, DatabaseEditorTab)

assets/kzgrids/
├── base.swf, base.fla
└── stubs/
    ├── com/Utils/ID32.as, ImageLoader.as
    ├── KzGridsPreview.as
    ├── KzGridsConsole.as
    └── KzGridsSlot.as
```
