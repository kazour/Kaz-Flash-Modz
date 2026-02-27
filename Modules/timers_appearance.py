"""
Timers Appearance Settings Module for KzBuilder 3.3.4
Defines defaults, validation, and I/O for KzTimers visual customization.
"""

import os
import json


# =============================================================================
# DEFAULT SETTINGS
# =============================================================================

TIMERS_APPEARANCE_DEFAULTS = {
    # Bar settings
    "bar_height": 20,           # 14-28 px
    "font_size": 11,            # 8-20 px
    "font_bold": True,
    "show_decimals": True,       # Show .N tenths in countdown
    "text_offset_x": 0,         # -10 to 10 px
    "text_offset_y": 0,         # -10 to 10 px
    "shadow_enabled": False,
    "shadow_color": "111111",
    # Panel settings
    "bg_opacity": 85,           # 0-100
    "colors": {
        "background": "0D0D0D", # Panel background
        "text": "FFFFFF",       # Bar font color
        "border": "3A3A30",     # Panel border
    },
    "border_width": 2,          # 1-4 px
    "corner_radius": 0,         # 0-12 px
    "pos_x": 100,               # 0-3840
    "pos_y": 100,               # 0-2160
    # Button settings
    "button_shape": "rounded",  # "square" / "rounded" / "pill"
    "button_colors": {
        "bg": "1A1A18",         # Preset button background
        "border": "4A4A40",     # Preset button border
        "hover": "2A2A24",      # Preset button hover
        "active_text": "FF6666",# Active preset text color
        "inactive": "CCCCCC",   # Inactive preset text color
    },
}

# =============================================================================
# VALIDATION RANGES
# =============================================================================

TIMERS_APPEARANCE_RANGES = {
    "bar_height":    {"min": 14,  "max": 28,   "step": 1},
    "font_size":     {"min": 8,   "max": 20,   "step": 1},
    "text_offset_x": {"min": -10, "max": 10,   "step": 1},
    "text_offset_y": {"min": -10, "max": 10,   "step": 1},
    "bg_opacity":    {"min": 0,   "max": 100,  "step": 1},
    "border_width":  {"min": 1,   "max": 4,    "step": 1},
    "corner_radius": {"min": 0,   "max": 12,   "step": 1},
    "pos_x":         {"min": 0,   "max": 3840, "step": 1},
    "pos_y":         {"min": 0,   "max": 2160, "step": 1},
}

VALID_BUTTON_SHAPES = ("square", "rounded", "pill")


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_default_settings():
    """Return a deep copy of the default timers appearance settings."""
    defaults = dict(TIMERS_APPEARANCE_DEFAULTS)
    defaults["colors"] = dict(TIMERS_APPEARANCE_DEFAULTS["colors"])
    defaults["button_colors"] = dict(TIMERS_APPEARANCE_DEFAULTS["button_colors"])
    return defaults


def _validate_color(color):
    """Validate a 6-char hex color string. Returns None if invalid."""
    if isinstance(color, str) and len(color) == 6:
        try:
            int(color, 16)
            return color
        except ValueError:
            pass
    return None


def validate_setting(key, value):
    """Validate a single timers appearance setting. Returns clamped/corrected value."""
    if key in ("shadow_enabled", "font_bold", "show_decimals"):
        return bool(value)

    if key == "shadow_color":
        validated = _validate_color(value)
        return validated if validated else TIMERS_APPEARANCE_DEFAULTS["shadow_color"]

    if key == "button_shape":
        return value if value in VALID_BUTTON_SHAPES else TIMERS_APPEARANCE_DEFAULTS["button_shape"]

    if key == "colors":
        if not isinstance(value, dict):
            return dict(TIMERS_APPEARANCE_DEFAULTS["colors"])
        result = {}
        for color_key, default_val in TIMERS_APPEARANCE_DEFAULTS["colors"].items():
            raw = value.get(color_key, default_val)
            validated = _validate_color(raw)
            result[color_key] = validated if validated else default_val
        return result

    if key == "button_colors":
        if not isinstance(value, dict):
            return dict(TIMERS_APPEARANCE_DEFAULTS["button_colors"])
        result = {}
        for color_key, default_val in TIMERS_APPEARANCE_DEFAULTS["button_colors"].items():
            raw = value.get(color_key, default_val)
            validated = _validate_color(raw)
            result[color_key] = validated if validated else default_val
        return result

    if key in TIMERS_APPEARANCE_RANGES:
        r = TIMERS_APPEARANCE_RANGES[key]
        try:
            value = int(value)
            return max(r["min"], min(value, r["max"]))
        except (ValueError, TypeError):
            return TIMERS_APPEARANCE_DEFAULTS.get(key, 0)

    return value


def validate_all_settings(settings):
    """Validate all timers appearance settings, returning cleaned dict."""
    defaults = get_default_settings()
    result = dict(defaults)

    for key, value in settings.items():
        if key in defaults:
            result[key] = validate_setting(key, value)

    # Ensure nested dicts are always complete
    result["colors"] = validate_setting("colors", result.get("colors", {}))
    result["button_colors"] = validate_setting("button_colors", result.get("button_colors", {}))

    return result


# =============================================================================
# SETTINGS FILE I/O
# =============================================================================

SETTINGS_FILENAME = "timers_appearance.json"


def get_settings_path(settings_folder):
    """Get the full path to timers_appearance.json."""
    return os.path.join(settings_folder, SETTINGS_FILENAME)


def load_settings(settings_folder):
    """Load timers appearance settings from JSON file, or return defaults."""
    settings_path = get_settings_path(settings_folder)

    try:
        if os.path.exists(settings_path):
            with open(settings_path, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
            return validate_all_settings(loaded)
    except (json.JSONDecodeError, IOError, OSError):
        pass

    return get_default_settings()


def save_settings(settings_folder, settings):
    """Save timers appearance settings to JSON file."""
    try:
        os.makedirs(settings_folder, exist_ok=True)
        settings_path = get_settings_path(settings_folder)
        validated = validate_all_settings(settings)

        with open(settings_path, 'w', encoding='utf-8') as f:
            json.dump(validated, f, indent=2)

        return True
    except (IOError, OSError):
        return False
