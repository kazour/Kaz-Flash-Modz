# Kaz Flash Modz Default Settings Reference

## Build / Module Enable (Welcome Screen)

| Setting | Default |
|---------|---------|
| KzGrids enabled | `true` |
| KzCastbars enabled | `true` |
| KzTimers enabled | `true` |
| KzStopwatch enabled | `true` |
| DamageInfo enabled | `true` |

---

## KzGrids — Grid Defaults

Per-grid, created via Add Grid Wizard.

| Setting | Default | Range |
|---------|---------|-------|
| enabled | `true` | — |
| type | `"player"` | player / target |
| rows | `1` | 1–64 |
| cols | `10` | 1–64 |
| iconSize | `56` | 24–64 px |
| gap | `-1` | -5 to 10 px |
| x | `100` (player) / `300` (target) | 0–2560 |
| y | `400` | 0–1440 |
| slotMode | `"dynamic"` | dynamic / static |
| showTimers | `true` | — |
| timerFontSize | `18` | 8–24 |
| timerFlashThreshold | `6` | 0–11 sec |
| timerYOffset | `0` | -10 to +10 px |
| enableFlashing | `true` | — |
| fillDirection | `"LR"` (1 row) / `"BT"` (1 col) / `"BL-TR"` (else) | LR/RL/TB/BT/TL-BR/etc |
| sortOrder | `"longest"` | shortest / longest / application |
| layout | `"buffFirst"` (player) / `"debuffFirst"` (target) | buffFirst / debuffFirst / mixed |
| whitelist | `[]` | — |
| slotAssignments | `{}` | — |

---

## KzCastbars — Castbar Defaults

| Setting | Default | Range |
|---------|---------|-------|
| bar_style | `1` | 1–6 |
| enable_player | `true` | — |
| enable_target | `true` | — |
| player_color | `9C6025` (bronze) | hex |
| target_color | `9C6025` (bronze) | hex |
| player_x | `300` | 0–2560 |
| player_y | `400` | 0–1440 |
| target_x | `300` | 0–2560 |
| target_y | `350` | 0–1440 |
| spell_font | `"Arial"` | Arial / Tahoma / Verdana / Segoe UI |
| spell_font_size | `12` | 8–24 |
| spell_bold | `false` | — |
| spell_color | `9F9F9F` (gray) | hex |
| spell_align | `"center"` | left / center |
| timer_font | `"Arial"` | Arial / Tahoma / Verdana / Segoe UI |
| timer_font_size | `10` | 8–24 |
| timer_bold | `true` | — |
| timer_color | `9F9F9F` (gray) | hex |
| show_timer | `false` | — |
| show_estimate | `false` | — |
| spell_x | `-3` | -200 to 200 |
| spell_y | `-2` | -100 to 100 |
| timer_x | `-15` | -200 to 200 |
| timer_y | `-2` | -100 to 100 |
| hide_default | `true` | — |

---

## KzTimers — Cooldown Timer Defaults

### Per-Timer

| Setting | Default | Notes |
|---------|---------|-------|
| enabled | `true` | — |
| trigger_type | `"buff_add"` | buff_add / buff_remove / cast_success |
| trigger_source | `"player"` | player / target |
| trigger_buff_id | `null` | — |
| trigger_spell_name | `null` | — |
| duration | `10.0` sec | > 0 |
| warning_threshold | `3.0` sec | >= 0 |
| bar_color | `99DD66` (green) | hex |
| warning_color | `FF7744` (orange) | hex |
| bar_direction | `"empty"` | empty (drains) / fill |
| count_direction | `"descending"` | descending (N→0) / ascending (0→N) |
| retrigger | `"restart"` | restart / ignore |

### Presets

3 max. 10 timers per preset max. Labels max 4 characters. All presets start with empty labels and no timers.

---

## KzTimers — Panel Appearance Defaults

| Setting | Default | Range |
|---------|---------|-------|
| bar_height | `20` | 14–28 px |
| font_size | `11` | 8–20 |
| font_bold | `true` | — |
| show_decimals | `true` | — |
| text_offset_x | `0` | -10 to 10 px |
| text_offset_y | `0` | -10 to 10 px |
| shadow_enabled | `false` | — |
| shadow_color | `111111` | hex |
| bg_opacity | `85` | 0–100 |
| colors.background | `0D0D0D` | hex |
| colors.text | `FFFFFF` | hex |
| colors.border | `3A3A30` | hex |
| border_width | `2` | 1–4 px |
| corner_radius | `0` | 0–12 px |
| pos_x | `100` | 0–3840 |
| pos_y | `100` | 0–2160 |
| button_shape | `"rounded"` | square / rounded / pill |
| button_colors.bg | `1A1A18` | hex |
| button_colors.border | `4A4A40` | hex |
| button_colors.hover | `2A2A24` | hex |
| button_colors.active_text | `FF6666` | hex |
| button_colors.inactive | `CCCCCC` | hex |

