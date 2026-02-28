---
name: as2-review
description: Audit AS2 code generators against documented constraints
disable-model-invocation: false
---

# AS2 Review — Audit Generated Code Against Constraints

Review all AS2 code generation modules for violations of ActionScript 2.0 / MTASC constraints documented in `docs/as2-reference.md`.

## What to check

Read each `*_generator.py` file and examine ALL string literals that contain AS2 code (multi-line strings used as templates or code fragments). Also read the AS2 template files in `assets/`.

### Constraint 1: No `for...in` on arrays

**Violation pattern**: `for (var k in someArray)` or `for (k in someArray)`
**Correct pattern**: `var i:Number = 0; while (i < arr.length) { ... i++; }`

Search all generated AS2 code for `for` loops that iterate arrays.

### Constraint 2: No `var` redefinition in same scope

**Violation pattern**: `var x:Number = 1;` followed by `var x:Number = 2;` in the same function
**Correct pattern**: Declare once, reassign without `var`

Check each generated function body for duplicate `var` declarations of the same variable name.

### Constraint 3: Explicit null comparison

**Violation pattern**: `if (!obj)` to check for null
**Correct pattern**: `if (obj == null)` or `if (obj == undefined)`

Note: `!obj` is fine for boolean checks. Only flag it when it's clearly being used as a null/existence check.

### Constraint 4: No string literal keys in object literals

**Violation pattern**: `{"key": value}`
**Correct pattern**: `{key: value}` or `obj["key"] = value` (bracket notation)

### Constraint 5: Closure variable capture

**Violation pattern**: Using `this` inside a closure/callback without capture
**Correct pattern**: `var self = this;` before the closure, then use `self` inside

### Constraint 6: 32KB bytecode limit per class

Estimate the size of each generated AS2 class. Reference sizes from `docs/as2-reference.md`:
- KzGrids main: ~22KB
- KzTimers shell: ~28KB (NEAR LIMIT)
- TimerManager: ~21KB
- KzStopwatch: ~24KB

Flag any class that appears to be approaching 28KB+ (danger zone).

### Constraint 7: Masks after content loads

**Violation pattern**: Applying masks during `MovieClip` creation
**Correct pattern**: Masks applied in `onLoadInit` callback (after content fully loads)

## Files to audit

**Generator files** (contain AS2 code as Python string literals):
- `Modules/as2_template.py` — KzGrids AS2 runtime template
- `Modules/grids_generator.py` — KzGrids code generation
- `Modules/castbar_generator.py` — KzCastbars code generation
- `Modules/timers_generator.py` — KzTimers + TimerManager code generation
- `Modules/stopwatch_generator.py` — KzStopwatch code generation
- `Modules/damageinfo_generator.py` — DamageInfo code generation

**Template files** (AS2 source with `%%PLACEHOLDER%%` markers):
- `assets/flash_timer/KzTimers.as.template`
- `assets/flash_timer/TimerManager.as.template`
- `assets/flash_stopwatch/KzStopwatch.as.template`

## Output format

```
## AS2 Constraint Review

### as2_template.py (KzGrids)
- ✓ No for...in on arrays
- ✓ No var redefinition
- ✓ Explicit null checks
- ✓ No string literal keys
- ✓ Closure captures correct
- ⚠ Estimated size: ~22KB (OK)

### timers_generator.py (KzTimers + TimerManager)
- ✗ Line 245: `for (var k in presets)` — use while loop
- ✓ No var redefinition
- ⚠ KzTimers shell estimated at ~28KB — NEAR LIMIT

(etc.)
```

Report all findings with file paths and line numbers. For violations, show the problematic code and the corrected version.
