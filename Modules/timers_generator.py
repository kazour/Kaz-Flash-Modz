"""
Cooldown Timer Generator for KzBuilder 3.3.4

Generates KzTimers.as + TimerManager.as from CooldownSettings, compiles with MTASC.
Two-class architecture: KzTimers (shell/UI/signals) + TimerManager (timer engine).
"""

import shutil
import tempfile
from pathlib import Path
from typing import Tuple

from .build_utils import compile_as2
from .timers_data import (
    CooldownSettings, CooldownTimer, CooldownPreset,
    TriggerType, MAX_TIMERS_PER_PRESET,
    validate_settings
)


# =============================================================================
# TEMPLATE LOADING
# =============================================================================

def _resolve_assets_path(assets_path=None):
    """Resolve the assets directory path."""
    if assets_path is not None:
        return Path(assets_path)
    return Path(__file__).parent.parent / "assets"


def _load_timer_template(assets_path=None):
    """Load KzTimers.as.template."""
    base = _resolve_assets_path(assets_path)
    template_path = base / "flash_timer" / "KzTimers.as.template"
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()


def _load_engine_template(assets_path=None):
    """Load TimerManager.as.template."""
    base = _resolve_assets_path(assets_path)
    template_path = base / "flash_timer" / "TimerManager.as.template"
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()


# =============================================================================
# CODE GENERATION — AS2 LITERALS
# =============================================================================

def _escape_as2_string(s: str) -> str:
    """Escape a string for safe inclusion in AS2 string literals."""
    return s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')


def _generate_timer_literal(timer: CooldownTimer) -> str:
    """Generate AS2 object literal for a CooldownTimer config."""
    enabled = "true" if timer.enabled else "false"
    buff_id = "null" if timer.trigger_buff_id is None else str(timer.trigger_buff_id)
    spell_name = f'"{_escape_as2_string(timer.trigger_spell_name)}"' if timer.trigger_spell_name else "null"
    name = _escape_as2_string(timer.name)
    timer_id = _escape_as2_string(timer.id)

    return (
        f'{{'
        f'id:"{timer_id}", '
        f'name:"{name}", '
        f'enabled:{enabled}, '
        f'triggerType:"{timer.trigger_type}", '
        f'triggerSource:"{timer.trigger_source}", '
        f'triggerBuffId:{buff_id}, '
        f'triggerSpellName:{spell_name}, '
        f'duration:{timer.duration}, '
        f'warningThreshold:{timer.warning_threshold}, '
        f'barColor:0x{timer.bar_color}, '
        f'warningColor:0x{timer.warning_color}, '
        f'barDirection:"{timer.bar_direction}", '
        f'countDirection:"{timer.count_direction}", '
        f'retrigger:"{timer.retrigger}"'
        f'}}'
    )


def _generate_preset_literal(preset: CooldownPreset) -> str:
    """Generate AS2 object literal for a CooldownPreset."""
    label = _escape_as2_string(preset.label)
    ids_arr = ", ".join(f'"{_escape_as2_string(tid)}"' for tid in preset.timer_ids)
    return f'{{label:"{label}", timerIds:[{ids_arr}]}}'


# =============================================================================
# CODE GENERATION — MAIN
# =============================================================================

