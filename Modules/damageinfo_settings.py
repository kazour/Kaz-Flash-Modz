"""
DamageInfo Settings Module for KzBuilder 3.3.6
Defines all AS2 global settings as OFFSETS from game defaults.

All values are offsets: 0 = no change from original game behavior.
Positive/negative values adjust from the original.
"""

# =============================================================================
# ORIGINAL GAME DEFAULTS (for reference and calculation)
# =============================================================================

GAME_DEFAULTS = {
    # Animation timing
    "show_duration": 0.2,       # seconds
    "fade_duration": 0.2,       # seconds
    "easing_type": 0,           # 0=Quad (gentle), 1=Cubic (moderate), 2=Quart (strong)

    # Direction 1: Above target (floats above player/enemy head)
    "dir1_x_offset": 50,        # pixels left from target head
    "dir1_y_offset": 0,         # pixels vertical shift (0 = at target position)

    # Direction -1: Fixed columns (at fixed screen position)
    # Column A (original): receives plain numbers (no prefix), or all numbers when split is off
    "fixed_col_x": 50,          # Column A: pixels from screen center
    "fixed_col_y": 100,         # Column A: pixels from top of screen
    # Column B (optional): receives prefix numbers (+/-) when split is enabled
    "fixed_col_split": 0,       # 0 = Column A only, 1 = Column A + B (split by prefix)
    "col_b_x": 50,              # Column B: pixels from screen center (same default as A)
    "col_b_y": 100,             # Column B: pixels from top of screen (same default as A)

    # Title text (labels like "CRITICAL", "MANA", etc.)
    "show_titles": 0,           # 0 = disabled (default), 1 = show title labels

    # Enemy resource loss direction override
    "other_resource_loss_to_target": 0,  # 0 = same as player, 1 = show at enemy position

    # Direction 0: Static zig-zag (around player character)
    "fixed_y_base": 100,        # pixels from center (0 = screen center)
    "fixed_x_offset": 200,      # pixels left/right spread
    "fixed_y_spacing": 60,      # pixels between stacked numbers

    # Visual effects
    "title_scale": 0.7,         # multiplier for label (e.g. "CRITICAL")
    "text_scale": 0.5,          # multiplier for damage number
    "shadow_distance": 4,       # pixels
    "shadow_blur": 3,           # pixels
}

# =============================================================================
# GLOBAL AS2 SETTINGS (as offsets from game defaults)
# =============================================================================