---

## KzStopwatch — Stopwatch Defaults

### Appearance

| Setting | Default | Range |
|---------|---------|-------|
| layout | `"standard"` | standard / compact |
| width | `220` | 120–400 |
| height | `120` | 40–200 |
| font_size | `28` | 12–48 |
| phase_font_size | `12` | 8–24 |
| bg_opacity | `85` | 0–100 |
| colors.background | `0D0D0D` | hex |
| colors.text | `CCCCCC` | hex |
| colors.border | `3A3A30` | hex |
| border_width | `2` | 1–4 px |
| corner_radius | `0` | 0–12 px |
| font_family | `"Arial"` | Hardcoded — only Arial is embedded in SWF |
| shadow_enabled | `true` | — |
| shadow_color | `111111` | hex |
| button_shape | `"rounded"` | square / rounded / pill |
| button_colors.bg | `1A1A18` | hex |
| button_colors.border | `4A4A40` | hex |
| button_colors.hover | `2A2A24` | hex |
| button_colors.start | `99DD66` (green) | hex |
| button_colors.pause | `FFE066` (yellow) | hex |
| button_colors.stop | `FF7744` (orange) | hex |
| button_colors.disabled | `555555` | hex |
| button_colors.preset_active | `FF6666` | hex |
| button_colors.preset_inactive | `CCCCCC` | hex |
| pos_x | `400` | 0–3840 |
| pos_y | `300` | 0–2160 |

Layout switching sets dimension defaults: Standard (220x120), Compact (220x40).

### Default Presets

3 presets, up to 10 phases each. Labels max 4 characters.

| Preset | Label | End Behavior | Direction | Phases |
|--------|-------|-------------|-----------|--------|
| P1 | `"Kuth"` | continue | descending | Timer Start (5s), Incoming Waves (95s), Half Time (5s), Incoming Waves (65s), Warning (10s), Wave About to End (10s), 10 Sec Remain (10s) — total 200s |
| P2 | `"SG"` | continue | descending | Same as P1 |
| P3 | `"Seed"` | loop | ascending | Seed (10s, red), Silence (6s, green), DPS Scorp (15s, yellow), Kill Scorp (8s, red) — total 39s |

Phase color palette: green (`99DD66`), yellow (`FFE066`), red (`FF7744`).

---

## DamageInfo — Global Settings (Offsets from Game Defaults)

All values are **offsets** from the original game values. `0` = no change.

| Setting | Default Offset | Game Base | Final Value | Range |
|---------|---------------|-----------|-------------|-------|
| show_duration | `0` | 0.2 sec | 0.2 sec | -0.15 to +0.8 |
| fade_duration | `0` | 0.2 sec | 0.2 sec | -0.15 to +0.8 |
| easing_type | `0` | Quad | Quad | 0=Quad / 1=Cubic / 2=Quart |
| dir1_x_offset | `0` | 50 px | 50 px | -50 to +150 |
| dir1_y_offset | `0` | 0 px | 0 px | -200 to +200 |
| fixed_col_x | `0` | 50 px | 50 px | -200 to +200 |
| fixed_col_y | `0` | 100 px | 100 px | -100 to +300 |
| fixed_col_split | `0` | off | off | 0/1 (bool) |
| col_b_x | `0` | 50 px | 50 px | -200 to +200 |
| col_b_y | `0` | 100 px | 100 px | -100 to +300 |
| show_titles | `0` | off | off | 0/1 (bool) |
| other_resource_loss_to_target | `0` | off | off | 0/1 (bool) |
| fixed_y_base | `0` | 100 px | 100 px | -200 to +200 |
| fixed_x_offset | `0` | 200 px | 200 px | -150 to +200 |
| fixed_y_spacing | `0` | 60 px | 60 px | -30 to +60 |
| title_scale | `0` | 0.7x | 0.7x | -0.4 to +0.8 |
| text_scale | `0` | 0.5x | 0.5x | -0.2 to +1.0 |
| shadow_distance | `0` | 4 px | 4 px | -4 to +6 |
| shadow_blur | `0` | 3 px | 3 px | -3 to +7 |

### DamageInfo Presets

| Preset | Animation | Easing | Shadow |
|--------|-----------|--------|--------|
| Default | 0 (no change) | Quad | 0 (no change) |
| Performance | -0.1s (faster) | Quad | -2px (sharper) |
| Beauty | +0.02s (slower) | Cubic | +1px (softer) |

---

## Live Tracker — Overlay Defaults

| Setting | Default | Range |
|---------|---------|-------|
| x | `0` (centered on first run) | 0–3840 |
| y | `50` | 0–2160 |
| width | `210` | 150–600 |
| height | `75` | 60–300 |
| locked | `false` | — |
| transparent_bg | `false` | — |
| opacity | `0.90` | 0.3–1.0 |
| font_size | `11` | 8–20 |
| visible | `true` | — |
