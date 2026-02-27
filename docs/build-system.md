# Build System — Compilation & Game Integration

## Build Modes

### Build All (Welcome Screen)

**"Build & Install All"** uses a two-phase approach for safety:

1. **Phase 1 — Compile:** All enabled modules compile to a temporary staging directory (`tempfile.mkdtemp(prefix="kzbuilder_")`)
2. If ANY module fails → error shown, game directory untouched, staging cleaned up
3. **Phase 2 — Install:** Copy SWFs from staging to game dir, run side effects (XML, scripts)
4. Disabled modules get artifacts cleaned up automatically
5. Scripts (`auto_login`, `reloadgrids`) regenerated for enabled modules only

### Per-Tab Build (Individual Modules)

Each module tab has its own **Build** button that compiles that single module's SWF directly to the game directory (no staging). Used for rapid iteration on one module.

---

## Compile Commands

All modules use `build_utils.compile_as2()` which runs MTASC with `-swf` (in-place modification) and `-version 8`. The general pattern is: copy base.swf → compile AS2 into the copy → output result.

### KzGrids
```bash
# Copy base.swf to output path, then:
mtasc.exe -cp stubs -cp common_stubs -swf KzGrids.swf -version 8 KzGrids.as
```

### KzCastbars
```bash
# Copy base.swf to output path, then:
mtasc.exe -cp castbars/stubs -cp common_stubs -swf KzCastbars.swf -version 8 KzCastbars.as
```

### KzTimers (multi-file)
```bash
# Copy base.swf to output path, then:
mtasc.exe -cp common_stubs -swf KzTimers.swf -version 8 KzTimers.as TimerManager.as
```

### KzStopwatch
```bash
# Copy base.swf to output path, then:
mtasc.exe -cp common_stubs -swf KzStopwatch.swf -version 8 KzStopwatch.as
```

### DamageInfo
```bash
# Copy DamageInfo_backup.swf to output path, modify sources in temp dir, then:
mtasc.exe -cp {compiler_dir}/std -cp {compiler_dir}/std8 -cp {temp_dir}/__Packages \
  -swf DamageInfo.swf -version 8 {temp_dir}/__Packages/MainDamageNumbers.as
```

DamageInfo is unique: it copies source files to a temp directory, applies setting offsets via regex, then compiles from the modified sources.

MTASC **replaces** AS2 classes in SWF (removes old, injects new). Library symbols (fonts, containers) preserved.

---

## Build Pipeline Flow

```
build()
  → _validate_build_prerequisites()    # game path + compiler check
  → _get_build_configuration()         # which modules, paths, step count
  → _execute_builds()                  # two-phase compile+install
      Phase 1: Compile all enabled modules to staging
        - KzGrids: build_grids() via grids_generator.py
        - DamageInfo: _compile_damageinfo() → build_damageinfo()
        - KzCastbars: _compile_castbars() → build_castbars()
        - KzTimers: _compile_timers() → build_flash_timer()
        - KzStopwatch: _compile_stopwatch() → build_stopwatch()
      Check: any failures → abort, game directory untouched
      Phase 2: Install to game directory
        - Copy SWFs from staging to Flash/
        - _cleanup_disabled_modules() → remove SWFs for unchecked modules
        - _install_damageinfo() → generate TextColors.xml
        - _install_castbars() → write/remove CommandTimerBar.xml, update auto_login
        - _create_scripts() → regenerate auto_login + reloadgrids
  → _display_build_summary()           # per-module status
```

---

## Side Effects

| Module | Side Effect | Target Path |
|--------|-------------|-------------|
| DamageInfo | Generate `TextColors.xml` (custom damage colors) | `Data/Gui/Customized/TextColors.xml` |
| KzCastbars | Write/remove `CommandTimerBar.xml` (hide default castbar) | `Data/Gui/Customized/Views/CommandTimerBar.xml` |
| KzCastbars | Update GUI-level `auto_login` script | `Data/Gui/Default/Scripts/auto_login` |
| All enabled | Update root `auto_login` script (`/loadclip` commands) | `Scripts/auto_login` |
| All enabled | Update `reloadgrids` script | `Scripts/reloadgrids` |

---

## Module Cleanup (Disabled Modules)

When a module is unchecked, `_cleanup_disabled_modules()` removes its artifacts:

| Module | Cleanup Action |
|--------|---------------|
| KzGrids | Delete `KzGrids.swf` |
| KzCastbars | Delete `KzCastbars.swf`, restore/remove `CommandTimerBar.xml`, strip GUI auto_login entries |
| KzTimers | Delete `KzTimers.swf` |
| KzStopwatch | Delete `KzStopwatch.swf` |
| DamageInfo | Restore original `DamageInfo.swf` from backup, restore/remove `TextColors.xml` |

