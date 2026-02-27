"""
DamageInfo Generator for KzBuilder 3.3.5
Handles AS2 code modification and MTASC compilation for DamageInfo.swf.
"""

import logging
import re
import shutil
import tempfile
from pathlib import Path
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

from Modules.build_utils import compile_as2

from .damageinfo_settings import (
    GLOBAL_SETTINGS,
    GAME_DEFAULTS,
    validate_all_global_settings,
    compute_final_value
)


class DamageInfoGenerator:
    """Generates customized DamageInfo AS2 code from user settings."""

    def __init__(self, source_path: str, settings: dict):
        """
        Initialize generator.

        Args:
            source_path: Path to '__Packages' folder containing AS2 sources
            settings: Dict of user settings (will be validated)
        """
        self.source_path = Path(source_path)
        self.settings = validate_all_global_settings(settings)
        self._modifications = {}

    def generate(self, output_path: str) -> bool:
        """
        Generate modified AS2 files to output directory.

        Args:
            output_path: Path to write modified files

        Returns:
            True if successful, False otherwise
        """
        output_path = Path(output_path)

        try:
            # Step 1: Copy entire source tree to output
            shutil.copytree(self.source_path, output_path, dirs_exist_ok=True)

            # Step 2: Build modifications map
            self._build_modifications()

            # Step 3: Apply modifications to relevant files
            for file_path, replacements in self._modifications.items():
                full_path = output_path / file_path
                if not full_path.exists():
                    logger.warning("File not found: %s", full_path)
                    continue

                self._apply_replacements(full_path, replacements)

            return True

        except Exception as e:
            logger.error("Error generating DamageInfo code: %s", e)
            return False

    def _build_modifications(self):
        """Build dict of {file_path: [(pattern, replacement), ...]}"""
        self._modifications = {}

        for key, meta in GLOBAL_SETTINGS.items():
            file_path = meta["file"]
            value = self.settings[key]

            if file_path not in self._modifications:
                self._modifications[file_path] = []

            # Build replacement based on setting
            replacement = self._build_replacement(key, meta, value)
            if replacement:
                self._modifications[file_path].append(replacement)

    def _build_replacement(self, key: str, meta: dict, offset) -> Optional[Tuple[str, str]]:
        """
        Build a (pattern, replacement) tuple for a setting.

        Args:
            key: Setting key
            meta: Setting metadata from GLOBAL_SETTINGS
            offset: User's offset value (0 = no change from game default)

        Returns:
            (regex_pattern, replacement_string) or None
        """
        # Compute final value: game_default + user_offset
        final_value = compute_final_value(key, offset)

        # Format value appropriately for AS2
        if isinstance(GAME_DEFAULTS.get(key, 0), float):
            formatted_value = f"{float(final_value):.4g}"
        else:
            formatted_value = str(int(final_value))

        # Special handling for shadow_blur (needs to replace two values)
        if key == "shadow_blur":
            # DropShadowFilter(dist,angle,color,alpha,blurX,blurY,...)
            # Match and replace both blurX and blurY
            pattern = r"(DropShadowFilter\(\d+,\d+,\d+,\d+,)(\d+),(\d+)"
            replacement = rf"\g<1>{formatted_value},{formatted_value}"
            return (pattern, replacement)

        # Generic pattern: use the pattern from settings, replace captured group 2
        pattern = meta["pattern"]
        replacement = rf"\g<1>{formatted_value}"
        return (pattern, replacement)

    def _apply_replacements(self, file_path: Path, replacements: list):
        """Apply all replacements to a file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        modified = False
        for pattern, replacement in replacements:
            new_content, count = re.subn(pattern, replacement, content)
            if count > 0:
                content = new_content
                modified = True
            else:
                logger.warning("Pattern did not match in %s: %s...", file_path.name, pattern[:60])

        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)


def build_damageinfo(
    source_path: str,
    backup_swf: str,
    output_swf: str,
    settings: dict,
    compiler_path: str
) -> Tuple[bool, str]:
    """
    Complete build process for DamageInfo.swf.

    Args:
        source_path: Path to '__Packages' folder containing AS2 sources
        backup_swf: Path to DamageInfo_backup.swf (original game file)
        output_swf: Path to write final DamageInfo.swf
        settings: User global settings dict
        compiler_path: Path to mtasc.exe

    Returns:
        (success: bool, message: str)
    """
    source_path = Path(source_path)
    backup_swf = Path(backup_swf)
    output_swf = Path(output_swf)
    compiler_path = Path(compiler_path)

    # Validate paths
    if not source_path.exists():
        return False, f"Source path not found: {source_path}"
    if not backup_swf.exists():
        return False, f"Backup SWF not found: {backup_swf}"
    if not compiler_path.exists():
        return False, f"Compiler not found: {compiler_path}"

    temp_dir = None
    try:
        # Create temp directory for modified sources
        temp_dir = tempfile.mkdtemp(prefix="damageinfo_")
        temp_scripts = Path(temp_dir) / "__Packages"

        # Step 1: Generate modified code
        generator = DamageInfoGenerator(source_path, settings)
        if not generator.generate(temp_scripts):
            return False, "Failed to generate modified AS2 code"

        # Step 2: Copy backup SWF to output location
        output_swf.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(backup_swf, output_swf)

        # Step 3: Find std library paths relative to compiler
        compiler_dir = compiler_path.parent
        std_path = compiler_dir / "std"
        std8_path = compiler_dir / "std8"

        # Step 4: Build MTASC command
        # Entry point is MainDamageNumbers.as
        entry_point = temp_scripts / "MainDamageNumbers.as"
        if not entry_point.exists():
            return False, f"Entry point not found: {entry_point}"

        # Step 5: Compile
        ok, err = compile_as2(compiler_path, [std_path, std8_path, temp_scripts],
                              output_swf, entry_point, temp_dir)
        if not ok:
            return False, f"MTASC compilation failed:\n{err}"

        # Success
        output_size = output_swf.stat().st_size
        return True, f"DamageInfo.swf built successfully ({output_size:,} bytes)"

    except Exception as e:
        return False, f"Build error: {str(e)}"
    finally:
        if temp_dir:
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass
