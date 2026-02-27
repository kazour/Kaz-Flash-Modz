"""
KzGrids Build Script
Compiles the application to an executable and bundles it with assets into a zip file.

Usage:
    python build.py
"""

import subprocess
import shutil
import os
import sys
from pathlib import Path
from datetime import datetime

# Configuration
APP_NAME = "Kaz Flash Modz"
MAIN_SCRIPT = "kzbuilder.py"
VERSION = "3.3.4"

# Directories
ROOT_DIR = Path(__file__).parent
DIST_DIR = ROOT_DIR / "dist"
BUILD_DIR = ROOT_DIR / "build"
BUNDLE_DIR = DIST_DIR / APP_NAME
ASSETS_DIR = ROOT_DIR / "assets"

# Files/folders to include in bundle
ASSETS_TO_COPY = [
    "compiler",
    "common_stubs",
    "kzgrids",
    "damageinfo",
    "castbars",
    "flash_timer",
    "flash_stopwatch",
]

# Profile to include
DEFAULT_PROFILE = None

# Folders to create (empty)
FOLDERS_TO_CREATE = [
    "settings",
    "temp",
]


def clean_build():
    """Remove previous build artifacts."""
    print("Cleaning previous build...")

    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)

    # Remove spec file
    spec_file = ROOT_DIR / f"{APP_NAME}.spec"
    if spec_file.exists():
        spec_file.unlink()

    # Remove old zip
    zip_file = ROOT_DIR / f"{APP_NAME}.zip"
    if zip_file.exists():
        zip_file.unlink()

    print("  Done.")


def build_executable():
    """Build the executable using PyInstaller."""
    print("Building executable with PyInstaller...")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", APP_NAME,
        "--distpath", str(DIST_DIR),
        "--workpath", str(BUILD_DIR),
        "--specpath", str(ROOT_DIR),
        "--hidden-import", "Modules",
        "--hidden-import", "Modules.as2_template",
        "--hidden-import", "Modules.database_editor",
        "--hidden-import", "Modules.damageinfo_tab",
        "--hidden-import", "Modules.damageinfo_generator",
        "--hidden-import", "Modules.damageinfo_settings",
        "--hidden-import", "Modules.damageinfo_xml",
        "--hidden-import", "Modules.build_utils",
        "--hidden-import", "Modules.grids_tab",
        "--hidden-import", "Modules.grids_generator",
        "--hidden-import", "Modules.castbar_tab",
        "--hidden-import", "Modules.castbar_generator",
        "--hidden-import", "Modules.castbar_settings",
        "--hidden-import", "Modules.timers_tab",
        "--hidden-import", "Modules.live_tracker_settings",
        "--hidden-import", "Modules.timers_appearance",
        "--hidden-import", "Modules.timers_data",
        "--hidden-import", "Modules.timers_editor",
        "--hidden-import", "Modules.timers_editor_dialog",
        "--hidden-import", "Modules.timers_generator",
        "--hidden-import", "Modules.boss_timer",
        "--hidden-import", "Modules.timer_overlay",
        "--hidden-import", "Modules.combat_monitor",
        "--hidden-import", "Modules.live_tracker_tab",
        "--hidden-import", "Modules.stopwatch_settings",
        "--hidden-import", "Modules.stopwatch_tab",
        "--hidden-import", "Modules.stopwatch_data",
        "--hidden-import", "Modules.stopwatch_editor",
        "--hidden-import", "Modules.stopwatch_phase_dialog",
        "--hidden-import", "Modules.stopwatch_generator",
        "--hidden-import", "PIL",
        "--hidden-import", "PIL.Image",
        "--hidden-import", "PIL.ImageTk",
        MAIN_SCRIPT
    ]

    result = subprocess.run(cmd, cwd=ROOT_DIR, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"  ERROR: PyInstaller failed!")
        print(result.stderr)
        return False

    exe_path = DIST_DIR / f"{APP_NAME}.exe"
    if not exe_path.exists():
        print(f"  ERROR: Executable not created!")
        return False

    print(f"  Created: {exe_path}")
    return True


def create_bundle():
    """Create the distribution bundle with all required files."""
    print("Creating distribution bundle...")

    # Create bundle directory
    BUNDLE_DIR.mkdir(parents=True, exist_ok=True)

    # Move executable to bundle
    exe_src = DIST_DIR / f"{APP_NAME}.exe"
    exe_dst = BUNDLE_DIR / f"{APP_NAME}.exe"
    shutil.move(str(exe_src), str(exe_dst))
    print(f"  Moved: {APP_NAME}.exe")

    # Create assets folder
    bundle_assets = BUNDLE_DIR / "assets"
    bundle_assets.mkdir(exist_ok=True)

    # Copy assets
    for asset in ASSETS_TO_COPY:
        src = ASSETS_DIR / asset
        dst = bundle_assets / asset

        if src.is_dir():
            shutil.copytree(src, dst)
            print(f"  Copied folder: assets/{asset}")
        elif src.is_file():
            shutil.copy2(src, dst)
            print(f"  Copied file: assets/{asset}")
        else:
            print(f"  WARNING: Asset not found: {asset}")

    # Create empty folders
    for folder in FOLDERS_TO_CREATE:
        folder_path = BUNDLE_DIR / folder
        folder_path.mkdir(exist_ok=True)
        print(f"  Created folder: {folder}")

    # Create empty profiles folder
    profiles_dir = BUNDLE_DIR / "profiles"
    profiles_dir.mkdir(exist_ok=True)

    print("  Done.")
    return True


def create_zip():
    """Create the final zip file."""
    print("Creating zip file...")

    zip_name = f"{APP_NAME}"
    zip_path = ROOT_DIR / f"{zip_name}.zip"

    # Create zip from bundle directory
    shutil.make_archive(
        str(ROOT_DIR / zip_name),
        'zip',
        DIST_DIR,
        APP_NAME
    )

    # Get file size
    size_mb = zip_path.stat().st_size / (1024 * 1024)
    print(f"  Created: {zip_path.name} ({size_mb:.1f} MB)")

    return True


def cleanup_build_artifacts():
    """Remove intermediate build files, keep only zip."""
    print("Cleaning up build artifacts...")

    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)

    spec_file = ROOT_DIR / f"{APP_NAME}.spec"
    if spec_file.exists():
        spec_file.unlink()

    print("  Done.")


def main():
    """Main build process."""
    print("=" * 60)
    print(f"  {APP_NAME} Build Script v{VERSION}")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()

    # Check if PyInstaller is available
    try:
        import PyInstaller
    except ImportError:
        print("ERROR: PyInstaller not installed!")
        print("Run: pip install pyinstaller")
        return 1

    # Build steps
    clean_build()
    print()

    if not build_executable():
        return 1
    print()

    if not create_bundle():
        return 1
    print()

    if not create_zip():
        return 1
    print()

    cleanup_build_artifacts()
    print()

    print("=" * 60)
    print("  BUILD COMPLETE!")
    print(f"  Output: {ROOT_DIR / f'{APP_NAME}.zip'}")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
