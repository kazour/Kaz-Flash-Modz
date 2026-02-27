"""
Cooldown Tracking Data Models — KzBuilder

Each timer represents one tracked ability cooldown:
  Trigger (buff_add | buff_remove | cast_success) → Start countdown bar for N seconds.
"""

import json
import os
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


# =============================================================================
# Enums
# =============================================================================

class TriggerType(Enum):
    BUFF_ADD = "buff_add"
    BUFF_REMOVE = "buff_remove"
    CAST_SUCCESS = "cast_success"


class BarDirection(Enum):
    EMPTY = "empty"     # bar starts full, drains to empty
    FILL = "fill"       # bar starts empty, fills up


class CountDirection(Enum):
    DESCENDING = "descending"  # counts down: N → 0 (default)
    ASCENDING = "ascending"    # counts up: 0 → N


class RetriggerMode(Enum):
    RESTART = "restart"   # reset timer to full duration
    IGNORE = "ignore"     # do nothing while running


# Default colors (hex strings without 0x prefix)
COLOR_DEFAULT = "CCCCCC"
COLOR_WARNING = "FFE066"
COLOR_ALERT = "FF7744"
COLOR_ACTIVE = "99DD66"


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class CooldownTimer:
    """A single cooldown tracker entry.

    Represents one ability/buff to track.
    When the trigger fires, a bar appears counting down 'duration' seconds.
    """
    id: str
    name: str                               # Display label (e.g. "Rune of Aggression")
    enabled: bool = True

    # --- Trigger ---
    trigger_type: str = "buff_add"          # TriggerType value
    trigger_source: str = "player"          # "player" or "target"
    trigger_buff_id: Optional[int] = None   # For buff_add / buff_remove
    trigger_buff_name: Optional[str] = None # Display name from database
    trigger_spell_name: Optional[str] = None # For cast_success

    # --- Timer ---
    duration: float = 10.0                  # Cooldown duration in seconds
    warning_threshold: float = 3.0          # Seconds remaining to show warning color

    # --- Appearance ---
    bar_color: str = COLOR_ACTIVE           # Main bar color (hex)
    warning_color: str = COLOR_ALERT        # Color when warning threshold reached
    bar_direction: str = "empty"            # BarDirection value (empty = drains)

    # --- Behavior ---
    count_direction: str = "descending"     # CountDirection value (descending = N→0)
    retrigger: str = "restart"              # RetriggerMode value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "enabled": self.enabled,
            "trigger_type": self.trigger_type,
            "trigger_source": self.trigger_source,
            "trigger_buff_id": self.trigger_buff_id,
            "trigger_buff_name": self.trigger_buff_name,
            "trigger_spell_name": self.trigger_spell_name,
            "duration": self.duration,
            "warning_threshold": self.warning_threshold,
            "bar_color": self.bar_color,
            "warning_color": self.warning_color,
            "bar_direction": self.bar_direction,
            "count_direction": self.count_direction,
            "retrigger": self.retrigger,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CooldownTimer":
        trigger_type = data.get("trigger_type", TriggerType.BUFF_ADD.value)

        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            enabled=data.get("enabled", True),
            trigger_type=trigger_type,
            trigger_source=data.get("trigger_source", "player"),
            trigger_buff_id=data.get("trigger_buff_id"),
            trigger_buff_name=data.get("trigger_buff_name"),
            trigger_spell_name=data.get("trigger_spell_name"),
            duration=float(data.get("duration", 10.0)),
            warning_threshold=float(data.get("warning_threshold", 3.0)),
            bar_color=data.get("bar_color", COLOR_ACTIVE),
            warning_color=data.get("warning_color", COLOR_ALERT),
            bar_direction=data.get("bar_direction", BarDirection.EMPTY.value),
            count_direction=data.get("count_direction", CountDirection.DESCENDING.value),
            retrigger=data.get("retrigger", RetriggerMode.RESTART.value),
        )


