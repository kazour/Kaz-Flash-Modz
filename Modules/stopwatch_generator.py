"""
Stopwatch Generator for KzBuilder 3.3.4

Generates KzStopwatch.as from stopwatch settings + preset data, compiles with MTASC.
"""

import shutil
import tempfile
from pathlib import Path
from typing import Tuple

from .build_utils import compile_as2
from .stopwatch_settings import validate_all_settings
from .stopwatch_data import (
    StopwatchPresetSettings, StopwatchPreset, StopwatchPhase,
    create_default_settings as create_default_presets,
)


# =============================================================================
# TEMPLATE LOADING
# =============================================================================

def _resolve_assets_path(assets_path=None):
    """Resolve the assets directory path."""
    if assets_path is not None:
        return Path(assets_path)
    return Path(__file__).parent.parent / "assets"


def _load_template(assets_path=None):
    """Load KzStopwatch.as.template."""
    base = _resolve_assets_path(assets_path)
    template_path = base / "flash_stopwatch" / "KzStopwatch.as.template"
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()


# =============================================================================
# AS2 LITERAL GENERATION
# =============================================================================

def _escape_as2_string(s: str) -> str:
    """Escape a string for safe inclusion in AS2 string literals."""
    return s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')


def _generate_phase_literal(phase: StopwatchPhase) -> str:
    """Generate AS2 object literal for a StopwatchPhase."""
    name = _escape_as2_string(phase.name)
    dur_ms = int(phase.duration * 1000)
    return f'{{name:"{name}", dur:{dur_ms}, color:0x{phase.color}}}'


def _generate_preset_literal(preset: StopwatchPreset) -> str:
    """Generate AS2 object literal for a StopwatchPreset."""
    label = _escape_as2_string(preset.label)
    total_dur_ms = int(preset.total_duration * 1000)

    phases_arr = []
    i = 0
    while i < len(preset.phases):
        phases_arr.append(_generate_phase_literal(preset.phases[i]))
        i += 1
    phases_str = ", ".join(phases_arr)

    return (
        f'{{label:"{label}", '
        f'endBehavior:"{preset.end_behavior}", '
        f'countDir:"{preset.count_direction}", '
        f'totalDur:{total_dur_ms}, '
        f'phases:[{phases_str}]}}'
    )


# =============================================================================
# CODE GENERATION
# =============================================================================

def generate_stopwatch_code(settings: dict, assets_path=None,
                            preset_settings: StopwatchPresetSettings = None) -> str:
    """
    Generate KzStopwatch.as source code from stopwatch settings + presets.

    Args:
        settings: Validated stopwatch appearance settings dict
        assets_path: Path to assets/ directory (for frozen exe support)
        preset_settings: Preset configuration (None = no presets)

    Returns:
        Complete AS2 source string
    """
    settings = validate_all_settings(settings)
    template = _load_template(assets_path)

    if preset_settings is None:
        preset_settings = create_default_presets()

    # Filter to presets that have phases
    active_presets = [p for p in preset_settings.presets if len(p.phases) > 0]
    num_presets = len(active_presets)

    # Generate presets array literal
    presets_arr = []
    i = 0
    while i < len(active_presets):
        presets_arr.append(_generate_preset_literal(active_presets[i]))
        i += 1
    presets_str = ", ".join(presets_arr)

    replacements = {
        "LAYOUT": settings["layout"],
        "WIDTH": str(settings["width"]),
        "HEIGHT": str(settings["height"]),
        "FONT_SIZE": str(settings["font_size"]),
        "PHASE_FONT_SIZE": str(settings["phase_font_size"]),
        "BG_OPACITY": str(settings["bg_opacity"]),
        "COLOR_BG": settings["colors"]["background"],
        "COLOR_TEXT": settings["colors"]["text"],
        "COLOR_BORDER": settings["colors"]["border"],
        "BORDER_WIDTH": str(settings["border_width"]),
        "CORNER_RADIUS": str(settings["corner_radius"]),
        "FONT_FAMILY": settings["font_family"],
        "SHADOW_ENABLED": "true" if settings["shadow_enabled"] else "false",
        "SHADOW_COLOR": settings["shadow_color"],
        "BUTTON_SHAPE": settings["button_shape"],
        "COLOR_BUTTON_BG": settings["button_colors"]["bg"],
        "COLOR_BUTTON_BORDER": settings["button_colors"]["border"],
        "COLOR_BUTTON_HOVER": settings["button_colors"]["hover"],
        "COLOR_START": settings["button_colors"]["start"],
        "COLOR_PAUSE": settings["button_colors"]["pause"],
        "COLOR_STOP": settings["button_colors"]["stop"],
        "COLOR_DISABLED": settings["button_colors"]["disabled"],
        "COLOR_PRESET_ACTIVE": settings["button_colors"].get("preset_active", "FF6666"),
        "COLOR_PRESET_INACTIVE": settings["button_colors"].get("preset_inactive", "CCCCCC"),
        "POS_X": str(settings["pos_x"]),
        "POS_Y": str(settings["pos_y"]),
        "NUM_PRESETS": str(num_presets),
        "PRESETS_ARRAY": presets_str,
    }

    for key, value in replacements.items():
        template = template.replace(f"%%{key}%%", value)

    return template


