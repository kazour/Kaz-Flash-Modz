# AoC Module System & Config Archive — Technical Reference

## Overview

Age of Conan's GUI framework provides a **module system** for managing SWF addons. Modules registered through this system get lifecycle callbacks, config archive persistence, and automatic reload on `/reloadui`. This document covers how the system works, how our modules integrate with it, and the current state of each module.

---

## 1. The Module System

### How AoC Discovers Modules

The game's GUI manager reads module definitions from `Modules.xml`. Each entry defines a SWF to load and the conditions under which it should be active.

**File priority:** The game checks `Customized/Modules.xml` first, falls back to `Default/Modules.xml`. The game compiles XML → `.bxml` (binary XML) for faster loading.

**Module definition format** (`Modules.xml.add` → merged into `Modules.xml`):
```xml
<Module
    name              = "KzGrids"
    movie             = "KzGrids.swf"
    flags             = "GMF_CFG_STORE_USER_CONFIG"
    depth_layer       = "Top"
    sub_depth         = "0"
    variable          = "KzGrids"
    criteria          = "KzGrids &amp;&amp; (guimode &amp; (GUIMODEFLAGS_INPLAY | GUIMODEFLAGS_ENABLEALLGUI))"
    config_name       = "KzGrids settings"
/>
```

| Attribute | Purpose |
|-----------|---------|
| `name` | Internal identifier |
| `movie` | SWF filename (loaded from `Default/Flash/`) |
| `flags` | `GMF_CFG_STORE_USER_CONFIG` enables config archive persistence |
| `depth_layer` | Rendering layer (`Top` = above most game UI) |
| `variable` | Boolean variable name in MainPrefs (controls enable/disable) |
| `criteria` | Load condition — variable must be true AND player must be in play mode |
| `config_name` | Archive name in MainPrefs for persistent storage |

### MainPrefs Registration

Each module needs two entries in `MainPrefs.xml`:

```xml
<Value name="KzGrids" value="true" />       <!-- Enable flag (criteria variable) -->
<Archive name="KzGrids settings" />          <!-- Config archive storage -->
```

**MainPrefs.xml** only exists in `Default/` — the game never looks for it in `Customized/`. The standard launcher **restores** `Default/` files on every launch, which is why the Aoc.exe launcher bypass is required (see Section 4).

### Module Lifecycle

When the game loads a registered module SWF:

1. Game loads the SWF into a MovieClip (`root`)
2. Frame 1 script runs — creates class instance, assigns to `m_Module`, calls `onLoad()`
3. Game calls `root.OnModuleActivated(archive)` — a **root-timeline function** (NOT `root.m_Module.OnModuleActivated`)
4. Frame script delegates to `m_Module.OnModuleActivated(archive)` — stores archive, reads saved state
5. On unload (logout, `/reloadui`), game calls `root.OnModuleDeactivated()`
6. Frame script delegates to `m_Module.OnModuleDeactivated()` — saves state, cleans up, returns archive
7. Game persists the returned archive to `Prefs_X.xml` for next activation

**Critical:** AoC calls lifecycle methods on the **root timeline**, not on `m_Module` directly. Every module MUST have `OnModuleActivated`/`OnModuleDeactivated` delegation functions in its base.fla frame 1 script. Without delegation, the game never passes the config archive to the class.

### Config Archive Storage

Archives are persisted in `%LOCALAPPDATA%\Funcom\Conan\Prefs\Prefs_X.xml` (where X is the character slot). Example:
```xml
<Archive name="KzTimers settings">
    <Double name="visible" value="0.000000" />
    <Double name="y" value="737.000000" />
    <Double name="x" value="463.000000" />
</Archive>
```

### Alternative: `/loadclip` Scripts

Modules can also be loaded via `/loadclip` commands in auto_login scripts. This method:
- Does NOT provide config archive persistence
- Does NOT survive `/reloadui` (module must be manually reloaded via `/reloadgrids` or similar)
- Does NOT call `OnModuleActivated` / `OnModuleDeactivated`
- Simply loads the SWF and calls `onLoad()` on the root timeline
- Works as a fallback when the module system isn't available

---

## 2. The Config Archive

### What It Is

The config archive is an opaque `Object` provided by the game engine. It acts as a key-value store that the game persists across sessions. Each module gets its own archive (identified by `config_name` in `Modules.xml`).

### API