@dataclass
class CooldownPreset:
    """A named group of timers to activate together."""
    label: str = ""
    timer_ids: List[str] = field(default_factory=list)  # IDs of CooldownTimers

    def to_dict(self) -> Dict[str, Any]:
        return {
            "label": self.label,
            "timer_ids": list(self.timer_ids),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CooldownPreset":
        return cls(
            label=data.get("label", "")[:4],
            timer_ids=list(data.get("timer_ids", []))[:MAX_TIMERS_PER_PRESET],
        )


MAX_PRESETS = 3
MAX_TIMERS_PER_PRESET = 10


@dataclass
class CooldownSettings:
    """Complete cooldown tracker configuration."""
    version: int = 2
    enabled: bool = True
    timers: List[CooldownTimer] = field(default_factory=list)
    presets: List[CooldownPreset] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "enabled": self.enabled,
            "timers": [t.to_dict() for t in self.timers],
            "presets": [p.to_dict() for p in self.presets],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CooldownSettings":
        return cls(
            version=2,
            enabled=data.get("enabled", True),
            timers=[CooldownTimer.from_dict(t) for t in data.get("timers", [])],
            presets=[CooldownPreset.from_dict(p)
                     for p in data.get("presets", [])][:MAX_PRESETS],
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


def validate_timer(timer: CooldownTimer) -> List[str]:
    """Validate a single cooldown timer, return error messages."""
    errors = []

    if not timer.id:
        errors.append("Timer ID is required")
    if not timer.name:
        errors.append("Timer name is required")

    # Trigger validation
    if timer.trigger_type not in [t.value for t in TriggerType]:
        errors.append(f"Invalid trigger type: {timer.trigger_type}")
    if timer.trigger_type in (TriggerType.BUFF_ADD.value, TriggerType.BUFF_REMOVE.value):
        if timer.trigger_buff_id is None:
            errors.append("Buff trigger requires a buff ID")
    if timer.trigger_type == TriggerType.CAST_SUCCESS.value:
        if not timer.trigger_spell_name:
            errors.append("Cast trigger requires a spell name")

    # Duration validation
    if timer.duration <= 0:
        errors.append(f"Duration must be positive: {timer.duration}")
    if timer.warning_threshold < 0:
        errors.append(f"Warning threshold cannot be negative: {timer.warning_threshold}")
    if timer.warning_threshold >= timer.duration and timer.warning_threshold > 0:
        errors.append(f"Warning threshold ({timer.warning_threshold}s) must be less than duration ({timer.duration}s)")

    # Color validation
    if not validate_color(timer.bar_color):
        errors.append(f"Invalid bar color: {timer.bar_color}")
    if not validate_color(timer.warning_color):
        errors.append(f"Invalid warning color: {timer.warning_color}")

    return errors


def validate_settings(settings: CooldownSettings) -> List[str]:
    """Validate complete settings, return error messages."""
    errors = []

    # Check for duplicate IDs
    timer_ids = [t.id for t in settings.timers]
    if len(timer_ids) != len(set(timer_ids)):
        errors.append("Duplicate timer IDs found")

    # Validate each timer
    for timer in settings.timers:
        timer_errors = validate_timer(timer)
        for err in timer_errors:
            errors.append(f"Timer '{timer.name}': {err}")

    # Validate presets
    if len(settings.presets) > MAX_PRESETS:
        errors.append(f"Maximum {MAX_PRESETS} presets allowed")
    for i, preset in enumerate(settings.presets):
        if len(preset.timer_ids) > MAX_TIMERS_PER_PRESET:
            name = preset.label or f"P{i+1}"
            errors.append(f"Preset '{name}' has {len(preset.timer_ids)} timers (maximum {MAX_TIMERS_PER_PRESET})")
        for timer_id in preset.timer_ids:
            if timer_id not in timer_ids:
                errors.append(f"Preset '{preset.label}' references unknown timer: {timer_id}")

    # Check for trigger collisions within each preset
    timer_by_id = {t.id: t for t in settings.timers}
    for preset in settings.presets:
        preset_timers = [timer_by_id[tid] for tid in preset.timer_ids if tid in timer_by_id]
        seen_triggers = {}
        for t in preset_timers:
            if t.trigger_type in (TriggerType.BUFF_ADD.value, TriggerType.BUFF_REMOVE.value):
                key = f"{t.trigger_type}:{t.trigger_buff_id}"
            elif t.trigger_type == TriggerType.CAST_SUCCESS.value:
                key = f"cast:{t.trigger_spell_name.strip().lower() if t.trigger_spell_name else ''}"
            else:
                continue
            if key in seen_triggers:
                errors.append(
                    f"Preset '{preset.label}': timers '{seen_triggers[key]}' and '{t.name}' "
                    f"share the same trigger — only one will work in-game"
                )
            else:
                seen_triggers[key] = t.name

    return errors


# =============================================================================
# Default Templates
# =============================================================================

def create_default_presets() -> List[CooldownPreset]:
    """Create default preset list (empty)."""
    return [
        CooldownPreset("", []),
        CooldownPreset("", []),
        CooldownPreset("", []),
    ]


def create_default_settings() -> CooldownSettings:
    """Create default cooldown settings (empty — user adds timers via Add button)."""
    return CooldownSettings(
        version=2,
        enabled=True,
        timers=[],
        presets=create_default_presets(),
    )


# =============================================================================
# File I/O
# =============================================================================

SETTINGS_FILENAME = "timers_data.json"


def load_settings(settings_folder: str) -> CooldownSettings:
    """Load settings from JSON file, or return defaults."""
    filepath = os.path.join(settings_folder, SETTINGS_FILENAME)
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return CooldownSettings.from_dict(data)
        except (json.JSONDecodeError, KeyError, TypeError):
            # Corrupted file — back up and fall through to defaults
            try:
                backup = filepath + ".corrupt"
                if not os.path.exists(backup):
                    os.rename(filepath, backup)
            except OSError:
                pass
    return create_default_settings()


def save_settings(settings_folder: str, settings: CooldownSettings) -> bool:
    """Save settings to JSON file."""
    filepath = os.path.join(settings_folder, SETTINGS_FILENAME)
    try:
        os.makedirs(settings_folder, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(settings.to_dict(), f, indent=2)
        return True
    except (IOError, OSError):
        return False


# =============================================================================
# Utility Functions
# =============================================================================

def generate_timer_id(name: str, existing_ids: List[str]) -> str:
    """Generate a unique timer ID from name."""
    base_id = name.lower().replace(" ", "_")
    base_id = ''.join(c for c in base_id if c.isalnum() or c == '_')
    if not base_id:
        base_id = "timer"

    timer_id = base_id
    counter = 1
    while timer_id in existing_ids:
        timer_id = f"{base_id}_{counter}"
        counter += 1

    return timer_id


def format_duration_display(seconds: float) -> str:
    """Format duration in seconds to human-readable string."""
    if seconds < 60:
        return f"{seconds:.1f}s" if seconds != int(seconds) else f"{int(seconds)}s"
    minutes = int(seconds // 60)
    secs = seconds % 60
    if secs == 0:
        return f"{minutes}m"
    return f"{minutes}m {int(secs)}s"


def parse_duration_input(text: str) -> Optional[float]:
    """Parse user duration input to seconds, return None if invalid."""
    text = text.strip().lower()
    if not text:
        return None

    try:
        # Try pure number (assume seconds)
        if text.replace('.', '', 1).isdigit():
            return float(text)

        # Try with 's' suffix
        if text.endswith('s') and not text.endswith('ms'):
            num = text[:-1].strip()
            if num.replace('.', '', 1).isdigit():
                return float(num)

        # Try with 'ms' suffix
        if text.endswith('ms'):
            num = text[:-2].strip()
            if num.replace('.', '', 1).isdigit():
                return float(num) / 1000.0

        # Try "Xm Ys" format
        if 'm' in text:
            parts = text.split('m')
            minutes = int(parts[0].strip())
            seconds = 0.0
            if len(parts) > 1:
                sec_part = parts[1].replace('s', '').strip()
                if sec_part:
                    seconds = float(sec_part)
            return minutes * 60 + seconds

    except (ValueError, IndexError):
        pass

    return None