---

## Required Files for Compilation

```
assets/common_stubs/                    ← Shared across all MTASC-compiled modules
├── com/GameInterface/Game/
│   ├── Character.as
│   └── CharacterBase.as
└── mx/utils/
    └── Delegate.as                     ← Full 26-line implementation

assets/kzgrids/                         ← KzGrids
├── base.swf, base.fla
└── stubs/
    ├── com/Utils/
    │   ├── ID32.as
    │   └── ImageLoader.as
    ├── KzGridsPreview.as
    ├── KzGridsConsole.as
    └── KzGridsSlot.as

assets/castbars/                        ← KzCastbars
├── base.swf, base.fla
├── art/                                # Preview PNGs (frame1-6, color1-6)
├── KzCastbars.as.template
└── stubs/
    └── KzCastbarsPreview.as

assets/flash_timer/                     ← KzTimers
├── base.swf, base.fla
├── KzTimers.as.template
└── TimerManager.as.template

assets/flash_stopwatch/                 ← KzStopwatch
├── base.swf, base.fla
└── KzStopwatch.as.template

assets/damageinfo/                      ← DamageInfo
├── DamageInfo_backup.swf               # Original game SWF
├── TextColors_default.xml
└── src/__Packages/
    ├── MainDamageNumbers.as            # Entry point
    ├── DamageNumberManager.as
    ├── helpers/ ...
    ├── numbersManagers/ ...
    ├── numbersTypes/ ...
    └── com/ ...                        # GameInterface intrinsics + TweenLite
```

---

## Temp Directories

| Context | Location | Cleanup |
|---------|----------|---------|
| Build All staging | `tempfile.mkdtemp(prefix="kzbuilder_")` | Always cleaned in `finally` block |
| KzGrids | `tempfile.mkdtemp(prefix="kzgrids_")` | Always cleaned in `finally` block |
| KzCastbars | `tempfile.mkdtemp(prefix="kzcastbars_")` | Always cleaned in `finally` block |
| KzTimers | `tempfile.mkdtemp(prefix="kztimers_")` | Always cleaned in `finally` block |
| KzStopwatch | `tempfile.mkdtemp(prefix="kzstopwatch_")` | Always cleaned in `finally` block |
| DamageInfo | `tempfile.mkdtemp(prefix="damageinfo_")` | Always cleaned in `finally` block |

---

## In-Game Reload Sequence

1. `/reloadui` — Loads new SWF files
2. `/reloadgrids` — Reloads KzGrids with changes

**`/reloadui` MUST come first, or changes won't apply!**

---

## AoC Directory Map

```
Age of Conan/                          ← game_path root
├── CombatLog-*.txt                    ← Combat logs (root, NOT Data/Logs)
├── Scripts/                           ← User slash commands
│   ├── auto_login                     ← Game settings + /loadclip commands
│   └── reloadgrids                    ← /reloadgrids command
├── Data/
│   └── Gui/
│       ├── Default/                   ← Game defaults + our SWFs
│       │   ├── Flash/                 ← SWF output directory
│       │   │   ├── KzGrids.swf
│       │   │   ├── KzCastbars.swf
│       │   │   ├── KzTimers.swf
│       │   │   ├── KzStopwatch.swf
│       │   │   └── DamageInfo.swf
│       │   ├── Scripts/
│       │   │   └── auto_login         ← GUI-level auto-load
│       │   ├── Views/
│       │   │   └── CommandTimerBar.xml ← Default castbar XML
│       │   ├── TextColors.xml
│       │   └── Fonts/
│       ├── Customized/                ← User overrides (priority)
│       │   ├── Views/
│       │   │   └── CommandTimerBar.xml ← Modified to hide default castbar
│       │   ├── TextColors.xml         ← Custom damage colors
│       │   └── Fonts/
│       └── Aoc/                       ← Third-party addons
```

**Two auto_login files:**
- `Scripts/auto_login` — Game settings, KzGrids + KzCastbars + KzTimers + KzStopwatch `/loadclip`
- `Data/Gui/Default/Scripts/auto_login` — GUI-level KzCastbars `/loadclip` only

**Key rules:**
- Combat logs at **game root**
- SWFs to `Data/Gui/Default/Flash/`
- XML overrides to `Data/Gui/Customized/`
- User scripts to `Scripts/`
