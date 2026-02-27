# AS2 Reference — MTASC Syntax Rules & Gotchas

## 32KB Bytecode Limit

MTASC enforces **32KB max per class**.

**Current sizes:**
- KzGrids main: ~22KB
- KzTimers shell: ~28KB
- TimerManager: ~21KB
- KzStopwatch: ~24KB

**Rules:**
- Do NOT add large methods to classes near the limit
- New features MUST go into helper classes
- String literals count toward limit
- Split if approaching 28KB

**Existing helpers:**
- `KzGridsPreview.as` (~5KB), `KzGridsConsole.as` (~4KB), `KzGridsSlot.as`

---

## Syntax Rules

```actionscript
// ❌ No for...in on arrays
for (var k in myArray) { }
// ✅ Use while with index
var i:Number = 0;
while (i < myArray.length) { var item = myArray[i]; i++; }

// ❌ No var redefinition in same scope
var x:Number = 1;
var x:Number = 2;
// ✅ Reuse variable
var x:Number = 1;
x = 2;

// ❌ Masks during creation (icon not loaded yet)
loadClip(url, mc); mc.setMask(mask);
// ✅ Masks AFTER content loads
function onLoadInit(mc) { mc.setMask(mask); }

// ⚠️ Object in boolean — works without -strict, but prefer explicit form
if (!myObj) return;           // OK in practice (MTASC default mode)
if (myObj == null) return;    // Preferred — explicit null comparison

// ❌ String literal keys in object literal
var map:Object = {"Slow Death Strike":{id:1}};
// ✅ Bracket notation assignment
var map:Object = {};
map["Slow Death Strike"] = {id:1};

// Closures need explicit scope capture
var self:KzGrids = this;
mc.onRelease = function() { self.doSomething(); };
```

---

## Common Patterns

### Static `main()` Entry Point
Present in KzTimers and KzStopwatch but unused — frame scripts call `onLoad()` directly, not `main()`. Kept for potential future MTASC `-main` flag usage:
```actionscript
public static function main(root:MovieClip):Void {
    var module:KzTimers = new KzTimers(root);
    root.m_Module = module;
    module.onLoad();
}
```

### Reusable Arrays (GC Reduction)
Clear arrays instead of creating new ones:
```actionscript
_tempBuffs.length = 0;  // Reuse existing array
// NOT: _tempBuffs = new Array();  // Creates GC pressure
```

### AS2 Boolean Generation (Python)
```python
def to_as2_bool(val):
    return "true" if val else "false"
```

---

## Performance Priorities

1. Grid visibility culling — skip hidden/empty grids
2. Math caching — pre-calculated alpha flash lookup (100 values)
3. GC reduction — reuse arrays (`_tempBuffs.length = 0`), pooled state objects in TimerManager
4. Smart expiry — early exit when buff queues empty
5. Timer optimizations — single `getTimer()` per update cycle, `_xscale` bar fills, cached `resizePanel()`, diffed TextField updates, pre-compiled color Numbers

---

## Flash CS6 Symbols

| Symbol | Linkage | Contents |
|--------|---------|----------|
| BuffSlot | `BuffSlot` | 64×64, gray border, `m_icon` at (0,0) |
| DebuffSlot | `DebuffSlot` | 64×64, dark red border, `m_icon` |
| MiscSlot | `MiscSlot` | 64×64, golden border, `m_icon` |

---

## Module-Specific Gotchas

### KzTimers
- MTASC strict boolean: `!myObj` fails, use `myObj == null`
- String keys in object literals fail — cast triggers use bracket notation assignment (`castTriggerMap[name] = {slot:i, src:src}`)
- Closures: `var self:KzTimers = this;` required
- Path resolution: all paths `.resolve()` to absolute (MTASC runs from temp dir)
- Two-class architecture: KzTimers (shell/UI) + TimerManager (cooldown engine), compiled together into one SWF
- Timer colors compiled as Number literals (`0xRRGGBB`) — no runtime `parseInt` parsing
- State objects pooled in TimerManager constructor — `getTimerState()` reuses them (zero allocation per call)
- Bar fills drawn once at full width, scaled via `_xscale` — only redrawn on color change

### KzStopwatch
- Own base.swf with frame 1 entry point (no `-main` flag)
- Same preview mode pattern as all other modules

### DamageInfo
- `defenderIsClient` ALWAYS true for resource events (mana/stamina loss) — use `characterID` comparison instead
- `Character.GetClientCharacter()` returns different ID format than damage events — capture ID from actual events
- DO NOT replace TweenLite animations — causes "freezing faded numbers" bug
- TweenLite is a third-party library — its code patterns may differ from project conventions (e.g., uses `for...in` on objects)

### KzGrids Config Archive Keywords
- `lt` is a deprecated AS2 less-than operator keyword — MTASC fails to parse it as a variable name
- Config archive keys renamed: `lt` → `clp`/`clt` (console log player / console log target)
- Always test config archive key names against AS2 reserved words before use

### Console Panel
- Text boxes sometimes render as boxes — exit/re-enter Preview Mode
- `embedFonts` must be `false`, `setTextFormat()` AFTER setting text

### Icon Centering
- Icons load at various sizes, `onLoadInit()` scales to 64×64 at (0,0)

### Slot Symbol Swapping
- When buff type changes: store props → `removeMovieClip()` → `attachMovie()` new type → restore props → update array ref
