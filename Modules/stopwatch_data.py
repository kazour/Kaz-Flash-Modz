"""
Stopwatch Preset Data Models — KzBuilder 3.3.4

Dataclasses for stopwatch presets: phase-based sequences with configurable
end behavior and count direction. Each preset defines a multi-phase timer
(e.g. Seed Cycle, OS Timer).
"""

import json
import os
from dataclasses import dataclass, field
from typing import List, Dict, Any


# =============================================================================
# Constants
# =============================================================================

MAX_PRESETS = 3
MAX_PHASES_PER_PRESET = 10
SETTINGS_FILENAME = "stopwatch_presets.json"

# Default phase colors
COLOR_GREEN = "99DD66"
COLOR_YELLOW = "FFE066"
COLOR_RED = "FF7744"
COLOR_DEFAULT = "CCCCCC"


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class StopwatchPhase:
    """A single phase in a stopwatch preset sequence."""
    name: str = "Phase"
    duration: float = 10.0      # seconds
    color: str = COLOR_GREEN    # hex string (no prefix)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "duration": self.duration,
            "color": self.color,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StopwatchPhase":
        return cls(
            name=data.get("name", "Phase"),
            duration=float(data.get("duration", 10.0)),
            color=data.get("color", COLOR_GREEN),
        )


@dataclass
class StopwatchPreset:
    """A named preset with a sequence of timed phases.

    End behaviors:
        "loop"     — restart from phase 1 when sequence ends
        "end"      — stop timer when sequence ends
        "continue" — keep counting past the end (negative if descending)

    Count direction:
        "ascending"  — 0 → total duration
        "descending" — total duration → 0
    """
    label: str = ""
    end_behavior: str = "loop"          # "loop" | "end" | "continue"
    count_direction: str = "ascending"  # "ascending" | "descending"
    phases: List[StopwatchPhase] = field(default_factory=list)

    @property
    def total_duration(self) -> float:
        """Total duration of all phases in seconds."""
        return sum(p.duration for p in self.phases)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "label": self.label,
            "end_behavior": self.end_behavior,
            "count_direction": self.count_direction,
            "phases": [p.to_dict() for p in self.phases],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StopwatchPreset":
        end_behavior = data.get("end_behavior", "loop")
        if end_behavior not in ("loop", "end", "continue"):
            end_behavior = "loop"

        count_direction = data.get("count_direction", "ascending")
        if count_direction not in ("ascending", "descending"):
            count_direction = "ascending"

        phases_data = data.get("phases", [])
        phases = [StopwatchPhase.from_dict(p) for p in phases_data[:MAX_PHASES_PER_PRESET]]

        return cls(
            label=data.get("label", "")[:4],
            end_behavior=end_behavior,
            count_direction=count_direction,
            phases=phases,
        )


@dataclass
class StopwatchPresetSettings:
    """Complete stopwatch preset configuration."""
    version: int = 1
    presets: List[StopwatchPreset] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "presets": [p.to_dict() for p in self.presets],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StopwatchPresetSettings":
        presets_data = data.get("presets", [])
        presets = [StopwatchPreset.from_dict(p) for p in presets_data[:MAX_PRESETS]]
        return cls(
            version=data.get("version", 1),
            presets=presets,
        )


# =============================================================================
# Validation
# =============================================================================

def validate_color(color: str) -> bool:
    """Check if color is valid 6-char hex string."""
    if not isinstance(color, str) or len(color) != 6:
        return False
    try:
        int(color, 16)
        return True
    except ValueError:
        return False


def validate_phase(phase: StopwatchPhase) -> List[str]:
    """Validate a single phase, return error messages."""
    errors = []
    if not phase.name:
        errors.append("Phase name is required")
    if phase.duration <= 0:
        errors.append(f"Duration must be positive: {phase.duration}")
    if not validate_color(phase.color):
        errors.append(f"Invalid color: {phase.color}")
    return errors


def validate_preset(preset: StopwatchPreset) -> List[str]:
    """Validate a single preset, return error messages."""
    errors = []
    if len(preset.phases) > MAX_PHASES_PER_PRESET:
        errors.append(f"Maximum {MAX_PHASES_PER_PRESET} phases allowed")
    if preset.end_behavior not in ("loop", "end", "continue"):
        errors.append(f"Invalid end behavior: {preset.end_behavior}")
    if preset.count_direction not in ("ascending", "descending"):
        errors.append(f"Invalid count direction: {preset.count_direction}")
    for phase in preset.phases:
        phase_errors = validate_phase(phase)
        for err in phase_errors:
            errors.append(f"Phase '{phase.name}': {err}")
    return errors