def generate_flash_timer_code(
    settings: CooldownSettings,
    appearance=None,
    assets_path=None
) -> Tuple[str, str]:
    """
    Generate KzTimers.as and TimerManager.as source code from cooldown settings.

    Args:
        settings: Validated CooldownSettings
        appearance: Appearance settings dict (from timers_appearance.py)
        assets_path: Path to assets/ directory (for frozen exe support)

    Returns:
        Tuple of (timer_code, engine_code) — both complete AS2 source strings
    """
    if appearance is None:
        from .timers_appearance import get_default_settings
        appearance = get_default_settings()

    # Generate timers array
    timers_arr = []
    for timer in settings.timers:
        timers_arr.append(_generate_timer_literal(timer))
    timers_str = ",\n        ".join(timers_arr) if timers_arr else ""

    # Filter to active presets only
    active_presets = [p for p in settings.presets if p.timer_ids]
    num_presets = len(active_presets)

    # Generate presets array
    presets_arr = []
    for preset in active_presets:
        presets_arr.append(_generate_preset_literal(preset))
    presets_str = ", ".join(presets_arr) if presets_arr else ""

    # Determine which game signals are needed
    # Check ALL timers (not just enabled) — presets can enable any timer at runtime
    needs_player = False
    needs_target = False

    for timer in settings.timers:
        src = timer.trigger_source
        trigger_type = timer.trigger_type

        if trigger_type in (TriggerType.BUFF_ADD.value, TriggerType.BUFF_REMOVE.value,
                            TriggerType.CAST_SUCCESS.value):
            if src == "player":
                needs_player = True
            else:
                needs_target = True

    # Panel dimensions
    panel_width = 240
    bar_height = appearance.get("bar_height", 20)
    grow_direction = "down"

    # --- Fill engine template ---
    engine_template = _load_engine_template(assets_path)
    engine_replacements = {
        "TIMERS_ARRAY": timers_str,
        "COLOR_TEXT": appearance["colors"]["text"],
        "MAX_ACTIVE": str(MAX_TIMERS_PER_PRESET),
        "SHOW_DECIMALS": "true" if appearance.get("show_decimals", True) else "false",
    }
    for key, value in engine_replacements.items():
        engine_template = engine_template.replace(f"%%{key}%%", str(value))

    # --- Fill timer template ---
    timer_template = _load_timer_template(assets_path)
    timer_replacements = {
        "PRESETS_ARRAY": presets_str,
        "NEEDS_PLAYER_SIGNALS": "true" if needs_player else "false",
        "NEEDS_TARGET_SIGNALS": "true" if needs_target else "false",
        "PANEL_WIDTH": str(panel_width),
        "BAR_HEIGHT": str(bar_height),
        "GROW_DIRECTION": grow_direction,
        # Appearance placeholders
        "COLOR_BG": appearance["colors"]["background"],
        "COLOR_TEXT": appearance["colors"]["text"],
        "COLOR_BORDER": appearance["colors"]["border"],
        "BG_OPACITY": str(appearance["bg_opacity"]),
        "BORDER_WIDTH": str(appearance["border_width"]),
        "CORNER_RADIUS": str(appearance["corner_radius"]),
        "FONT_SIZE": str(appearance["font_size"]),
        "FONT_BOLD": "true" if appearance.get("font_bold", True) else "false",
        "SHADOW_ENABLED": "true" if appearance.get("shadow_enabled", False) else "false",
        "SHADOW_COLOR": appearance.get("shadow_color", "111111"),
        "TEXT_OFFSET_X": str(appearance.get("text_offset_x", 0)),
        "TEXT_OFFSET_Y": str(appearance.get("text_offset_y", 0)),
        "POS_X": str(appearance.get("pos_x", 100)),
        "POS_Y": str(appearance.get("pos_y", 100)),
        "BUTTON_SHAPE": appearance.get("button_shape", "rounded"),
        "COLOR_BUTTON_BG": appearance["button_colors"]["bg"],
        "COLOR_BUTTON_BORDER": appearance["button_colors"]["border"],
        "COLOR_BUTTON_HOVER": appearance["button_colors"]["hover"],
        "COLOR_BUTTON_ACTIVE": appearance["button_colors"]["active_text"],
        "COLOR_BUTTON_INACTIVE": appearance["button_colors"].get("inactive", "CCCCCC"),
        "MAX_BARS": str(MAX_TIMERS_PER_PRESET),
    }
    for key, value in timer_replacements.items():
        timer_template = timer_template.replace(f"%%{key}%%", str(value))

    return timer_template, engine_template


# =============================================================================
# BUILD PROCESS
# =============================================================================

def build_flash_timer(
    flash_timer_path: str,
    output_swf: str,
    settings: CooldownSettings,
    compiler_path: str,
    appearance: dict = None
) -> Tuple[bool, str]:
    """
    Complete build process for KzTimers.swf.

    Args:
        flash_timer_path: Path to assets/flash_timer/ directory
        output_swf: Path to write final KzTimers.swf
        settings: Cooldown settings
        compiler_path: Path to mtasc.exe

    Returns:
        (success: bool, message: str)
    """
    flash_timer_path = Path(flash_timer_path).resolve()
    output_swf = Path(output_swf).resolve()
    compiler_path = Path(compiler_path).resolve()

    base_swf = flash_timer_path / "base.swf"
    common_stubs = flash_timer_path.parent / "common_stubs"

    # Validate paths
    if not base_swf.exists():
        return False, f"Flash Timer base.swf not found:\n{base_swf}"
    if not compiler_path.exists():
        return False, f"MTASC compiler not found:\n{compiler_path}"

    # Validate settings
    errors = validate_settings(settings)
    if errors:
        return False, "Settings validation failed:\n" + "\n".join(errors)

    temp_dir = None
    try:
        # Step 1: Generate AS2 code (two files)
        timer_code, engine_code = generate_flash_timer_code(
            settings, appearance=appearance, assets_path=str(flash_timer_path.parent))

        # Step 2: Write both .as files to temp directory
        temp_dir = tempfile.mkdtemp(prefix="flash_timer_")

        temp_timer_as = Path(temp_dir) / "KzTimers.as"
        with open(temp_timer_as, 'w', encoding='utf-8') as f:
            f.write(timer_code)

        temp_engine_as = Path(temp_dir) / "TimerManager.as"
        with open(temp_engine_as, 'w', encoding='utf-8') as f:
            f.write(engine_code)

        # Step 3: Copy base.swf to temp location
        output_swf.parent.mkdir(parents=True, exist_ok=True)
        temp_swf = Path(temp_dir) / "KzTimers_temp.swf"
        shutil.copy2(base_swf, temp_swf)

        # Step 4: Compile both AS2 files into one SWF
        ok, err = compile_as2(
            compiler_path, [common_stubs], temp_swf.name,
            [temp_timer_as.name, temp_engine_as.name], temp_dir)
        if not ok:
            return False, f"MTASC compilation failed:\n{err}"

        # Step 5: Move to final location
        shutil.copy2(temp_swf, output_swf)

        output_size = output_swf.stat().st_size
        return True, f"KzTimers.swf built successfully ({output_size:,} bytes)"

    except Exception as e:
        return False, f"Build error: {str(e)}"
    finally:
        if temp_dir:
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass
