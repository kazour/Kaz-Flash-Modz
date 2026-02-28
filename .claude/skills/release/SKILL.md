---
name: release
description: Build, tag, and publish a new release to GitHub with auto-changelog
disable-model-invocation: true
---

# Release — Build, Tag, and Publish to GitHub

This skill automates the full release pipeline for Kaz Flash Modz.

## Prerequisites

- `python` available on PATH
- `gh` CLI authenticated with GitHub
- PyInstaller installed (`pip install pyinstaller`)
- Clean working tree (no uncommitted changes)

## Steps

### 1. Pre-flight checks

- Run `git status` — abort if there are uncommitted changes (warn user to commit or stash first)
- Run `git fetch origin` to ensure we're up to date
- Read the current version from `build.py` line 19 (`VERSION = "X.Y.Z"`)
- Report current version to user

### 2. Get release info from user

Ask the user for:
- **New version number** (e.g., "3.3.7") — validate it's higher than current
- **Short release title** (e.g., "Timer hotfix") — used in tag, commit, and release title

### 3. Generate changelog entry

- Run `git log --oneline` since the last tag to see what changed
- Ask the user to describe/confirm what changed, or summarize from commit history
- Write a CHANGELOG.md entry following the established format:

```markdown
## vX.Y.Z — <Title>

### Added
- (new features, if any)

### Changed
- (modifications to existing features)

### Fixed
- (bug fixes, if any)
```

- Insert the new section at the top of CHANGELOG.md (after line 5, before the first `## v` entry)
- Separate from the next entry with `---`

### 4. Update version in all files

Update the version string in these locations:

**Master version:**
- `build.py` line 19: `VERSION = "X.Y.Z"`

**App version:**
- `kzbuilder.py` line 56: `APP_VERSION = "X.Y.Z"`
- `kzbuilder.py` line 2: docstring `Kaz Flash Modz vX.Y.Z`

**CLAUDE.md:**
- Line containing `**Version:**` — update to new version

**All module docstrings** (line 2 of each file — the `"""..."""` docstring):
Update `KzBuilder X.Y.Z` to new version in these files:
- `Modules/build_utils.py`
- `Modules/database_editor.py`
- `Modules/grids_tab.py`
- `Modules/ui_helpers.py`
- `Modules/timers_data.py`
- `Modules/as2_template.py`
- `Modules/boss_timer.py`
- `Modules/castbar_generator.py`
- `Modules/castbar_settings.py`
- `Modules/castbar_tab.py`
- `Modules/combat_monitor.py`
- `Modules/damageinfo_generator.py`
- `Modules/damageinfo_settings.py`
- `Modules/damageinfo_tab.py`
- `Modules/damageinfo_xml.py`
- `Modules/live_tracker_settings.py`
- `Modules/live_tracker_tab.py`
- `Modules/stopwatch_data.py`
- `Modules/stopwatch_editor.py`
- `Modules/stopwatch_generator.py`
- `Modules/stopwatch_phase_dialog.py`
- `Modules/stopwatch_settings.py`
- `Modules/stopwatch_tab.py`
- `Modules/timers_appearance.py`
- `Modules/timers_editor.py`
- `Modules/timers_editor_dialog.py`
- `Modules/timers_generator.py`
- `Modules/timers_tab.py`
- `Modules/timer_overlay.py`
- `Modules/grids_generator.py`

Use a search-and-replace for the old version string → new version string in each file's docstring. Do NOT change version strings that appear in code logic (like default parameters) — only docstrings.

### 5. Build the distribution

Run: `python build.py`

This will:
1. Clean previous build artifacts
2. Build `Kaz Flash Modz.exe` via PyInstaller
3. Bundle exe + assets into `Kaz Flash Modz/` folder
4. Create `Kaz Flash Modz.zip`
5. Clean up intermediate files

Verify: Check that `Kaz Flash Modz.zip` exists and report its file size.

### 6. Commit, tag, and push

```bash
# Stage all version-bumped files
git add build.py kzbuilder.py CLAUDE.md CHANGELOG.md Modules/*.py

# Commit
git commit -m "bump: vX.Y.Z — <title>"

# Tag
git tag vX.Y.Z

# Push commit and tag
git push origin main
git push origin vX.Y.Z
```

### 7. Create GitHub release

Extract the changelog section for this version (everything between `## vX.Y.Z` and the next `---`).

```bash
gh release create vX.Y.Z \
  --title "vX.Y.Z — <title>" \
  --notes "<extracted changelog section>" \
  "Kaz Flash Modz.zip"
```

### 8. Report

Show the user:
- Release URL (from `gh release view`)
- Version bumped in N files
- Zip size
- Changelog entry that was generated