def validate_settings(settings: StopwatchPresetSettings) -> List[str]:
    """Validate complete preset settings, return error messages."""
    errors = []
    if len(settings.presets) > MAX_PRESETS:
        errors.append(f"Maximum {MAX_PRESETS} presets allowed")
    for i, preset in enumerate(settings.presets):
        label = preset.label or f"P{i+1}"
        preset_errors = validate_preset(preset)
        for err in preset_errors:
            errors.append(f"Preset '{label}': {err}")
    return errors


# =============================================================================
# Built-in Templates
# =============================================================================

def _os_timer_phases() -> list:
    """OS Timer phases — extracted from Stopwatch.as getOSPhase()."""
    return [
        StopwatchPhase(name="Timer Start", duration=5.0, color=COLOR_GREEN),
        StopwatchPhase(name="Incoming Waves", duration=95.0, color=COLOR_GREEN),
        StopwatchPhase(name="Half Time", duration=5.0, color=COLOR_YELLOW),
        StopwatchPhase(name="Incoming Waves", duration=65.0, color=COLOR_YELLOW),
        StopwatchPhase(name="Warning", duration=10.0, color=COLOR_YELLOW),
        StopwatchPhase(name="Wave About to End", duration=10.0, color=COLOR_RED),
        StopwatchPhase(name="10 Sec Remain", duration=10.0, color=COLOR_RED),
    ]


def _seed_cycle_phases() -> list:
    """Seed cycle phases — extracted from boss_timer.py Ethram-Fal 39s cycle."""
    return [
        StopwatchPhase(name="Seed", duration=10.0, color=COLOR_RED),
        StopwatchPhase(name="Silence", duration=6.0, color=COLOR_GREEN),
        StopwatchPhase(name="DPS Scorp", duration=15.0, color=COLOR_YELLOW),
        StopwatchPhase(name="Kill Scorp", duration=8.0, color=COLOR_RED),
    ]


# =============================================================================
# Defaults
# =============================================================================

def create_default_presets() -> List[StopwatchPreset]:
    """Create default preset list — Kuth OS, SG OS, Seed Cycle."""
    return [
        StopwatchPreset("Kuth", "continue", "descending", _os_timer_phases()),
        StopwatchPreset("SG", "continue", "descending", _os_timer_phases()),
        StopwatchPreset("Seed", "loop", "ascending", _seed_cycle_phases()),
    ]


def create_default_settings() -> StopwatchPresetSettings:
    """Create default preset settings (empty)."""
    return StopwatchPresetSettings(
        version=1,
        presets=create_default_presets(),
    )


# =============================================================================
# File I/O
# =============================================================================

def load_settings(settings_folder: str) -> StopwatchPresetSettings:
    """Load preset settings from JSON file, or return defaults."""
    filepath = os.path.join(settings_folder, SETTINGS_FILENAME)
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return StopwatchPresetSettings.from_dict(data)
        except (json.JSONDecodeError, KeyError, TypeError):
            # Corrupted file — back up and fall through to defaults
            try:
                backup = filepath + ".corrupt"
                if not os.path.exists(backup):
                    os.rename(filepath, backup)
            except OSError:
                pass
    return create_default_settings()


def save_settings(settings_folder: str, settings: StopwatchPresetSettings) -> bool:
    """Save preset settings to JSON file."""
    filepath = os.path.join(settings_folder, SETTINGS_FILENAME)
    try:
        os.makedirs(settings_folder, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(settings.to_dict(), f, indent=2)
        return True
    except (IOError, OSError):
        return False


# =============================================================================
# Utility
# =============================================================================

def format_duration_display(seconds: float) -> str:
    """Format duration in seconds to human-readable string."""
    if seconds < 60:
        return f"{seconds:.1f}s" if seconds != int(seconds) else f"{int(seconds)}s"
    minutes = int(seconds // 60)
    secs = seconds % 60
    if secs == 0:
        return f"{minutes}m"
    return f"{minutes}m {int(secs)}s"