GLOBAL_SETTINGS = {
    # =========================================================================
    # Animation Timing (AbstractManager.as)
    # =========================================================================
    "show_duration": {
        "default": 0,           # Offset from 0.2s
        "min": -0.15,           # Minimum 0.05s total
        "max": 0.8,             # Maximum 1.0s total
        "step": 0.05,
        "unit": "sec",
        "description": "Pop-in speed",
        "tooltip": "How fast numbers appear. Negative = faster, positive = slower.",
        "file": "numbersManagers/AbstractManager.as",
        "pattern": r"(static var SHOW_DURATION\s*=\s*)(\d+\.?\d*)",
        "line_hint": 11,
    },
    "fade_duration": {
        "default": 0,           # Offset from 0.2s
        "min": -0.15,           # Minimum 0.05s total
        "max": 0.8,             # Maximum 1.0s total
        "step": 0.05,
        "unit": "sec",
        "description": "Fade-out speed",
        "tooltip": "How fast numbers fade out. Negative = faster, positive = slower.",
        "file": "numbersManagers/AbstractManager.as",
        "pattern": r"(static var FADE_DURATION\s*=\s*)(\d+\.?\d*)",
        "line_hint": 12,
    },
    "easing_type": {
        "default": 0,           # 0=Quad, 1=Cubic, 2=Quart
        "min": 0,
        "max": 2,
        "step": 1,
        "unit": "",
        "type": "enum",
        "options": ["Quad", "Cubic", "Quart"],
        "description": "Animation style",
        "tooltip": "Quad=gentle (t²), Cubic=moderate (t³), Quart=strong (t⁴).",
        "file": "numbersManagers/AbstractManager.as",
        "pattern": r"(static var EASING_TYPE\s*=\s*)(\d+)",
        "line_hint": 13,
    },

    # =========================================================================
    # Direction 1: Above Target (MovingDamageText.as)
    # Numbers float above player head (self) or enemy head (other)
    # =========================================================================
    "dir1_x_offset": {
        "default": 0,           # Offset from 50px
        "min": -50,             # Minimum 0px (directly on target)
        "max": 150,             # Maximum 200px
        "step": 10,
        "unit": "px",
        "description": "X shift from head",
        "tooltip": "How far left from target's head. Negative = closer to head, positive = further left.",
        "file": "numbersTypes/MovingDamageText.as",
        "pattern": r"(static var DIR1_X_OFFSET\s*=\s*)(-?\d+)",
        "line_hint": 6,
    },
    "dir1_y_offset": {
        "default": 0,           # Offset from 0px
        "min": -200,            # Higher above head
        "max": 200,             # Lower (toward head)
        "step": 25,
        "unit": "px",
        "description": "Y shift from head",
        "tooltip": "Vertical adjustment from target's head. Negative = higher above, positive = lower.",
        "file": "numbersTypes/MovingDamageText.as",
        "pattern": r"(static var DIR1_Y_OFFSET\s*=\s*)(-?\d+)",
        "line_hint": 7,
    },

    # =========================================================================
    # Direction -1: Fixed Columns (MovingDamageText.as)
    # Column A: plain numbers (or all numbers when split is off)
    # Column B: prefix numbers (+/-) when split is enabled
    # =========================================================================
    "fixed_col_x": {
        "default": 0,           # Offset from 50px
        "min": -200,            # Minimum -150px (left of center)
        "max": 200,             # Maximum 250px from center
        "step": 25,
        "unit": "px",
        "description": "Col A: X",
        "tooltip": "Column A X position from screen center. Plain numbers go here (or all numbers when split is off).",
        "file": "numbersTypes/MovingDamageText.as",
        "pattern": r"(static var FIXED_COL_X\s*=\s*)(-?\d+)",
        "line_hint": 12,
    },
    "fixed_col_y": {
        "default": 0,           # Offset from 100px
        "min": -100,            # Minimum 0px (top of screen)
        "max": 300,             # Maximum 400px (lower on screen)
        "step": 25,
        "unit": "px",
        "description": "Col A: Y",
        "tooltip": "Column A Y position from top of screen.",
        "file": "numbersTypes/MovingDamageText.as",
        "pattern": r"(static var FIXED_COL_Y\s*=\s*)(-?\d+)",
        "line_hint": 13,
    },
    "fixed_col_split": {
        "default": 0,           # 0 = disabled (Column A only)
        "min": 0,
        "max": 1,
        "step": 1,
        "unit": "",
        "type": "bool",         # Render as checkbox in UI
        "description": "Enable Column B",
        "tooltip": "When enabled, prefix numbers (+/-) go to Column B, plain numbers stay in Column A.",
        "file": "numbersTypes/MovingDamageText.as",
        "pattern": r"(static var FIXED_COL_SPLIT\s*=\s*)(\d+)",
        "line_hint": 14,
    },
    "col_b_x": {
        "default": 0,           # Offset from 50px (same default as Column A)
        "min": -200,            # Minimum -150px (left of center)
        "max": 200,             # Maximum 250px from center
        "step": 25,
        "unit": "px",
        "description": "Col B: X",
        "tooltip": "Column B X position from screen center. Prefix numbers (+/-) go here when split is enabled.",
        "file": "numbersTypes/MovingDamageText.as",
        "pattern": r"(static var COL_B_X\s*=\s*)(-?\d+)",
        "line_hint": 15,
    },
    "col_b_y": {
        "default": 0,           # Offset from 100px (same default as Column A)
        "min": -100,            # Minimum 0px (top of screen)
        "max": 300,             # Maximum 400px (lower on screen)
        "step": 25,
        "unit": "px",
        "description": "Col B: Y",
        "tooltip": "Column B Y position from top of screen. Only used when split is enabled.",
        "file": "numbersTypes/MovingDamageText.as",
        "pattern": r"(static var COL_B_Y\s*=\s*)(-?\d+)",
        "line_hint": 16,
    },

    # =========================================================================
    # Direction 0: Static Zig-Zag (FixedManager.as)
    # Numbers appear in zig-zag pattern around player character
    # =========================================================================
    "fixed_y_base": {
        "default": 0,           # Offset from 100px
        "min": -200,            # Allow going above screen center
        "max": 200,             # Maximum 300px below center
        "step": 25,
        "unit": "px",
        "description": "Zig-zag Y center",
        "tooltip": "Vertical center of zig-zag pattern. Negative = higher, positive = lower.",
        "file": "numbersManagers/FixedManager.as",
        "pattern": r"(static var TEXT_Y_BASE\s*=\s*)(-?\d+)",
        "line_hint": 5,
    },
    "fixed_x_offset": {
        "default": 0,           # Offset from 200px
        "min": -150,            # Minimum 50px from center
        "max": 200,             # Maximum 400px from center
        "step": 25,
        "unit": "px",
        "description": "Zig-zag X spread",
        "tooltip": "How far left/right the zig-zag goes. Negative = tighter, positive = wider.",
        "file": "numbersManagers/FixedManager.as",
        "pattern": r"(static var TEXT_X_OFFSET\s*=\s*)(-?\d+)",
        "line_hint": 6,
    },
    "fixed_y_spacing": {
        "default": 0,           # Offset from 60px
        "min": -30,             # Minimum 30px spacing
        "max": 60,              # Maximum 120px spacing
        "step": 10,
        "unit": "px",
        "description": "Stack spacing",
        "tooltip": "Vertical gap between stacked numbers. Negative = tighter, positive = more spread.",
        "file": "numbersManagers/FixedManager.as",
        "pattern": r"(static var TEXT_Y_OFFSET\s*=\s*)(-?\d+)",
        "line_hint": 7,
    },

    # =========================================================================
    # Title Labels (DamageNumberManager.as)
    # =========================================================================
    "show_titles": {
        "default": 0,           # 0 = disabled (only Dodge/Parry/Resist show labels)
        "min": 0,
        "max": 1,
        "step": 1,
        "unit": "",
        "type": "bool",         # Render as checkbox in UI
        "description": "Show title labels",
        "tooltip": "Show labels like 'CRITICAL', 'MANA', 'STAMINA', 'HEALTH' above damage numbers. When disabled, only Dodge/Parry/Resist labels are shown.",
        "file": "DamageNumberManager.as",
        "pattern": r"(static var SHOW_ALL_TITLES\s*=\s*)(\d+)",
        "line_hint": 18,
    },

    # =========================================================================
    # Enemy Resource Loss Override (DamageNumberManager.as)
    # =========================================================================
    "other_resource_loss_to_target": {
        "default": 0,           # 0 = same direction as player's resource loss
        "min": 0,
        "max": 1,
        "step": 1,
        "unit": "",
        "type": "bool",         # Render as checkbox in UI
        "description": "Enemy drain at target",
        "tooltip": "When enabled, mana/stamina you drain FROM enemies appears above their head instead of at your fixed column position.",
        "file": "DamageNumberManager.as",
        "pattern": r"(static var OTHER_RESOURCE_LOSS_TO_TARGET\s*=\s*)(\d+)",
        "line_hint": 25,
    },

    # =========================================================================
    # Visual Effects (DamageTextAbstract.as)
    # =========================================================================
    "title_scale": {
        "default": 0,           # Offset from 0.7x
        "min": -0.4,            # Minimum 0.3x
        "max": 0.8,             # Maximum 1.5x
        "step": 0.1,
        "unit": "x",
        "description": "Label size",
        "tooltip": "Size of damage type label (e.g. 'CRITICAL'). Negative = smaller, positive = larger.",
        "file": "numbersTypes/DamageTextAbstract.as",
        "pattern": r"(var DEFAULT_TITLE_SCALE\s*=\s*)(\d+\.?\d*)",
        "line_hint": 13,
    },
    "text_scale": {
        "default": 0,           # Offset from 0.5x
        "min": -0.2,            # Minimum 0.3x
        "max": 1.0,             # Maximum 1.5x
        "step": 0.1,
        "unit": "x",
        "description": "Number size",
        "tooltip": "Size of damage numbers. Negative = smaller, positive = larger.",
        "file": "numbersTypes/DamageTextAbstract.as",
        "pattern": r"(var DEFAULT_TEXT_SCALE\s*=\s*)(\d+\.?\d*)",
        "line_hint": 14,
    },
    "shadow_distance": {
        "default": 0,           # Offset from 4px
        "min": -4,              # Minimum 0px (no shadow offset)
        "max": 6,               # Maximum 10px
        "step": 1,
        "unit": "px",
        "description": "Shadow offset",
        "tooltip": "Drop shadow distance. Negative = closer, positive = further.",
        "file": "numbersTypes/DamageTextAbstract.as",
        "pattern": r"(DropShadowFilter\()(\d+)",
        "line_hint": 18,
    },
    "shadow_blur": {
        "default": 0,           # Offset from 3px
        "min": -3,              # Minimum 0px (sharp shadow)
        "max": 7,               # Maximum 10px (very soft)
        "step": 1,
        "unit": "px",
        "description": "Shadow softness",
        "tooltip": "How blurry the shadow is. Negative = sharper, positive = softer.",
        "file": "numbersTypes/DamageTextAbstract.as",
        "pattern": r"(DropShadowFilter\(\d+,\d+,\d+,\d+,)(\d+),(\d+)",
        "line_hint": 18,
    },
}