```actionscript
// Read a value (returns the value, or undefined if key doesn't exist)
var value:Object = config.FindEntry("keyName");

// Write/update a value (creates key if missing, updates if exists)
config.ReplaceEntry("keyName", value);
```

Values can be numbers, strings, or simple objects. The game serializes/deserializes them automatically.

### Lifecycle Integration

```
OnModuleActivated(archive)     ← Game passes saved archive
    ↓
config = archive               ← Module stores reference
config.FindEntry("x")          ← Module reads saved state
    ↓
[Module runs, user interacts]
    ↓
config.ReplaceEntry("x", 150)  ← Module writes state changes
    ↓
OnModuleDeactivated()          ← Game requests archive back
return config                  ← Module returns archive for persistence
```

### Critical Rules

1. **`OnModuleDeactivated` MUST return the archive.** If it returns `null` or `undefined`, the game loses all persisted state for that module. This is the most common mistake.

2. **`OnModuleActivated` return value is optional.** Analysis of the original kazbars v1 (which worked correctly) shows it returned `undefined` (Void) from `OnModuleActivated`. The game keeps its own reference to the archive — it only needs it back from `OnModuleDeactivated`.

3. **`FindEntry` returns `undefined` for missing keys**, not `null`. Always check with `=== undefined` or use a default: `var x = config.FindEntry("x"); if (x === undefined) x = defaultValue;`

4. **Call `ReplaceEntry` at save points**, not continuously. Good save points: `exitPreview()`, `OnModuleDeactivated()`, `onRelease` after drag.

---

## 3. Module Attachment Patterns

### Pattern A: Frame Script (kazbars v1 — original)

The original kazbars v1 used a **frame script** approach. All code runs on the root timeline. The game finds the lifecycle functions directly on the root MovieClip — no explicit `m_Module` assignment needed because `root` IS the module.

```actionscript
// Frame 1 script — runs on root timeline
// 'this' == root MovieClip

var config;

function OnModuleActivated(archive)
{
    config = archive;
    LoadSavedPosition();    // Read state BEFORE initializing UI
    onLoad();               // Initialize
    // No return — game keeps its own archive reference
}

function OnModuleDeactivated()
{
    SavePosition();         // Save ALL element positions
    cleanupAll();           // Teardown
    return config;          // MUST return archive
}

function onLoad()
{
    // Normal initialization — also called by /loadclip (no archive)
    Stage.showMenu = false;
    Key.addListener(this);
    initializeSystem();
    // Connect signals...
}
```

**Key characteristics:**
- Single SWF contains everything (buffs, castbars, grids — all in one file)
- Functions defined at root scope = game finds them automatically
- No class, no `m_Module` assignment
- `onLoad()` works both via module system (after `OnModuleActivated`) and via `/loadclip` (standalone)

### Pattern B: Class with Frame Script Delegation (ALL current modules)

All modules use MTASC-compiled classes with a **mandatory frame 1 script** in base.fla that handles instance creation and lifecycle delegation.

```actionscript
// base.fla frame 1 script (REQUIRED for all modules):
function onLoad()
{
   m_Module = new KzTimers(this);
   m_Module.onLoad();
}
function OnModuleActivated(archive)
{
   if (m_Module)
   {
      return m_Module.OnModuleActivated(archive);
   }
   return null;
}
function OnModuleDeactivated()
{
   if (m_Module)
   {
      return m_Module.OnModuleDeactivated();
   }
   return null;
}
var m_Module;
```

```actionscript
// Class code (compiled by MTASC into base.swf):
class KzTimers
{
    private var rootClip:MovieClip;
    private var config:Object;

    public function KzTimers(root:MovieClip)
    {
        rootClip = root;
    }

    public function OnModuleActivated(archive:Object):Object
    {
        config = archive;
        // Read saved state...
        return config;
    }

    public function OnModuleDeactivated():Object
    {
        // Save state to config...
        cleanup();
        return config;
    }

    public function onLoad():Void
    {
        // Init for both module system and /loadclip paths
        initialize();
    }
}
```

**Key characteristics:**
- Frame script creates the instance, sets `m_Module`, and delegates lifecycle calls
- AoC calls `root.OnModuleActivated()` / `root.OnModuleDeactivated()` on the **root timeline** — delegation to `m_Module` is mandatory
- `onLoad()` provides initialization for both paths: module system (after frame load) and `/loadclip` (standalone)
- `OnModuleActivated` does NOT re-init — just stores config and applies saved state (UI already created by `onLoad()`)
- `OnModuleDeactivated` MUST return the config archive or persistence is lost

