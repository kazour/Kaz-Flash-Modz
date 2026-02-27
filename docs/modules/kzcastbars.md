# KzCastbars Module Reference

## Architecture

```
KzCastbars.as (main class)
    ├── KzCastbarsPreview.as (loosely coupled helper)
    ├── m_PlayerCastBar (frame, color, mask, text fields)
    └── m_TargetCastBar (same structure)
```

---

## Configuration Model

```javascript
{
    bar_style: 1,               // 1-5 visible, 6 = hidden; linkage "castbar{N}"
    enable_player: true,
    enable_target: true,
    player_x: 300, player_y: 400,
    target_x: 300, target_y: 350,
    hide_default: true,         // Writes modified CommandTimerBar.xml

    player_color: "9C6025",     // Bronze (matches game default)
    target_color: "9C6025",
    spell_font: "Arial",
    spell_font_size: 12,
    spell_bold: false,
    spell_color: "9F9F9F",      // Gray (matches game default)
    spell_align: "center",
    timer_font: "Arial",
    timer_font_size: 10,
    timer_bold: true,
    timer_color: "9F9F9F",
    show_timer: false,
    show_estimate: false,       // "1.2/2.5" elapsed/total format
    spell_x: -3, spell_y: -2,
    timer_x: -15, timer_y: -2,
}
```

Spell name and timer text have independent font size controls (`spell_font_size` and `timer_font_size`).

---

## Preview Mode Design

Overlay created on `rootClip` (sibling of bar), not as child. This means:
- Overlay stays visible when bar hides (cast ends)
- Bar behaves normally during preview
- Overlay removed only via hotkey toggle

**Loose coupling:** Preview helper only knows generic bar objects:
```actionscript
{ mc: MovieClip, label: String, overlayColor: Number, width: Number, height: Number }
```

---

## CommandTimerBar.xml Hiding

**Hide:** Copy Default XML to Customized, modify `ProgressBar` and `TextView` with `max_size_limit="Point(0, 0)"`

**Restore:** Delete Customized XML (game falls back to Default)

---

## Build

```bash
# Copy base.swf to output path, then:
mtasc.exe -cp castbars/stubs -cp common_stubs -swf KzCastbars.swf -version 8 KzCastbars.as
```

Per-tab Build button compiles directly to game directory. Build All compiles to staging first.

---

## Files

```
assets/castbars/
├── base.swf, base.fla
├── art/                     # Preview PNGs (frame1-6, color1-6)
├── KzCastbars.as.template   # %%PLACEHOLDER%% markers
└── stubs/KzCastbarsPreview.as

Modules/
├── castbar_tab.py           # UI (per-tab Build button, preview, settings)
├── castbar_generator.py     # Template → AS2 → MTASC compile
└── castbar_settings.py      # CASTBAR_DEFAULTS, validation, STYLE_COLOR_MULT/OFFS, BAR_STYLE_LINKAGE
```