# Category groupings for UI organization
GLOBAL_CATEGORIES = {
    "Animation Timing": ["show_duration", "fade_duration", "easing_type"],
    "Dir 1: Above Target": ["dir1_x_offset", "dir1_y_offset"],
    "Dir -1: Fixed Columns": ["fixed_col_x", "fixed_col_y", "fixed_col_split", "col_b_x", "col_b_y"],
    "Dir 0: Static Zig-Zag": ["fixed_y_base", "fixed_x_offset", "fixed_y_spacing"],
    "Display Options": ["show_titles", "other_resource_loss_to_target"],
    "Visual Effects": ["title_scale", "text_scale", "shadow_distance", "shadow_blur"],
}

# =============================================================================
# PRESET SYSTEM
# =============================================================================

# Categories hidden from UI (controlled by preset dropdown)
HIDDEN_CATEGORIES = ["Animation Timing", "Visual Effects"]

# Preset configurations: animation speed + easing + shadow
# Designed for 3 use cases: original game feel, performance, and visual quality
PRESETS = {
    "Default": {
        "show_duration": 0,
        "fade_duration": 0,
        "easing_type": 0,        # Quad
        "shadow_distance": 0,
        "shadow_blur": 0,
    },
    "Performance": {
        "show_duration": -0.1,
        "fade_duration": -0.1,
        "easing_type": 0,        # Quad
        "shadow_distance": -2,
        "shadow_blur": -2,
    },
    "Beauty": {
        "show_duration": 0.02,
        "fade_duration": 0.02,
        "easing_type": 1,        # Cubic
        "shadow_distance": 1,
        "shadow_blur": 1,
    },
}

