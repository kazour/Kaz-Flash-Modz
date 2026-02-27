"""
DamageInfo XML Module for KzBuilder 3.3.5
Handles parsing and generation of TextColors.xml for per-type damage number customization.
"""

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Dict
import copy
import re


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class DamageType:
    """Represents a single damage type's display settings."""
    name: str
    color: str = "0xFFFFFF"           # Hex color (0xRRGGBB)
    font_size: str = "small"          # small, medium, large
    font_family: str = "hyborian3"    # hyborian, hyborian3
    font_style: str = "bold"          # bold, etc.
    speed: int = 100                  # Movement speed
    waitonscreen: float = 2.0         # Display duration (seconds)
    direction: int = 1                # -1=up, 0=static, 1=right

    def to_xml_attribs(self) -> Dict[str, str]:
        """Convert to XML attributes dict."""
        return {
            "name": self.name,
            "color": self.color,
            "font-size": self.font_size,
            "font-style": self.font_style,
            "font-family": self.font_family,
            "speed": str(self.speed),
            "waitonscreen": f"{float(self.waitonscreen):.1f}",
            "direction": str(self.direction),
        }

    @classmethod
    def from_xml_element(cls, elem: ET.Element) -> "DamageType":
        """Create from XML element."""
        return cls(
            name=elem.get("name", ""),
            color=elem.get("color", "0xFFFFFF"),
            font_size=elem.get("font-size", "small"),
            font_family=elem.get("font-family", "hyborian3"),
            font_style=elem.get("font-style", "bold"),
            speed=int(elem.get("speed", "100")),
            waitonscreen=float(elem.get("waitonscreen", "2.0")),
            direction=int(elem.get("direction", "1")),
        )


# =============================================================================
# DAMAGE TYPE CATEGORIES AND METADATA
# =============================================================================

# Maps XML name -> (display_name, category)
DAMAGE_TYPE_INFO = {
    # Heals
    "self_healed": ("Self Healed", "Heals"),
    "other_healed": ("Other Healed", "Heals"),
    "self_healed_critical": ("Self Healed (Crit)", "Heals"),
    "other_healed_critical": ("Other Healed (Crit)", "Heals"),

    # Physical Attacks
    "self_attacked": ("Self Attacked", "Physical Attacks"),
    "other_attacked": ("Other Attacked", "Physical Attacks"),
    "self_attacked_unshielded": ("Self Unshielded", "Physical Attacks"),
    "other_attacked_unshielded": ("Other Unshielded", "Physical Attacks"),
    "self_attacked_critical": ("Self Critical", "Physical Attacks"),
    "other_attacked_critical": ("Other Critical", "Physical Attacks"),

    # Spell Attacks
    "self_attacked_spell": ("Self Spell", "Spell Attacks"),
    "other_attacked_spell": ("Other Spell", "Spell Attacks"),
    "self_attacked_spell_critical": ("Self Spell (Crit)", "Spell Attacks"),
    "other_attacked_spell_critical": ("Other Spell (Crit)", "Spell Attacks"),

    # Combo Attacks
    "self_attacked_combo": ("Self Combo", "Combo Attacks"),
    "other_attacked_combo": ("Other Combo", "Combo Attacks"),
    "self_attacked_combo_critical": ("Self Combo (Crit)", "Combo Attacks"),
    "other_attacked_combo_critical": ("Other Combo (Crit)", "Combo Attacks"),
    "self_combo_name": ("Self Combo Name", "Combo Attacks"),
    "other_combo_name": ("Other Combo Name", "Combo Attacks"),

    # Dodges/Evades
    "self_dodged": ("Self Dodged", "Dodges"),
    "other_dodged": ("Other Dodged", "Dodges"),

    # Environment
    "self_attacked_environment": ("Self Environment", "Environment"),
    "other_attacked_environment": ("Other Environment", "Environment"),

    # Resources
    "stamina_gained": ("Stamina Gained", "Resources"),
    "stamina_lost": ("Stamina Lost", "Resources"),
    "mana_gained": ("Mana Gained", "Resources"),
    "mana_lost": ("Mana Lost", "Resources"),
    "stamina_gained_critical": ("Stamina Gained (Crit)", "Resources"),
    "mana_gained_critical": ("Mana Gained (Crit)", "Resources"),
    "stamina_loss_critical": ("Stamina Loss (Crit)", "Resources"),
    "mana_loss_critical": ("Mana Loss (Crit)", "Resources"),

    # Misc
    "xp_gained": ("XP Gained", "Misc"),
    "murder_points_gained": ("Murder Points", "Misc"),
    "murder_points_gained_murderer": ("Murder Points (Murderer)", "Misc"),
}

# Category order for UI display
CATEGORY_ORDER = [
    "Heals",
    "Physical Attacks",
    "Spell Attacks",
    "Combo Attacks",
    "Dodges",
    "Environment",
    "Resources",
    "Misc",
]


# =============================================================================
# DEFAULT TEXTCOLORS XML TEMPLATE
# =============================================================================
# Loaded from assets/damageinfo/TextColors_default.xml (game default).
# Contains all HTMLColor entries (chat, items, UI) and HTMLFont entries (damage).
# Used as the base template when generating customized TextColors.xml.

_DEFAULT_XML_PATH = Path(__file__).parent.parent / "assets" / "damageinfo" / "TextColors_default.xml"


def _load_default_xml(assets_path=None):
    """Load the default TextColors XML template from the assets folder."""
    if assets_path is not None:
        path = Path(assets_path) / "damageinfo" / "TextColors_default.xml"
    else:
        path = _DEFAULT_XML_PATH
    return path.read_text(encoding='utf-8')


# =============================================================================
# DEFAULT VALUES (from game default TextColors.xml)
# =============================================================================

DEFAULT_DAMAGE_TYPES = {
    # Heals
    "self_healed": DamageType("self_healed", "0x5B933D", "small", "hyborian3", "bold", 100, 2.0, -1),
    "other_healed": DamageType("other_healed", "0x5B9364", "small", "hyborian3", "bold", 100, 2.0, -1),
    "self_healed_critical": DamageType("self_healed_critical", "0x5B933D", "large", "hyborian3", "bold", 50, 2.0, 0),
    "other_healed_critical": DamageType("other_healed_critical", "0x5B9364", "large", "hyborian3", "bold", 50, 2.0, -1),

    # Physical Attacks
    "self_attacked": DamageType("self_attacked", "0xb41d1d", "small", "hyborian3", "bold", 100, 2.0, 1),
    "other_attacked": DamageType("other_attacked", "0x8a8a89", "small", "hyborian3", "bold", 100, 2.0, 1),
    "self_attacked_unshielded": DamageType("self_attacked_unshielded", "0xb41d1d", "medium", "hyborian3", "bold", 100, 2.0, 1),
    "other_attacked_unshielded": DamageType("other_attacked_unshielded", "0xd7d7d7", "medium", "hyborian3", "bold", 100, 2.0, 1),
    "self_attacked_critical": DamageType("self_attacked_critical", "0xb41d1d", "medium", "hyborian3", "bold", 50, 3.0, 1),
    "other_attacked_critical": DamageType("other_attacked_critical", "0xd7d7d7", "large", "hyborian3", "bold", 50, 3.0, 0),

    # Spell Attacks
    "self_attacked_spell": DamageType("self_attacked_spell", "0xb41d1d", "small", "hyborian3", "bold", 100, 2.0, 1),
    "other_attacked_spell": DamageType("other_attacked_spell", "0xFFFFFF", "small", "hyborian3", "bold", 100, 2.0, 1),
    "self_attacked_spell_critical": DamageType("self_attacked_spell_critical", "0xFFFFFF", "large", "hyborian3", "bold", 50, 3.0, 0),
    "other_attacked_spell_critical": DamageType("other_attacked_spell_critical", "0xFFFFFF", "large", "hyborian3", "bold", 50, 3.0, 0),

    # Combo Attacks
    "self_attacked_combo": DamageType("self_attacked_combo", "0xb41d1d", "medium", "hyborian3", "bold", 100, 2.0, 1),
    "other_attacked_combo": DamageType("other_attacked_combo", "0xFF8040", "medium", "hyborian3", "bold", 100, 2.0, 1),
    "self_attacked_combo_critical": DamageType("self_attacked_combo_critical", "0xb41d1d", "medium", "hyborian3", "bold", 50, 3.0, 1),
    "other_attacked_combo_critical": DamageType("other_attacked_combo_critical", "0xFF8040", "large", "hyborian3", "bold", 50, 3.0, 0),
    "self_combo_name": DamageType("self_combo_name", "0xb41d1d", "small", "hyborian3", "bold", 100, 2.0, 1),
    "other_combo_name": DamageType("other_combo_name", "0xFF8040", "small", "hyborian3", "bold", 100, 2.0, 1),

    # Dodges
    "self_dodged": DamageType("self_dodged", "0xFFFFFF", "medium", "hyborian3", "bold", 100, 2.0, 1),
    "other_dodged": DamageType("other_dodged", "0x999999", "medium", "hyborian3", "bold", 100, 2.0, 1),

    # Environment
    "self_attacked_environment": DamageType("self_attacked_environment", "0xb41d1d", "medium", "hyborian3", "bold", 100, 2.0, 1),
    "other_attacked_environment": DamageType("other_attacked_environment", "0xBBBBBB", "small", "hyborian3", "bold", 100, 2.0, 1),

    # Resources
    "stamina_gained": DamageType("stamina_gained", "0x6da0ff", "small", "hyborian3", "bold", 100, 2.0, -1),
    "stamina_lost": DamageType("stamina_lost", "0x6da0ff", "small", "hyborian3", "bold", 100, 2.0, 1),
    "mana_gained": DamageType("mana_gained", "0x2222FF", "small", "hyborian3", "bold", 100, 2.0, -1),
    "mana_lost": DamageType("mana_lost", "0x2222FF", "small", "hyborian3", "bold", 100, 2.0, 1),
    "stamina_gained_critical": DamageType("stamina_gained_critical", "0x6da0ff", "large", "hyborian3", "bold", 50, 3.0, -1),
    "mana_gained_critical": DamageType("mana_gained_critical", "0x2222FF", "large", "hyborian3", "bold", 50, 3.0, -1),
    "stamina_loss_critical": DamageType("stamina_loss_critical", "0x6da0ff", "large", "hyborian3", "bold", 50, 3.0, 1),
    "mana_loss_critical": DamageType("mana_loss_critical", "0x2222FF", "large", "hyborian3", "bold", 50, 3.0, 1),

    # Misc
    "xp_gained": DamageType("xp_gained", "0x9999FF", "small", "hyborian3", "bold", 50, 3.0, -1),
    "murder_points_gained": DamageType("murder_points_gained", "0xa65300", "small", "hyborian3", "bold", 100, 2.0, -1),
    "murder_points_gained_murderer": DamageType("murder_points_gained_murderer", "0xb41d1d", "small", "hyborian3", "bold", 100, 2.0, -1),
}


# =============================================================================
# VALIDATION
# =============================================================================

VALID_FONT_SIZES = ["small", "medium", "large"]
VALID_FONT_FAMILIES = ["hyborian", "hyborian3"]
VALID_DIRECTIONS = [-1, 0, 1]


def validate_color(color: str) -> str:
    """Validate and normalize hex color."""
    color = color.strip()
    # Accept both 0xRRGGBB and #RRGGBB formats
    if color.startswith("#"):
        color = "0x" + color[1:]
    if not color.startswith("0x"):
        color = "0x" + color
    # Validate hex digits
    hex_part = color[2:]
    if len(hex_part) != 6:
        return "0xFFFFFF"
    try:
        int(hex_part, 16)
        return color
    except ValueError:
        return "0xFFFFFF"


def validate_damage_type(dtype: DamageType) -> DamageType:
    """Validate and clamp all fields of a DamageType."""
    return DamageType(
        name=dtype.name,
        color=validate_color(dtype.color),
        font_size=dtype.font_size if dtype.font_size in VALID_FONT_SIZES else "small",
        font_family=dtype.font_family if dtype.font_family in VALID_FONT_FAMILIES else "hyborian3",
        font_style=dtype.font_style or "bold",
        speed=max(1, min(200, dtype.speed)),
        waitonscreen=max(0.5, min(10.0, dtype.waitonscreen)),
        direction=dtype.direction if dtype.direction in VALID_DIRECTIONS else 1,
    )


# =============================================================================
# XML PARSING AND GENERATION
# =============================================================================

def parse_textcolors_xml(filepath: str) -> Dict[str, DamageType]:
    """
    Parse TextColors.xml and extract HTMLFont entries for damage types.

    Returns dict mapping type name -> DamageType object.
    Only returns entries that are damage-related (defined in DAMAGE_TYPE_INFO).
    """
    result = {}

    try:
        tree = ET.parse(filepath)
        root = tree.getroot()

        for elem in root.findall("HTMLFont"):
            name = elem.get("name", "")
            if name in DAMAGE_TYPE_INFO:
                dtype = DamageType.from_xml_element(elem)
                result[name] = validate_damage_type(dtype)
    except ET.ParseError as e:
        print(f"Error parsing TextColors.xml (malformed XML): {e}")
    except FileNotFoundError:
        print(f"TextColors.xml not found: {filepath}")
    except Exception as e:
        print(f"Error reading TextColors.xml: {e}")

    return result


def get_default_damage_types() -> Dict[str, DamageType]:
    """Return a deep copy of the default damage types."""
    return {name: copy.copy(dtype) for name, dtype in DEFAULT_DAMAGE_TYPES.items()}


def generate_textcolors_xml(
    damage_types: Dict[str, DamageType],
    output_path: str,
    source_template: str = None,
    assets_path=None
) -> bool:
    """
    Generate TextColors.xml with custom damage type settings.

    Uses regex-based replacement to preserve EXACT formatting of the source file.
    Only attribute VALUES are changed - all spacing, quotes, comments preserved.

    Args:
        damage_types: Dict of type name -> DamageType with custom settings
        output_path: Path to write the modified XML
        source_template: Path to source XML file to use as template (optional).
                        If None, uses the default TextColors_default.xml from assets.
        assets_path: Path to assets/ directory (for frozen exe support)

    Returns:
        True if successful, False otherwise
    """
    try:
        # Read source template
        if source_template:
            with open(source_template, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            # Use default template with proper header
            content = (
                '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>\n'
                '<!-- $Change: 601173 $ (must be within the first 200 characters of the file) -->\n'
                + _load_default_xml(assets_path)
            )

        # For each damage type, find and update its HTMLFont line
        for name, dtype in damage_types.items():
            dtype = validate_damage_type(dtype)
            content = _replace_htmlfont_attributes(content, name, dtype)

        # Write output preserving exact content
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return True

    except Exception as e:
        print(f"Error generating TextColors.xml: {e}")
        return False


def _replace_htmlfont_attributes(content: str, type_name: str, dtype: DamageType) -> str:
    """
    Replace attribute values for a specific HTMLFont element while preserving formatting.

    Finds the HTMLFont line with the given name and replaces attribute values in-place,
    preserving all whitespace, quote styles, and spacing.
    """
    # Pattern to find the HTMLFont line with this name
    # Matches: <HTMLFont name="type_name" ... /> or <HTMLFont name='type_name' ... />
    line_pattern = re.compile(
        r'(<HTMLFont\s+[^>]*name\s*=\s*["\']' + re.escape(type_name) + r'["\'][^>]*/\s*>)',
        re.IGNORECASE
    )

    match = line_pattern.search(content)
    if not match:
        return content  # Type not found in template, skip

    original_line = match.group(1)
    modified_line = original_line

    # Replace each attribute value, preserving quote style and spacing
    # Attributes to update: color, font-size, font-style, font-family, speed, waitonscreen, direction
    attr_values = {
        'color': dtype.color,
        'font-size': dtype.font_size,
        'font-style': dtype.font_style,
        'font-family': dtype.font_family,
        'speed': str(dtype.speed),
        'waitonscreen': f"{dtype.waitonscreen:.1f}",
        'direction': str(dtype.direction),
    }

    for attr_name, new_value in attr_values.items():
        # Pattern matches: attr_name (optional space) = (optional space) (quote) value (quote)
        # Preserves: the attribute name, spacing around =, and quote style
        attr_pattern = re.compile(
            r'(' + re.escape(attr_name) + r'\s*=\s*)(["\'])([^"\']*)\2'
        )
        attr_match = attr_pattern.search(modified_line)
        if attr_match:
            # Replace keeping the prefix (attr=) and quote style
            prefix = attr_match.group(1)
            quote = attr_match.group(2)
            modified_line = attr_pattern.sub(prefix + quote + new_value + quote, modified_line)

    # Replace the original line with modified line in content
    content = content[:match.start()] + modified_line + content[match.end():]

    return content


def get_types_by_category() -> Dict[str, list]:
    """
    Get damage types organized by category.

    Returns dict mapping category name -> list of type names in that category.
    """
    result = {cat: [] for cat in CATEGORY_ORDER}

    for type_name, (display_name, category) in DAMAGE_TYPE_INFO.items():
        if category in result:
            result[category].append(type_name)

    return result


def get_display_name(type_name: str) -> str:
    """Get the display name for a damage type."""
    if type_name in DAMAGE_TYPE_INFO:
        return DAMAGE_TYPE_INFO[type_name][0]
    return type_name


def damage_type_to_dict(dtype: DamageType) -> dict:
    """Convert DamageType to a serializable dict."""
    return {
        "name": dtype.name,
        "color": dtype.color,
        "font_size": dtype.font_size,
        "font_family": dtype.font_family,
        "font_style": dtype.font_style,
        "speed": dtype.speed,
        "waitonscreen": dtype.waitonscreen,
        "direction": dtype.direction,
    }


def dict_to_damage_type(data: dict) -> DamageType:
    """Create DamageType from a dict."""
    return DamageType(
        name=data.get("name", ""),
        color=data.get("color", "0xFFFFFF"),
        font_size=data.get("font_size", "small"),
        font_family=data.get("font_family", "hyborian3"),
        font_style=data.get("font_style", "bold"),
        speed=data.get("speed", 100),
        waitonscreen=float(data.get("waitonscreen", 2.0)),
        direction=data.get("direction", 1),
    )
