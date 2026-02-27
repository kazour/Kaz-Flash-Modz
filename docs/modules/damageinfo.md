# DamageInfo Module Reference

## Overview

`DamageInfo.swf` is a **default game file** (decompiled and optimized). Kaz Flash Modz exposes 19 settings as offsets from game defaults, organized into 6 categories, plus a preset system for animation/visual presets.

Unlike the other modules (KzGrids, KzCastbars, KzTimers, KzStopwatch), DamageInfo is NOT a class-based MTASC module — it's the game's own SWF with source modifications. It does not integrate with the AoC module system (no config archive, no OnModuleActivated/OnModuleDeactivated).

---

## Architecture

```
Game Engine (C++)
    ├── SignalDamageInfo.Emit()        → Creates damage number
    ├── SignalDestroyDamageInfo.Emit() → Clears all
    └── DistributedValue changes       → Updates settings
            │
      DamageNumberManager
            ├── MovingManager (floating numbers)
            │       ├── NumbersColumn (per target/direction)
            │       └── MovingDamageText (pooled)
            └── FixedManager (static numbers)
                    └── FixedDamageText (pooled)
```

---

## Offset-Based Settings Architecture

All settings are defined as **offsets from game defaults** (0 = original game behavior). This design means users adjust relative to the game's baseline, not absolute values.

```python
# Example: show_duration
game_default = 0.2   # seconds (original game value)
user_offset  = 0.1   # user's adjustment
final_value  = 0.3   # what gets compiled into AS2
```

The generator computes `final_value = game_default + offset` for each setting and patches the AS2 source via regex before MTASC compilation.

---

## Customizable Settings (19 total)

### Animation Timing (3 settings)
| Setting | Default Offset | Game Default | Range | Description |
|---------|---------------|--------------|-------|-------------|
| `show_duration` | 0 | 0.2s | -0.15 to +0.8 | Pop-in speed |
| `fade_duration` | 0 | 0.2s | -0.15 to +0.8 | Fade-out speed |
| `easing_type` | 0 | Quad | 0-2 | Animation curve (Quad/Cubic/Quart) |

### Dir 1: Above Target (2 settings)
| Setting | Default Offset | Game Default | Range | Description |
|---------|---------------|--------------|-------|-------------|
| `dir1_x_offset` | 0 | 50px | -50 to +150 | X shift from target head |
| `dir1_y_offset` | 0 | 0px | -200 to +200 | Y shift from target head |

### Dir -1: Fixed Columns (5 settings)
| Setting | Default Offset | Game Default | Range | Description |
|---------|---------------|--------------|-------|-------------|
| `fixed_col_x` | 0 | 50px | -200 to +200 | Column A: X from center |
| `fixed_col_y` | 0 | 100px | -100 to +300 | Column A: Y from top |
| `fixed_col_split` | 0 | off | 0-1 | Enable Column B (prefix numbers) |
| `col_b_x` | 0 | 50px | -200 to +200 | Column B: X from center |
| `col_b_y` | 0 | 100px | -100 to +300 | Column B: Y from top |

### Dir 0: Static Zig-Zag (3 settings)
| Setting | Default Offset | Game Default | Range | Description |
|---------|---------------|--------------|-------|-------------|
| `fixed_y_base` | 0 | 100px | -200 to +200 | Zig-zag Y center |
| `fixed_x_offset` | 0 | 200px | -150 to +200 | Zig-zag X spread |
| `fixed_y_spacing` | 0 | 60px | -30 to +60 | Stack spacing |

### Display Options (2 settings)
| Setting | Default Offset | Game Default | Range | Description |
|---------|---------------|--------------|-------|-------------|
| `show_titles` | 0 | off | 0-1 | Show labels (CRITICAL, MANA, etc.) |
| `other_resource_loss_to_target` | 0 | off | 0-1 | Enemy drain at target position |

### Visual Effects (4 settings)
| Setting | Default Offset | Game Default | Range | Description |
|---------|---------------|--------------|-------|-------------|
| `title_scale` | 0 | 0.7x | -0.4 to +0.8 | Label size multiplier |
| `text_scale` | 0 | 0.5x | -0.2 to +1.0 | Number size multiplier |
| `shadow_distance` | 0 | 4px | -4 to +6 | Drop shadow offset |
| `shadow_blur` | 0 | 3px | -3 to +7 | Shadow softness |

---

## Preset System

Three presets control the hidden categories (Animation Timing + Visual Effects):

| Preset | Effect |
|--------|--------|
| **Default** | All offsets at 0 (original game behavior) |
| **Performance** | Faster animations (-0.1s), smaller shadows (-2px) |
| **Beauty** | Slightly slower (+0.02s), Cubic easing, larger shadows (+1px) |

The preset dropdown in the UI controls `HIDDEN_CATEGORIES` settings. Users can still adjust Dir/Display settings independently.

---

## TextColors.xml

`damageinfo_xml.py` handles custom damage type colors:
- Parses the game's `Default/TextColors.xml` as baseline
- Applies user's color overrides per damage type
- Writes modified XML to `Customized/TextColors.xml`
- Game loads Customized version with priority over Default

---

## Source Files

```
assets/damageinfo/src/__Packages/
├── DamageNumberManager.as
├── MainDamageNumbers.as        # Entry point
├── helpers/
│   ├── ObjectPool.as, DamageNumberType.as, DamageTextFactory.as
├── numbersManagers/
│   ├── AbstractManager.as, MovingManager.as, FixedManager.as, NumbersColumn.as
├── numbersTypes/
│   ├── DamageTextAbstract.as, MovingDamageText.as, FixedDamageText.as
└── com/
    ├── GameInterface/          # Game engine intrinsics
    └── greensock/              # TweenLite library
```

Some classes are **intrinsic** (type info only): `DistributedValueBase`, `ID32`

---

## Optimization History

- O(1) column lookup via hashmap (was O(n))
- O(1) array deletion via swap-and-pop (was O(n) splice)
- Object pooling for MovieClips and text
- Column cleanup after 2s delay (fixes memory leak)
- Numeric hashmap keys (avoids string GC)

**DO NOT replace TweenLite animations** — causes "freezing faded numbers" bug.

---

## Build

DamageInfo uses a unique build process:
1. Copy source files to temp directory
2. Apply setting offsets via regex pattern matching on AS2 source
3. Compile modified sources with MTASC
4. Copy result to output path
5. Clean up temp directory

```bash
mtasc.exe -cp {compiler_dir}/std -cp {compiler_dir}/std8 -cp {temp_dir}/__Packages \
  -swf DamageInfo.swf -version 8 {temp_dir}/__Packages/MainDamageNumbers.as
```

MTASC replaces AS2 classes, preserves library symbols. ~0.05s compile.

---

## Python Files

```
Modules/
├── damageinfo_tab.py           # UI (per-tab Build button, preset dropdown, settings)
├── damageinfo_generator.py     # Offset application via regex + MTASC compile
├── damageinfo_settings.py      # 19 settings as offsets, 3 presets, validation
└── damageinfo_xml.py           # TextColors.xml parsing/generation

assets/damageinfo/
├── DamageInfo_backup.swf       # Original game SWF
└── TextColors_default.xml      # Default XML template
```
