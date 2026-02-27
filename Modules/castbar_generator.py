"""
Castbar Generator for KzBuilder 3.3.4
Generates KzCastbars.as from user settings, compiles with MTASC,
and handles CommandTimerBar.xml for hiding the default castbar.
"""

import re
import shutil
import tempfile
from pathlib import Path
from typing import Tuple

from .castbar_settings import validate_all_settings, STYLE_COLOR_MULT, STYLE_COLOR_OFFS, BAR_STYLE_LINKAGE
from .build_utils import compile_as2


# =============================================================================
# TEMPLATE LOADING
# =============================================================================

def _load_template(assets_path=None):
    """Load AS2 template from external file."""
    if assets_path is not None:
        template_path = Path(assets_path) / "castbars" / "KzCastbars.as.template"
    else:
        template_path = Path(__file__).parent.parent / "assets" / "castbars" / "KzCastbars.as.template"
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()






# =============================================================================
# CODE GENERATION
# =============================================================================

def generate_castbar_code(settings: dict, assets_path=None) -> str:
    """
    Generate KzCastbars.as source code from user settings.

    Args:
        settings: Validated castbar settings dict
        assets_path: Path to assets/ directory (for frozen exe support)

    Returns:
        Complete AS2 source code as string
    """
    settings = validate_all_settings(settings)

    def to_as2_bool(val):
        return "true" if val else "false"

    bar_linkage = BAR_STYLE_LINKAGE.get(settings["bar_style"], "castbar1")

    style = settings["bar_style"]
    color_mult = STYLE_COLOR_MULT.get(style, 1.0)
    color_offs = STYLE_COLOR_OFFS.get(style, 0)

    template = _load_template(assets_path)
    replacements = {
        "PLAYER_COLOR": settings["player_color"],
        "TARGET_COLOR": settings["target_color"],
        "PLAYER_X": settings["player_x"],
        "PLAYER_Y": settings["player_y"],
        "TARGET_X": settings["target_x"],
        "TARGET_Y": settings["target_y"],
        "ENABLE_PLAYER": to_as2_bool(settings["enable_player"]),
        "ENABLE_TARGET": to_as2_bool(settings["enable_target"]),
        "SPELL_FONT": settings["spell_font"],
        "SPELL_FONT_SIZE": settings["spell_font_size"],
        "SPELL_BOLD": to_as2_bool(settings["spell_bold"]),
        "SPELL_COLOR": settings["spell_color"],
        "SPELL_ALIGN": settings["spell_align"],
        "TIMER_FONT": settings["timer_font"],
        "TIMER_FONT_SIZE": settings["timer_font_size"],
        "TIMER_BOLD": to_as2_bool(settings["timer_bold"]),
        "TIMER_COLOR": settings["timer_color"],
        "SHOW_ESTIMATE": to_as2_bool(settings["show_estimate"]),
        "SHOW_TIMER": to_as2_bool(settings["show_timer"]),
        "SPELL_X": settings["spell_x"],
        "SPELL_Y": settings["spell_y"],
        "TIMER_X": settings["timer_x"],
        "TIMER_Y": settings["timer_y"],
        "BAR_LINKAGE": bar_linkage,
        "COLOR_MULT": color_mult,
        "COLOR_OFFS": color_offs,
    }
    for key, value in replacements.items():
        template = template.replace(f"%%{key}%%", str(value))
    return template


# =============================================================================
# BUILD PROCESS
# =============================================================================

def build_castbars(
    castbars_path: str,
    output_swf: str,
    settings: dict,
    compiler_path: str
) -> Tuple[bool, str]:
    """
    Complete build process for KzCastbars.swf.

    Args:
        castbars_path: Path to assets/castbars/ directory
        output_swf: Path to write final KzCastbars.swf
        settings: User castbar settings dict
        compiler_path: Path to mtasc.exe

    Returns:
        (success: bool, message: str)
    """
    castbars_path = Path(castbars_path)
    output_swf = Path(output_swf)
    compiler_path = Path(compiler_path)

    base_swf = castbars_path / "base.swf"
    stubs_path = castbars_path / "stubs"
    common_stubs = castbars_path.parent / "common_stubs"

    # Validate paths
    if not base_swf.exists():
        return False, f"Castbar base.swf not found:\n{base_swf}"
    if not compiler_path.exists():
        return False, f"MTASC compiler not found:\n{compiler_path}"

    temp_dir = None
    try:
        # Step 1: Generate AS2 code
        code = generate_castbar_code(settings, assets_path=str(castbars_path.parent))

        # Step 2: Write to temp .as file
        temp_dir = tempfile.mkdtemp(prefix="castbars_")
        temp_as = Path(temp_dir) / "KzCastbars.as"
        with open(temp_as, 'w', encoding='utf-8') as f:
            f.write(code)

        # Step 3: Copy base.swf to output location
        output_swf.parent.mkdir(parents=True, exist_ok=True)
        temp_swf = Path(temp_dir) / "KzCastbars_temp.swf"
        shutil.copy2(base_swf, temp_swf)

        # Step 4: Compile
        ok, err = compile_as2(compiler_path, [stubs_path, common_stubs], temp_swf, temp_as, temp_dir)
        if not ok:
            return False, f"MTASC compilation failed:\n{err}"

        # Step 5: Move to final location
        shutil.copy2(temp_swf, output_swf)

        output_size = output_swf.stat().st_size
        return True, f"KzCastbars.swf built successfully ({output_size:,} bytes)"

    except Exception as e:
        return False, f"Build error: {str(e)}"
    finally:
        if temp_dir:
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass


# =============================================================================
# COMMAND TIMER BAR XML MANAGEMENT
# =============================================================================

def write_hide_xml(game_path: str) -> Tuple[bool, str]:
    """
    Copy CommandTimerBar.xml from Default to Customized and modify to hide castbar.

    Reads from: Data/Gui/Default/Views/CommandTimerBar.xml
    Writes to:  Data/Gui/Customized/Views/CommandTimerBar.xml

    Args:
        game_path: Path to Age of Conan installation

    Returns:
        (success: bool, message: str)
    """
    try:
        # Source: Default folder (clean original)
        default_xml = Path(game_path) / "Data" / "Gui" / "Default" / "Views" / "CommandTimerBar.xml"
        if not default_xml.exists():
            return False, f"Game's Default CommandTimerBar.xml not found:\n{default_xml}"

        # Output: Customized folder
        customized_path = Path(game_path) / "Data" / "Gui" / "Customized" / "Views"
        customized_path.mkdir(parents=True, exist_ok=True)
        output_xml = customized_path / "CommandTimerBar.xml"

        # Read original
        with open(default_xml, 'r', encoding='utf-8') as f:
            content = f.read()

        # Modify to hide: add max_size_limit="Point(0, 0)" to ProgressBar
        # and set TextView max_size_limit to Point(0, 0)
        content = _modify_commandtimerbar_to_hide(content)

        # Write modified
        with open(output_xml, 'w', encoding='utf-8') as f:
            f.write(content)

        return True, f"Default castbar hidden: {output_xml}"
    except Exception as e:
        return False, f"Failed to write CommandTimerBar.xml: {e}"


def remove_hide_xml(game_path: str) -> Tuple[bool, str]:
    """
    Remove Customized CommandTimerBar.xml so the game falls back to Default.

    Deletes: Data/Gui/Customized/Views/CommandTimerBar.xml

    Args:
        game_path: Path to Age of Conan installation

    Returns:
        (success: bool, message: str)
    """
    try:
        customized_xml = Path(game_path) / "Data" / "Gui" / "Customized" / "Views" / "CommandTimerBar.xml"
        if customized_xml.exists():
            customized_xml.unlink()
            return True, "Default castbar restored (removed Customized override)"
        return True, "Default castbar already active (no Customized override found)"
    except Exception as e:
        return False, f"Failed to restore CommandTimerBar.xml: {e}"


def _modify_commandtimerbar_to_hide(content: str) -> str:
    """
    Modify CommandTimerBar.xml content to hide the castbar.

    Adds max_size_limit="Point(0, 0)" to ProgressBar and sets TextView
    max_size_limit to Point(0, 0) while preserving exact formatting.
    """
    # Add max_size_limit to ProgressBar (insert before bg_gfx or fg_gfx)
    # Pattern: find ProgressBar element, insert max_size_limit if not present
    if 'ProgressBar' in content and 'name="TimerBar"' in content and 'max_size_limit' not in content.split('ProgressBar')[1].split('/>')[0]:
        # Insert max_size_limit before bg_gfx
        content = re.sub(
            r'(name="TimerBar"[^>]*?)(bg_gfx=)',
            r'\1max_size_limit="Point(0, 0)"\n\t\t     \2',
            content
        )

    # Set TextView max_size_limit to Point(0, 0)
    content = re.sub(
        r'(name="ActionName"[^>]*max_size_limit=")Point\([^)]+\)(")',
        r'\1Point(0, 0)\2',
        content
    )

    # Clear TextView value
    content = re.sub(
        r'(name="ActionName"[^>]*value=")[^"]*(")',
        r'\1\2',
        content
    )

    return content