**Note:** Some modules still have a `static main()` method (KzTimers, KzStopwatch) — this is dead code left from an earlier pattern. The frame script handles everything. Can be removed during future cleanup.

**Historical note:** Earlier versions had KzGrids/KzCastbars using frame scripts without lifecycle delegation. This caused broken archive persistence. All modules now use the same Pattern B with full delegation.

---

## 4. Aoc.exe Launcher Bypass

**Note:** `Aoc.exe` and the `.xml.add` files described below are **not part of the Kaz Flash Modz repository**. They are installed separately in the user's AoC game directory. Kaz Flash Modz only generates the SWF files.

### Problem

The standard AoC launcher restores `Default/MainPrefs.xml` and `Default/Modules.xml` on every launch. Any module registrations added to these files get wiped.

### Solution

`Aoc.exe` sits in `Data/Gui/Aoc/Kazbars/` (inside the game installation) and replaces the normal launcher:

1. Reads `.xml.add` files from addon directories under `Data/Gui/Aoc/`
2. Merges `MainPrefs.xml.add` → `Default/MainPrefs.xml` (appends entries before `</Root>`)
3. Merges `Modules.xml.add` → `Customized/Modules.xml` (game checks Customized first)
4. Copies SWFs from addon `Flash/` dirs to `Default/Flash/` (N/A for Kaz Flash Modz — we output directly)
5. Launches the game

### Directory Structure

```
Data/Gui/Aoc/Kazbars/
├── Aoc.exe                     ← Launcher bypass tool
├── MainPrefs.xml.add           ← Merged into Default/MainPrefs.xml
├── Modules.xml.add             ← Merged into Customized/Modules.xml
└── Flash/                      ← Old SWFs (DamageInfo.swf, kazcast.swf, timer.swf)
    └── (not used by Kaz Flash Modz — we write directly to Default/Flash/)
```

### .xml.add File Formats

**MainPrefs.xml.add** — Value + Archive pairs for each module:
```xml
<Value name="KzGrids" value="true" />
<Archive name="KzGrids settings" />
<Value name="KzCastbars" value="true" />
<Archive name="KzCastbars settings" />
<Value name="KzStopwatch" value="true" />
<Archive name="KzStopwatch settings" />
<Value name="KzTimers" value="true" />
<Archive name="KzTimers settings" />
```

**Modules.xml.add** — Full module definitions (see Section 1 for format).

### Without Aoc.exe

If the user doesn't use `Aoc.exe`, modules fall back to `/loadclip` scripts. The module system features (archive persistence, `/reloadui` survival) are unavailable. Modules still work but positions and visibility reset every session.

---

## 5. Current Module Status

**Note:** DamageInfo is excluded from this section. It's a decompiled game file, not a class-based MTASC module, and does not integrate with the AoC module system (no config archive, no lifecycle callbacks). See `docs/modules/damageinfo.md` for its architecture.

### KzTimers — COMPLETE
**File:** `assets/flash_timer/KzTimers.as.template`
**Pattern:** Class with frame script delegation (base.fla updated)

| Feature | Status | Implementation |
|---------|--------|----------------|
| `OnModuleActivated` | OK | Stores config, reads x/y, returns config |
| `OnModuleDeactivated` | OK | Saves x/y + visibility, cleans up, returns config |
| `m_Module` setup | In base.fla | Frame 1 script with lifecycle delegation (updated) |
| Position persistence | OK | 3 save points: drag `onRelease`, `exitPreview()`, `OnModuleDeactivated` |
| Visibility persistence | OK | `hideModule` → `FindEntry("visible")`/`ReplaceEntry("visible", ...)` |
| Signal disconnect | OK | `cleanup()` disconnects `SignalClientCharacterAlive`, player, and target signals |
| `/reloadui` survival | OK | Verified — position and visibility persist across `/reloadui` |
| `/loadclip` fallback | OK | `onLoad()` → `initialize()` with hardcoded (100, 100) default position |

**Archive keys:** `x`, `y`, `visible`

**Root cause of previous failure:** The old base.fla frame script lacked `OnModuleActivated`/`OnModuleDeactivated` delegation functions. AoC calls lifecycle methods on the **root timeline**, not on `root.m_Module`. Without frame script delegation, the game never passed the config archive to the class, leaving it null. Fixed by updating base.fla to the standard delegation pattern (same as all other modules).

### KzStopwatch — COMPLETE
**File:** `assets/flash_stopwatch/KzStopwatch.as.template`
**Pattern:** Class with frame script delegation (Pattern B) — has own base.swf with frame 1 entry point

| Feature | Status | Implementation |
|---------|--------|----------------|
| `OnModuleActivated` | OK | Stores config, returns config |
| `OnModuleDeactivated` | OK | Saves x/y, cleans up, returns config |
| `m_Module` setup | In base.fla | Frame 1 script with lifecycle delegation |
| Position persistence | OK | 3 save points: drag `onRelease`, `exitPreview()`, `OnModuleDeactivated`. Reads saved position in `initialize()` with compile-time fallback. |
| Visibility persistence | OK | Same pattern as KzTimers |
| `/reloadui` survival | OK | Verified — position and visibility persist across `/reloadui` |
| `/loadclip` fallback | OK | `onLoad()` → `initialize()` with compile-time `POS_X`/`POS_Y` |

**Archive keys:** `x`, `y`, `visible`

### KzGrids — COMPLETE
**File:** `Modules/as2_template.py`
**Pattern:** Class with frame script delegation (Pattern B)

| Feature | Status | Implementation |
|---------|--------|----------------|
| `OnModuleActivated` | OK | Stores config, applies saved per-grid positions (no re-init) |
| `OnModuleDeactivated` | OK | Saves per-grid positions, cleans up, returns config |
| `m_Module` setup | In base.fla | Frame 1 script with lifecycle delegation (updated) |
| Position persistence | OK | 2 save points: `exitPreview()`, `OnModuleDeactivated`. Per-grid indexed keys. |
| Visibility persistence | N/A | Grids auto-show/hide based on active tracked buffs |
| `/reloadui` survival | OK | Verified — per-grid positions persist across `/reloadui` |
| `/loadclip` fallback | OK | `onLoad()` creates grids at compile-time positions |

**Archive keys:** `g0_x`, `g0_y`, `g1_x`, `g1_y`, ... (indexed per grid)

### KzCastbars — COMPLETE
**File:** `assets/castbars/KzCastbars.as.template`
**Pattern:** Class with frame script delegation (Pattern B)

| Feature | Status | Implementation |
|---------|--------|----------------|
| `OnModuleActivated` | OK | Stores config, applies saved player/target bar positions (no re-init) |
| `OnModuleDeactivated` | OK | Saves bar positions, disconnects signals, returns config |
| `config` member var | OK | `private var config:Object` added |
| `m_Module` setup | In base.fla | Frame 1 script with lifecycle delegation (updated — `OnModuleActivated` added) |
| Position persistence | OK | 2 save points: `exitPreview()`, `OnModuleDeactivated`. Separate keys per bar. |
| Visibility persistence | N/A | Castbars auto-show during casts, auto-hide when done |
| `/reloadui` survival | OK | Verified — player and target bar positions persist across `/reloadui` |
| `/loadclip` fallback | OK | `onLoad()` creates castbars at compile-time positions |

**Archive keys:** `px`, `py` (player bar), `tx`, `ty` (target bar)

---

## 6. kazbars v1 Reference Analysis

The original kazbars v1 was a single SWF containing ALL functionality (buffs, castbars, grids). It used the frame script pattern (Pattern A) and had working config archive persistence.

### Position Persistence (4 elements, 8 keys)

```actionscript
function LoadSavedPosition()
{
    if (!config) return;
    var pos = {
        x:      config.FindEntry("x"),       // Player castbar X
        y:      config.FindEntry("y"),       // Player castbar Y
        xt:     config.FindEntry("xt"),      // Target castbar X
        yt:     config.FindEntry("yt"),      // Target castbar Y
        xgrid:  config.FindEntry("xgrid"),   // Grid X
        ygrid:  config.FindEntry("ygrid"),   // Grid Y
        xgridr: config.FindEntry("xgridr"),  // Grid R (right) X
        ygridr: config.FindEntry("ygridr")   // Grid R (right) Y
    };
    setPosition(m_Bar,   pos.x,     pos.y);
    setPosition(m_BarT,  pos.xt,    pos.yt);
    setPosition(m_Grid,  pos.xgrid, pos.ygrid);
    setPosition(m_GridR, pos.xgridr,pos.ygridr);
}

function SavePosition()
{
    if (!config) return;
    saveElementPosition(m_Bar,   "x",     "y");     // Player castbar
    saveElementPosition(m_BarT,  "xt",    "yt");     // Target castbar
    saveElementPosition(m_Grid,  "xgrid", "ygrid");  // Grid
    saveElementPosition(m_GridR, "xgridr","ygridr"); // Grid R
}

function saveElementPosition(element, keyX, keyY)
{
    if (!config || !element) return;
    config.ReplaceEntry(keyX, element._x);
    config.ReplaceEntry(keyY, element._y);
}

function setPosition(element, x, y)
{
    if (!element || x === undefined || y === undefined) return;
    element._x = Math.max(0, Math.min(x, Math.max(0, Stage.width - (element._width || 100))));
    element._y = Math.max(0, Math.min(y, Math.max(0, Stage.height - (element._height || 50))));
}
```

