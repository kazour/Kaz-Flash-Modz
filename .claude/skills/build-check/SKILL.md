---
name: build-check
description: Verify all KzBuilder modules import successfully
disable-model-invocation: false
---

# Build Check — Verify Module Imports

Run a quick import check across all KzBuilder modules to catch import errors, missing dependencies, and circular imports.

## Steps

### 1. Import check

Run this command from the project root:

```bash
python -c "
from Modules import (
    ui_helpers, build_utils, as2_template,
    grids_tab, grids_generator, database_editor,
    castbar_tab, castbar_generator, castbar_settings,
    damageinfo_tab, damageinfo_generator, damageinfo_settings, damageinfo_xml,
    timers_tab, timers_editor, timers_editor_dialog, timers_generator,
    timers_data, timers_appearance,
    stopwatch_tab, stopwatch_editor, stopwatch_phase_dialog,
    stopwatch_generator, stopwatch_data, stopwatch_settings,
    live_tracker_tab, live_tracker_settings,
    boss_timer, combat_monitor, timer_overlay,
)
print('All 30 modules imported successfully')
"
```

### 2. Syntax check

Run `py_compile` on every Python file:

```bash
python -c "
import py_compile, glob, sys
errors = []
for f in glob.glob('Modules/*.py') + ['kzbuilder.py', 'build.py']:
    try:
        py_compile.compile(f, doraise=True)
    except py_compile.PyCompileError as e:
        errors.append(str(e))
if errors:
    print('SYNTAX ERRORS:')
    for e in errors:
        print(f'  {e}')
    sys.exit(1)
else:
    print('All files pass syntax check')
"
```

### 3. Report

- If both pass: report "All modules import and compile successfully"
- If import fails: show the exact error, which module failed, and the traceback
- If syntax check fails: show the file and line with the syntax error
