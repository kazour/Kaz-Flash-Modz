"""
Timers Tab Module for KzBuilder 3.3.6
Cooldown Editor with integrated appearance settings.
Stopwatch moved to StopwatchTab in v3.2.0.
"""

import json
import tkinter as tk
from tkinter import ttk, filedialog
from ttkbootstrap.dialogs import Messagebox
from pathlib import Path

from .timers_data import CooldownSettings, create_default_settings, MAX_TIMERS_PER_PRESET
from .timers_editor import TimersEditorPanel
from .timers_generator import build_flash_timer
from .timers_appearance import (
    get_default_settings as get_default_appearance,
    validate_all_settings as validate_appearance,
    load_settings as load_appearance,
    save_settings as save_appearance,
)
from .ui_helpers import (
    THEME_COLORS,
    create_tip_bar, create_profile_info_bar,
    BTN_MEDIUM,
    FONT_SMALL,
)


class TimersTab(ttk.Frame):
    """
    Timers tab UI — Cooldown Editor with integrated appearance controls.

    Usage:
        tab = TimersTab(notebook, settings_manager)
        notebook.add(tab, text="Timers")
    """

    def __init__(self, parent, settings_manager, assets_path=None, database=None,
                 on_open_database=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self._assets_path = assets_path
        self.database = database
        self.on_open_database = on_open_database
        self.profile_label = tk.StringVar(value="No profile loaded")
        self.timer_count_label = tk.StringVar(value="")
        self.settings_folder = str(Path(settings_manager.filepath).parent)

        # Load appearance settings
        self.appearance_settings = load_appearance(self.settings_folder)

        self._build_ui()

    def _build_ui(self):
        """Build the tab UI with button bar and timer editor."""
        # === BUTTONS (top bar) ===
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill='x', padx=10, pady=(5, 5))

        ttk.Button(btn_frame, text="Reset", command=self._reset_appearance,
                   width=BTN_MEDIUM).pack(side='left', padx=2)

        # Build status label
        self.build_status = ttk.Label(
            btn_frame, text="",
            font=FONT_SMALL, foreground=THEME_COLORS['muted']
        )
        self.build_status.pack(side='left', padx=(10, 0))

        ttk.Button(btn_frame, text="Build", command=self._build_flash_timer,
                   width=BTN_MEDIUM).pack(side='right', padx=2)
        ttk.Button(btn_frame, text="Export...", command=self._export_settings,
                   width=BTN_MEDIUM).pack(side='right', padx=2)
        ttk.Button(btn_frame, text="Import...", command=self._import_settings,
                   width=BTN_MEDIUM).pack(side='right', padx=2)

        # === TIP BAR + PROFILE INFO ===
        create_tip_bar(self, "Configure KzTimers cooldown trackers and panel appearance.")
        create_profile_info_bar(self, self.profile_label,
                               extra_labels=[self.timer_count_label])

        # === TIMER EDITOR (with integrated appearance settings) ===
        self.timer_editor = TimersEditorPanel(
            self, self.settings_folder,
            on_change=self._on_timer_settings_change,
            database=self.database,
            appearance_settings=self.appearance_settings,
            on_appearance_change=self._on_appearance_settings_change,
        )
        self.timer_editor.pack(fill='both', expand=True, padx=10, pady=5)
        self._update_timer_count()

    def _update_timer_count(self):
        """Update the timer count in the profile info bar."""
        idx = self.timer_editor.selected_preset_index
        if idx < len(self.timer_editor.settings.presets):
            count = len(self.timer_editor.settings.presets[idx].timer_ids)
        else:
            count = 0
        self.timer_count_label.set(f"{count} / {MAX_TIMERS_PER_PRESET} timers")

    def _on_timer_settings_change(self):
        """Handle timer editor settings changes."""
        if hasattr(self, 'timer_editor'):
            self._update_timer_count()

    def _on_appearance_settings_change(self, new_settings):
        """Called by editor panel when appearance controls change."""
        self.appearance_settings = new_settings
        save_appearance(self.settings_folder, self.appearance_settings)

    # =========================================================================
    # Add / Edit / Database
    # =========================================================================

    def _add_timer(self):
        """Open TimerEditorDialog to add a new timer."""
        idx = self.timer_editor.selected_preset_index
        if idx < len(self.timer_editor.settings.presets):
            preset = self.timer_editor.settings.presets[idx]
            if len(preset.timer_ids) >= MAX_TIMERS_PER_PRESET:
                Messagebox.show_warning(
                    f"Maximum {MAX_TIMERS_PER_PRESET} timers per preset reached.",
                    title="Limit Reached"
                )
                return
        from .timers_editor_dialog import TimerEditorDialog
        dialog = TimerEditorDialog(
            self,
            database=self.database,
            existing_ids=[t.id for t in self.timer_editor.settings.timers],
        )
        self.wait_window(dialog)
        if dialog.result is not None:
            timer = dialog.result
            self.timer_editor.settings.timers.append(timer)
            # Auto-assign to current preset
            preset_idx = self.timer_editor.selected_preset_index
            while len(self.timer_editor.settings.presets) <= preset_idx:
                from .timers_data import CooldownPreset
                self.timer_editor.settings.presets.append(CooldownPreset())
            self.timer_editor.settings.presets[preset_idx].timer_ids.append(timer.id)
            self.timer_editor._refresh_timer_list()
            self.timer_editor._select_timer(len(self.timer_editor.settings.timers) - 1)
            self.timer_editor._save_and_notify()

    def _edit_timer(self):
        """Open TimerEditorDialog to edit the selected timer."""
        idx = self.timer_editor.selected_timer_index
        if idx is None or idx >= len(self.timer_editor.settings.timers):
            Messagebox.show_info("Select a timer to edit.", title="Edit Timer")
            return
        from .timers_editor_dialog import TimerEditorDialog
        timer = self.timer_editor.settings.timers[idx]
        dialog = TimerEditorDialog(
            self,
            database=self.database,
            existing_ids=[t.id for t in self.timer_editor.settings.timers],
            timer=timer,
        )
        self.wait_window(dialog)
        if dialog.result is not None:
            self.timer_editor.settings.timers[idx] = dialog.result
            self.timer_editor._refresh_timer_list()
            self.timer_editor._select_timer(idx)
            self.timer_editor._save_and_notify()

    def _open_database(self):
        """Open the database editor window."""
        if self.on_open_database:
            self.on_open_database()

    # =========================================================================
    # Build
    # =========================================================================

    def _build_flash_timer(self):
        """Build the Flash Timer SWF with timer definitions."""
        game_path = self.settings_manager.get("game_path", "")

        if not game_path:
            Messagebox.show_error(
                "Game path not set.\n\nSet the game path on the Welcome screen first.",
                title="Error"
            )
            return

        if self._assets_path is not None:
            base_assets = Path(self._assets_path)
        else:
            base_assets = Path(__file__).parent.parent / "assets"
        assets_path = base_assets / "flash_timer"
        compiler_path = base_assets / "compiler" / "mtasc.exe"
        output_path = Path(game_path) / "Data" / "Gui" / "Default" / "Flash" / "KzTimers.swf"

        base_swf = assets_path / "base.swf"
        if not base_swf.exists():
            Messagebox.show_error(
                f"Flash Timer base.swf not found:\n{base_swf}\n\n"
                "You need to create this file in Flash CS6.\n"
                "See assets/flash_timer/README.md for instructions.",
                title="Missing base.swf"
            )
            return

        self.build_status.config(text="Building...", foreground=THEME_COLORS['warning'])
        self.update()

        settings = self.timer_editor.get_settings()

        success, message = build_flash_timer(
            str(assets_path),
            str(output_path),
            settings,
            str(compiler_path),
            appearance=self.appearance_settings
        )

        if success:
            self.build_status.config(text="Build successful!", foreground=THEME_COLORS['success'])
            Messagebox.show_info(
                f"{message}\n\nOutput: {output_path}\n\n"
                "In-game, type /reloadui to load the new timer.",
                title="Build Complete"
            )
        else:
            self.build_status.config(text="Build failed", foreground=THEME_COLORS['danger'])
            Messagebox.show_error(message, title="Build Failed")

    # =========================================================================
    # Import / Export
    # =========================================================================

    def _export_settings(self):
        """Export timers settings (timers + appearance) to JSON."""
        path = filedialog.asksaveasfilename(
            defaultextension='.json',
            filetypes=[('JSON files', '*.json')],
            title="Export Timers Settings"
        )
        if not path:
            return
        try:
            data = self.get_profile_data()
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            Messagebox.show_error(str(e), title="Export Error")

    def _import_settings(self):
        """Import timers settings from JSON."""
        path = filedialog.askopenfilename(
            filetypes=[('JSON files', '*.json')],
            title="Import Timers Settings"
        )
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.load_profile_data(data)
        except (json.JSONDecodeError, IOError) as e:
            Messagebox.show_error(f"Failed to import: {e}", title="Import Error")

    def _reset_appearance(self):
        """Reset appearance settings to defaults (does not touch timers)."""
        result = Messagebox.yesno(
            "Reset all appearance settings to defaults?",
            title="Reset Appearance"
        )
        if result == "Yes":
            self.appearance_settings = get_default_appearance()
            save_appearance(self.settings_folder, self.appearance_settings)
            if hasattr(self, 'timer_editor'):
                self.timer_editor.load_appearance(self.appearance_settings)

    def _delete_all_timers(self):
        """Delete all timers from all presets after confirmation."""
        if not self.timer_editor.settings.timers:
            return
        result = Messagebox.yesno(
            "Delete all timers from all presets?",
            title="Delete All Timers"
        )
        if result == "Yes":
            self.timer_editor.settings.timers.clear()
            for preset in self.timer_editor.settings.presets:
                preset.timer_ids.clear()
            self.timer_editor.selected_timer_index = None
            self.timer_editor._refresh_timer_list()
            self.timer_editor._save_and_notify()

    # =========================================================================
    # Public API (same contract as all tabs)
    # =========================================================================

    def save_settings(self):
        """Save timer editor and appearance settings to disk."""
        if hasattr(self, 'timer_editor'):
            self.timer_editor.save_settings()
        save_appearance(self.settings_folder, self.appearance_settings)

    def get_profile_data(self) -> dict:
        """Get cooldown timer + appearance settings for global profile."""
        data = {'timers': self.timer_editor.get_settings().to_dict()}
        data['appearance'] = dict(self.appearance_settings)
        data['appearance']['colors'] = dict(self.appearance_settings['colors'])
        data['appearance']['button_colors'] = dict(self.appearance_settings['button_colors'])
        return data

    def load_profile_data(self, config: dict):
        """Load timer settings from global profile dict."""
        if not config:
            self._update_timer_count()
            return
        timer_data = config.get('timers')
        if timer_data:
            settings = CooldownSettings.from_dict(timer_data)
            self.timer_editor.settings = settings
            self.timer_editor._refresh_timer_list()
            if settings.timers:
                self.timer_editor._select_first_preset_timer()
            else:
                self.timer_editor.selected_timer_index = None
        if 'appearance' in config:
            self.appearance_settings = validate_appearance(config['appearance'])
            save_appearance(self.settings_folder, self.appearance_settings)
            if hasattr(self, 'timer_editor'):
                self.timer_editor.load_appearance(self.appearance_settings)
        self._update_timer_count()

    def set_profile_name(self, name):
        """Update the profile indicator label."""
        self.profile_label.set(name)

    def reset_to_defaults(self):
        """Reset timer editor and appearance to defaults."""
        self.timer_editor.settings = create_default_settings()
        self.timer_editor._refresh_timer_list()
        if self.timer_editor.settings.timers:
            self.timer_editor._select_first_preset_timer()
        else:
            self.timer_editor.selected_timer_index = None
        self.appearance_settings = get_default_appearance()
        save_appearance(self.settings_folder, self.appearance_settings)
        if hasattr(self, 'timer_editor'):
            self.timer_editor.load_appearance(self.appearance_settings)
        self._update_timer_count()

    def cleanup(self):
        """Save all settings on close."""
        if hasattr(self, 'timer_editor'):
            self.timer_editor.save_settings()
        save_appearance(self.settings_folder, self.appearance_settings)
