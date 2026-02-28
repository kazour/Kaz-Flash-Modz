---
name: doc-sync
description: Check and update all documentation to match current code
disable-model-invocation: false
---

# Doc Sync — Keep Documentation in Sync with Code

Scan all settings files, generators, and templates, then compare against documentation. Report mismatches and fix them.

## When to run

Run this skill after making code changes that affect:
- Default values or validation ranges in `*_settings.py` files
- Compile-time placeholders in `*_generator.py` files or AS2 templates
- Adding/removing/renaming files in `Modules/`
- Version numbers

## Checks to perform

### Check 1: Default Settings (`docs/default-settings.md`)

Read these code files and extract all default values and ranges:

| Code File | Dict to Extract |
|-----------|----------------|
| `Modules/castbar_settings.py` | `CASTBAR_DEFAULTS`, `CASTBAR_RANGES` |
| `Modules/timers_appearance.py` | `TIMERS_APPEARANCE_DEFAULTS`, `TIMERS_APPEARANCE_RANGES` |
| `Modules/timers_data.py` | Default values in `CooldownTimer` dataclass and `TIMER_RANGES` |
| `Modules/stopwatch_settings.py` | `STOPWATCH_DEFAULTS`, `STOPWATCH_RANGES` |
| `Modules/stopwatch_data.py` | `StopwatchPhase`/`StopwatchPreset` defaults, built-in preset data |
| `Modules/damageinfo_settings.py` | `GAME_DEFAULTS`, `GLOBAL_SETTINGS` (each entry has `default`, `min`, `max`) |

Then read `docs/default-settings.md` and for each documented setting, verify:
- The default value in the doc matches the code
- The min/max range in the doc matches the code
- No settings exist in code that are missing from the doc
- No settings exist in the doc that were removed from code

### Check 2: Module Documentation (`docs/modules/*.md`)

For each module doc, verify:

**`docs/modules/kzcastbars.md`:**
- Configuration model fields match `CASTBAR_DEFAULTS` keys in `castbar_settings.py`
- File structure section matches actual files

**`docs/modules/kztimers.md`:**
- Appearance settings match `TIMERS_APPEARANCE_DEFAULTS` in `timers_appearance.py`
- CooldownTimer data model matches `timers_data.py` dataclass fields
- Compile-time placeholder table matches `%%PLACEHOLDER%%` patterns in `timers_generator.py`

**`docs/modules/kzstopwatch.md`:**
- Configuration model matches `STOPWATCH_DEFAULTS` in `stopwatch_settings.py`
- Compile-time placeholder table matches `%%PLACEHOLDER%%` patterns in `stopwatch_generator.py`
- Preset system description matches `stopwatch_data.py` structure

**`docs/modules/damageinfo.md`:**
- All 19 settings with defaults and ranges match `GLOBAL_SETTINGS` in `damageinfo_settings.py`
- Game base values match `GAME_DEFAULTS` dict

**`docs/modules/kzgrids.md`:**
- Grid defaults match hardcoded values in `grids_tab.py` (Add Grid Wizard)

### Check 3: CLAUDE.md File Structure

Read the file tree in CLAUDE.md (the `File Structure` section) and compare against actual files:
- Run `ls Modules/*.py` to get the real file list
- Flag any files in CLAUDE.md that don't exist on disk
- Flag any files on disk that aren't listed in CLAUDE.md

### Check 4: Version Consistency

Read the version from these locations and verify they all match:
- `build.py` line 19: `VERSION = "X.Y.Z"`
- `kzbuilder.py` line 56: `APP_VERSION = "X.Y.Z"`
- `CLAUDE.md`: `**Version:** X.Y.Z`
- `CHANGELOG.md`: First `## vX.Y.Z` heading

### Check 5: Compile-Time Placeholders

For each generator, extract all `%%PLACEHOLDER%%` patterns used in string replacements:
- `Modules/timers_generator.py` → compare against `docs/modules/kztimers.md` placeholder table
- `Modules/stopwatch_generator.py` → compare against `docs/modules/kzstopwatch.md` placeholder table
- `Modules/castbar_generator.py` → compare against `docs/modules/kzcastbars.md`
- `Modules/damageinfo_generator.py` → compare against `docs/modules/damageinfo.md`
- `Modules/grids_generator.py` → compare against `docs/modules/kzgrids.md`

## Output Format

Present findings as a checklist:

```
## Doc Sync Report

### Default Settings (docs/default-settings.md)
- ✓ Castbar defaults: 21/21 settings match
- ✗ Timers appearance: `corner_radius` range is 0-12 in code but 0-10 in doc
- ✗ Stopwatch: new setting `phase_font_bold` in code, missing from doc

### Module Docs
- ✓ kzcastbars.md: All fields match
- ✗ kztimers.md: Placeholder %%NEW_THING%% in generator but not documented
- ✓ kzstopwatch.md: All placeholders match

### CLAUDE.md File Structure
- ✓ All 31 module files accounted for
- (or) ✗ Missing from CLAUDE.md: Modules/new_file.py

### Version Consistency
- ✓ All 4 locations show v3.3.6
- (or) ✗ build.py says 3.3.7 but CLAUDE.md says 3.3.6

### Compile-Time Placeholders
- ✓ All generators match their docs
```

## Fixing Mismatches

After reporting, fix all mismatches by updating the documentation files to match the code (code is the source of truth). Show each fix as you make it.

If a mismatch is ambiguous (e.g., code and doc disagree but it's unclear which is correct), flag it for the user instead of auto-fixing.
