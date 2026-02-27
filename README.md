# Kaz Flash Modz

A mod builder for **Age of Conan** that creates and manages custom UI modules. Configure everything in a desktop app, build your SWF files, and load them in-game.

## Modules

### KzGrids — Buff/Debuff Tracking
- Dynamic grids that auto-fill with matching buffs from your whitelist, sorted by time remaining
- Static grids with fixed slots for specific buffs (always in the same position)
- Track buffs on yourself or your current target
- Icons flash and turn red when buffs are about to expire
- Buff Discovery Console — see all buff IDs in real-time, pin the console to keep it open outside preview mode

### KzCastbars — Custom Cast Bars
- Per-bar color settings via ColorTransform
- Font customization for spell name and timer text
- Optional elapsed/total timer estimation ("1.2/2.5")
- 6 visual frame styles
- Automatically hides the game's default castbar

### KzTimers — Cooldown Tracker
- Create named timers with trigger conditions, durations, and bar appearance
- Trigger types: Buff Added, Buff Removed, Cast Success (with fuzzy spell name matching)
- In-game panel shows countdown bars with fill/drain animation
- Per-timer customization: bar color, warning color, fill direction, count direction (ascending/descending), retrigger mode
- 3 presets — group timers and switch between them in-game

### KzStopwatch — Standalone Timer
- Simple start/pause/stop clock with HH:MM:SS format
- Two layouts: Standard (panel + buttons) and Compact (thin strip)
- 23+ customizable settings — dimensions, fonts, colors, border, button shape, opacity

### DamageInfo — Damage Number Customization
- ~19 settings for animation timing, number positioning, and visual effects
- Configure floating and static numbers independently
- 3 animation presets (Default, Performance, Beauty)
- Per-damage-type color customization via TextColors.xml

## Requirements

- **Age of Conan** (with mod support)
- **Windows 10/11**

## Installation

1. Download the latest release `.zip` from [Releases](https://github.com/kazour/Kaz-Flash-Modz/releases)
2. Extract the zip to any folder
3. Run `Kaz Flash Modz.exe`
4. On first launch, set your Age of Conan installation path
5. Configure modules in their respective tabs
6. Click **Build & Install All** on the Welcome screen
7. In-game: `/reloadui` then `/reloadgrids`

## Development

To run from source instead of the bundled exe:

- **Python 3.8+** required
- `pip install -r requirements.txt`
- `python kzbuilder.py`
- MTASC compiler is included in `assets/compiler/`
- Flash CS6 for editing base.swf files (optional — only needed for advanced modifications)

## In-Game Controls

| Key / Command | Action |
|---|---|
| `Ctrl+Shift+Alt` | Toggle Preview Mode — drag grids, castbars, timers, stopwatch into position |
| `/reloadui` | Load new SWF files (run this first after building) |
| `/reloadgrids` | Reload all Kz modules |

## Module System Support

Kaz Flash Modz modules work in two modes:

- **Module system** (requires [Aoc.exe launcher bypass](docs/module-system.md)) — full position persistence across sessions, modules survive `/reloadui`
- **Script fallback** (`/loadclip`) — modules load via auto_login scripts with compile-time positions. No persistence, but fully functional.

Both modes are supported automatically. Users with `Aoc.exe` get persistence; users without it get the same features with positions reset each session.

## Folder Structure

```
Kaz Flash Modz/
├── kzbuilder.py              # Main Python GUI (entry point)
├── build.py                  # PyInstaller build script
├── Modules/                  # Python modules (UI, generators, settings)
├── assets/
│   ├── common_stubs/         # Shared AS2 stubs
│   ├── compiler/             # MTASC compiler + standard libraries
│   ├── kzgrids/              # KzGrids assets (base.swf, database, stubs)
│   ├── castbars/             # KzCastbars assets (base.swf, template, stubs)
│   ├── flash_timer/          # KzTimers assets (base.swf, templates)
│   ├── flash_stopwatch/      # KzStopwatch assets (base.swf, template)
│   └── damageinfo/           # DamageInfo assets (backup SWF, source)
├── profiles/                 # Saved configurations
├── settings/                 # App settings (auto-generated)
├── docs/                     # Technical documentation
└── temp/                     # Build artifacts (auto-generated)
```

## Profiles

- **Global profiles** (File > Save/Open) — save and restore ALL module settings at once
- **Per-tab Import/Export** — share individual module configurations
- Profile files are JSON — easy to share with other players via Discord or other channels

## Limits

- Maximum 64 total buff slots across all grids
- Grid dimensions: 1–64 rows, 1–64 columns (within the 64 slot limit)
- Icons scale from 24px to 64px
- Up to 10 simultaneous countdown bars in KzTimers
- Up to 3 timer presets

## Troubleshooting

**Mod doesn't load in-game:**
- Verify SWF files are in `Age of Conan/Data/Gui/Default/Flash/`
- Make sure you ran `/reloadui` before `/reloadgrids`

**Icons not showing:**
- Check that buff IDs are correct in the database
- Use the Buff Discovery Console (Preview Mode) to find correct IDs

**Preview mode not activating:**
- Make sure no other mod is capturing `Ctrl+Shift+Alt`

**Build fails:**
- Check that your AoC installation path is set correctly (Welcome screen)
- Verify the MTASC compiler exists in `assets/compiler/`

## Documentation

Developer documentation is in the `docs/` folder:

| Doc | Contents |
|---|---|
| [Architecture](docs/architecture.md) | Code structure, data models, generation flow |
| [AS2 Reference](docs/as2-reference.md) | ActionScript 2.0 syntax rules and MTASC gotchas |
| [Build System](docs/build-system.md) | Compilation process, file requirements, AoC directory map |
| [Module System](docs/module-system.md) | AoC module registration, config archive, Aoc.exe bypass |
| [Default Settings](docs/default-settings.md) | All default values and ranges |

Module-specific docs:
[KzGrids](docs/modules/kzgrids.md) ·
[KzCastbars](docs/modules/kzcastbars.md) ·
[KzTimers](docs/modules/kztimers.md) ·
[KzStopwatch](docs/modules/kzstopwatch.md) ·
[DamageInfo](docs/modules/damageinfo.md)

## Credits

**Author:** Kaz

**Tools:**
- [MTASC](https://www.mtasc.org/) — Motion-Twin ActionScript 2 Compiler
- [ttkbootstrap](https://ttkbootstrap.readthedocs.io/) — Python GUI theming (darkly theme)
- [pywinstyles](https://github.com/Akascape/py-window-styles) — Windows dark title bars

## License

MIT License — see [LICENSE](LICENSE) for details.