### Save Points

Position was saved at **three** points:
1. `OnModuleDeactivated()` — before returning archive
2. `exitPreview()` — when leaving preview mode
3. `onRelease` / `onReleaseOutside` — immediately after each drag operation

### Key Design Decisions

- **All elements shared one archive** (single `config` variable with unique key prefixes per element)
- **Positions loaded BEFORE `onLoad()`** — `OnModuleActivated` calls `LoadSavedPosition()` first, then `onLoad()`
- **Screen-clamped on load** — `setPosition()` clamps to `Stage.width`/`Stage.height` to prevent off-screen elements
- **Graceful degradation** — if `config` is null (loaded via `/loadclip`), position functions return immediately and elements use their default positions from the timeline

---

## 7. Dual-Mode Design (Module System + Hardcoded Fallback)

### Goal

Every module should work in **two modes**:
1. **Module system mode** — full archive persistence (position, visibility saved across sessions)
2. **`/loadclip` mode** — hardcoded compile-time positions (no persistence, but still functional)

### The Dual-Mode Pattern

```actionscript
class KzModule
{
    private var config:Object;          // null when loaded via /loadclip
    private var COMPILED_X:Number;      // Compile-time default position
    private var COMPILED_Y:Number;

    // === MODULE SYSTEM PATH ===

    public function OnModuleActivated(archive:Object):Object
    {
        config = archive;
        initialize();
        return config;
    }

    public function OnModuleDeactivated():Object
    {
        saveState();
        cleanup();
        return config;      // MUST return archive
    }

    // === /LOADCLIP PATH ===

    public function onLoad():Void
    {
        // config is null — no archive available
        initialize();
    }

    // === SHARED INIT ===

    private function initialize():Void
    {
        createUI();

        // Position: prefer saved → fall back to compiled default
        if (config)
        {
            var sx:Object = config.FindEntry("x");
            var sy:Object = config.FindEntry("y");
            if (sx !== undefined && sy !== undefined)
            {
                // Saved position from archive
                setPosition(Number(sx), Number(sy));
            }
            else
            {
                // First run via module system — use compiled defaults
                setPosition(COMPILED_X, COMPILED_Y);
            }
        }
        else
        {
            // /loadclip mode — always use compiled defaults
            setPosition(COMPILED_X, COMPILED_Y);
        }
    }

    private function saveState():Void
    {
        if (!config) return;    // No archive in /loadclip mode
        config.ReplaceEntry("x", panel._x);
        config.ReplaceEntry("y", panel._y);
        // Save any other persistent state...
    }

    private function setPosition(x:Number, y:Number):Void
    {
        var maxX:Number = Stage.width - PANEL_WIDTH;
        var maxY:Number = Stage.height - PANEL_HEIGHT;
        panel._x = Math.max(0, Math.min(x, maxX));
        panel._y = Math.max(0, Math.min(y, maxY));
    }
}
```

### Priority Chain

```
Position source priority (highest to lowest):
1. Config archive saved position  (config.FindEntry → defined value)
2. Compile-time defaults          (COMPILED_X, COMPILED_Y from Python generator)
3. Hardcoded fallback             (100, 100 or similar safe default)
```

### Save Points (per kazbars v1 pattern)

Every module should save position at these three points:
1. **`OnModuleDeactivated()`** — game is unloading the module
2. **`exitPreview()`** — user finished repositioning
3. **Drag `onRelease`** — each individual drag operation

This ensures position survives `/reloadui`, preview toggle, and unexpected shutdowns.