# Preset names in display order
PRESET_NAMES = list(PRESETS.keys())


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_default_global_settings():
    """Return dict with all default offset values (all zeros)."""
    return {key: meta["default"] for key, meta in GLOBAL_SETTINGS.items()}


def validate_global_setting(key, value):
    """Validate a single setting offset value. Returns clamped value."""
    if key not in GLOBAL_SETTINGS:
        return value
    meta = GLOBAL_SETTINGS[key]
    try:
        if isinstance(meta["default"], float) or isinstance(meta["min"], float):
            value = float(value)
        else:
            value = int(value)
        return max(meta["min"], min(value, meta["max"]))
    except (ValueError, TypeError):
        return meta["default"]


def validate_all_global_settings(settings):
    """Validate all global settings offsets, returning cleaned dict."""
    defaults = get_default_global_settings()
    result = dict(defaults)
    for key, value in settings.items():
        if key in GLOBAL_SETTINGS:
            result[key] = validate_global_setting(key, value)
    return result


def compute_final_value(key, offset):
    """
    Compute the final AS2 value from an offset.
    final_value = game_default + offset
    """
    if key not in GAME_DEFAULTS:
        return offset
    return GAME_DEFAULTS[key] + offset


def validate_damageinfo_color(hex_str):
    """Validate a hex color string in 0xRRGGBB format. Returns normalized string or None."""
    hex_str = str(hex_str).strip()
    # Strip any prefix
    if hex_str.startswith('0x') or hex_str.startswith('0X'):
        bare = hex_str[2:]
    elif hex_str.startswith('#'):
        bare = hex_str[1:]
    else:
        bare = hex_str
    bare = bare.upper()
    if len(bare) == 6:
        try:
            int(bare, 16)
            return "0x" + bare
        except ValueError:
            pass
    return None