# =============================================================================
# BUILD PROCESS
# =============================================================================

def build_stopwatch(
    flash_stopwatch_path: str,
    output_swf: str,
    settings: dict,
    compiler_path: str,
    preset_settings: StopwatchPresetSettings = None
) -> Tuple[bool, str]:
    """
    Complete build process for KzStopwatch.swf.

    Args:
        flash_stopwatch_path: Path to assets/flash_stopwatch/ directory
        output_swf: Path to write final KzStopwatch.swf
        settings: Stopwatch appearance settings dict
        compiler_path: Path to mtasc.exe
        preset_settings: Preset configuration (None = no presets)

    Returns:
        (success: bool, message: str)
    """
    flash_stopwatch_path = Path(flash_stopwatch_path).resolve()
    output_swf = Path(output_swf).resolve()
    compiler_path = Path(compiler_path).resolve()

    base_swf = flash_stopwatch_path / "base.swf"
    common_stubs = flash_stopwatch_path.parent / "common_stubs"

    if not base_swf.exists():
        return False, f"Stopwatch base.swf not found:\n{base_swf}"
    if not compiler_path.exists():
        return False, f"MTASC compiler not found:\n{compiler_path}"

    temp_dir = None
    try:
        # Step 1: Generate AS2 code
        code = generate_stopwatch_code(
            settings, str(flash_stopwatch_path.parent),
            preset_settings=preset_settings)

        # Step 2: Write .as file to temp directory
        temp_dir = tempfile.mkdtemp(prefix="flash_stopwatch_")

        temp_as = Path(temp_dir) / "KzStopwatch.as"
        with open(temp_as, 'w', encoding='utf-8') as f:
            f.write(code)

        # Step 3: Copy base.swf to temp, compile AS2 into it with -main
        output_swf.parent.mkdir(parents=True, exist_ok=True)
        temp_swf = Path(temp_dir) / "KzStopwatch_temp.swf"
        shutil.copy2(base_swf, temp_swf)

        ok, err = compile_as2(
            compiler_path, [common_stubs], temp_swf.name,
            temp_as.name, temp_dir)
        if not ok:
            return False, f"MTASC compilation failed:\n{err}"

        # Step 4: Copy to final location
        shutil.copy2(temp_swf, output_swf)

        output_size = output_swf.stat().st_size
        return True, f"KzStopwatch.swf built successfully ({output_size:,} bytes)"

    except Exception as e:
        return False, f"Build error: {str(e)}"
    finally:
        if temp_dir:
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass
