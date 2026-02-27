"""
Stopwatch Settings Module for KzBuilder 3.3.4
Defines defaults, validation, and I/O for the standalone stopwatch SWF.
"""

import os
import json


# =============================================================================
# DEFAULT SETTINGS
# =============================================================================

STOPWATCH_DEFAULTS = {
    "layout": "standard",       # "standard" | "compact"
    "width": 220,
    "height": 120,
    "font_size": 28,
    "phase_font_size": 12,
    "bg_opacity": 85,           # 0-100
    "colors": {
        "background": "0D0D0D",
        "text": "CCCCCC",
        "border": "3A3A30",
    },
    "border_width": 2,          # 1-4 px
    "corner_radius": 0,         # 0-12 px
    "font_family": "Arial",     # Device font name
    "shadow_enabled": True,
    "shadow_color": "111111",
    "button_shape": "rounded",  # "square" | "rounded" | "pill"
    "button_colors": {
        "bg": "1A1A18",
        "border": "4A4A40",
        "hover": "2A2A24",
        "start": "99DD66",
        "pause": "FFE066",
        "stop": "FF7744",
        "disabled": "555555",
        "preset_active": "FF6666",
        "preset_inactive": "CCCCCC",
    },
    "pos_x": 400,
    "pos_y": 300,
}

# =============================================================================
# VALIDATION RANGES
# =============================================================================

STOPWATCH_RANGES = {
    "width":         {"min": 120, "max": 400, "step": 1},
    "height":        {"min": 40,  "max": 200, "step": 1},
    "font_size":     {"min": 12,  "max": 48,  "step": 1},
    "phase_font_size": {"min": 8, "max": 24, "step": 1},
    "bg_opacity":    {"min": 0,   "max": 100, "step": 1},
    "border_width":  {"min": 1,   "max": 4,   "step": 1},
    "corner_radius": {"min": 0,   "max": 12,  "step": 1},
    "pos_x":         {"min": 0,   "max": 3840, "step": 1},
    "pos_y":         {"min": 0,   "max": 2160, "step": 1},
}

VALID_LAYOUTS = ("standard", "compact")
VALID_FONTS = ("Arial", "Tahoma", "Verdana", "Consolas")
VALID_BUTTON_SHAPES = ("square", "rounded", "pill")


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_default_settings():
    """Return a deep copy of the default stopwatch settings."""
    defaults = dict(STOPWATCH_DEFAULTS)
    defaults["colors"] = dict(STOPWATCH_DEFAULTS["colors"])
    defaults["button_colors"] = dict(STOPWATCH_DEFAULTS["button_colors"])
    return defaults


def _validate_color(color):
    """Validate a 6-char hex color string. Returns default if invalid."""
    if isinstance(color, str) and len(color) == 6:
        try:
            int(color, 16)
            return color
        except ValueError:
            pass
    return None


def validate_setting(key, value):
    """Validate a single stopwatch setting. Returns clamped/corrected value."""
    if key == "layout":
        return value if value in VALID_LAYOUTS else STOPWATCH_DEFAULTS["layout"]

    if key == "font_family":
        return value if value in VALID_FONTS else STOPWATCH_DEFAULTS["font_family"]

    if key == "button_shape":
        return value if value in VALID_BUTTON_SHAPES else STOPWATCH_DEFAULTS["button_shape"]

    if key == "shadow_enabled":
        return bool(value)

    if key == "shadow_color":
        validated = _validate_color(value)
        return validated if validated else STOPWATCH_DEFAULTS["shadow_color"]

    if key == "colors":
        if not isinstance(value, dict):
            return dict(STOPWATCH_DEFAULTS["colors"])
        result = {}
        for color_key, default_val in STOPWATCH_DEFAULTS["colors"].items():
            raw = value.get(color_key, default_val)
            validated = _validate_color(raw)
            result[color_key] = validated if validated else default_val
        return result

    if key == "button_colors":
        if not isinstance(value, dict):
            return dict(STOPWATCH_DEFAULTS["button_colors"])
        result = {}
        for color_key, default_val in STOPWATCH_DEFAULTS["button_colors"].items():
            raw = value.get(color_key, default_val)
            validated = _validate_color(raw)
            result[color_key] = validated if validated else default_val
        return result

    if key in STOPWATCH_RANGES:
        r = STOPWATCH_RANGES[key]
        try:
            value = int(value)
            return max(r["min"], min(value, r["max"]))
        except (ValueError, TypeError):
            return STOPWATCH_DEFAULTS.get(key, 0)

    return value


def validate_all_settings(settings):
    """Validate all stopwatch settings, returning cleaned dict."""
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

SETTINGS_FILENAME = "stopwatch_settings.json"


def get_settings_path(settings_folder):
    """Get the full path to stopwatch_settings.json."""
    return os.path.join(settings_folder, SETTINGS_FILENAME)


def load_settings(settings_folder):
    """Load stopwatch settings from JSON file, or return defaults."""
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
    """Save stopwatch settings to JSON file."""
    try:
        os.makedirs(settings_folder, exist_ok=True)
        settings_path = get_settings_path(settings_folder)
        validated = validate_all_settings(settings)

        with open(settings_path, 'w', encoding='utf-8') as f:
            json.dump(validated, f, indent=2)

        return True
    except (IOError, OSError):
        return False
