"""
Castbar Settings Module for KzBuilder 3.3.5
Defines all castbar compile-time constants, defaults, and validation.
"""

# =============================================================================
# DEFAULT SETTINGS
# =============================================================================

CASTBAR_DEFAULTS = {
    # Bar settings (defaults match AoC default castbar appearance)
    "bar_style": 1,
    "enable_player": True,
    "enable_target": True,
    "player_color": "9C6025",       # Bronze/copper (matches game default)
    "target_color": "9C6025",
    "player_x": 300,
    "player_y": 400,
    "target_x": 300,
    "target_y": 350,

    # Text settings
    "spell_font": "Arial",
    "spell_font_size": 12,
    "spell_bold": False,
    "spell_color": "9F9F9F",        # Medium gray (matches game default)
    "spell_align": "center",
    "timer_font": "Arial",
    "timer_font_size": 10,
    "timer_bold": True,
    "timer_color": "9F9F9F",
    "show_timer": False,
    "show_estimate": False,
    "spell_x": -3,
    "spell_y": -2,
    "timer_x": -15,
    "timer_y": -2,

    # Game UI
    "hide_default": True,
}

# Fonts embedded in the castbar base.swf
CASTBAR_FONTS = ["Arial", "Tahoma", "Verdana", "Segoe UI"]

# Per-style color transform settings (pure tint for grayscale color overlays)
# Style 5: offs=-80 compensates for over-bright grayscale export
STYLE_COLOR_MULT = {1: 1.0, 2: 1.0, 3: 1.0, 4: 1.0, 5: 1.0, 6: 1.0}
STYLE_COLOR_OFFS = {1: 0, 2: 0, 3: 0, 4: 0, 5: -80, 6: 0}

# Flash library linkage IDs per bar style
BAR_STYLE_LINKAGE = {1: "castbar1", 2: "castbar2", 3: "castbar3", 4: "castbar4", 5: "castbar5", 6: "castbar6"}

# =============================================================================
# VALIDATION RANGES
# =============================================================================

CASTBAR_RANGES = {
    "player_x":     {"min": 0,    "max": 2560, "step": 1},
    "player_y":     {"min": 0,    "max": 1440, "step": 1},
    "target_x":     {"min": 0,    "max": 2560, "step": 1},
    "target_y":     {"min": 0,    "max": 1440, "step": 1},
    "spell_font_size": {"min": 8, "max": 24, "step": 1},
    "timer_font_size": {"min": 8, "max": 24, "step": 1},
    "spell_x":      {"min": -200, "max": 200,  "step": 1},
    "spell_y":      {"min": -100, "max": 100,  "step": 1},
    "timer_x":      {"min": -200, "max": 200,  "step": 1},
    "timer_y":      {"min": -100, "max": 100,  "step": 1},
}


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_default_settings():
    """Return a copy of the default castbar settings."""
    return dict(CASTBAR_DEFAULTS)


def validate_color(hex_str):
    """Validate a hex color string. Returns cleaned 6-char hex or default."""
    hex_str = str(hex_str).strip().lstrip('#').upper()
    if len(hex_str) == 6:
        try:
            int(hex_str, 16)
            return hex_str
        except ValueError:
            pass
    return "00FF00"


def validate_setting(key, value):
    """Validate a single castbar setting. Returns clamped/corrected value."""
    if key == "bar_style":
        return value if value in (1, 2, 3, 4, 5, 6) else 1
    if key in ("enable_player", "enable_target", "show_timer", "show_estimate",
               "hide_default", "spell_bold", "timer_bold"):
        return bool(value)
    if key in ("spell_font", "timer_font"):
        return value if value in CASTBAR_FONTS else "Arial"
    if key in ("player_color", "target_color", "spell_color", "timer_color"):
        return validate_color(value)
    if key == "spell_align":
        return value if value in ("left", "center") else "left"
    if key in CASTBAR_RANGES:
        r = CASTBAR_RANGES[key]
        try:
            value = int(value)
            return max(r["min"], min(value, r["max"]))
        except (ValueError, TypeError):
            return CASTBAR_DEFAULTS.get(key, 0)
    return value


def validate_all_settings(settings):
    """Validate all castbar settings, returning cleaned dict."""
    defaults = get_default_settings()
    result = dict(defaults)
    for key, value in settings.items():
        if key in defaults:
            result[key] = validate_setting(key, value)
    return result
