"""
Stopwatch Tab UI for KzBuilder 3.3.6
Standalone KzStopwatch — thin shell with embedded StopwatchEditorPanel.
Follows TimersTab pattern: tab handles CRUD dialogs, editor owns layout.
"""

import json
import tkinter as tk
from tkinter import ttk, filedialog
from ttkbootstrap.dialogs import Messagebox
from pathlib import Path

from .stopwatch_generator import build_stopwatch
from .stopwatch_settings import (
    get_default_settings as get_default_stopwatch,
    validate_all_settings as validate_stopwatch,
    load_settings as load_stopwatch,
    save_settings as save_stopwatch,
)
from .stopwatch_data import (
    StopwatchPresetSettings,
    MAX_PHASES_PER_PRESET,
    create_default_settings as create_default_presets,
)
from .stopwatch_editor import StopwatchEditorPanel
from .ui_helpers import (
    THEME_COLORS,
    create_tip_bar, create_profile_info_bar,
    BTN_MEDIUM, FONT_SMALL,
)


class StopwatchTab(ttk.Frame):
    """
    Stopwatch tab UI — thin shell with embedded StopwatchEditorPanel.

    Usage:
        tab = StopwatchTab(notebook, settings_folder, game_path_var, assets_path)
        notebook.add(tab, text="Stopwatch")
    """

    def __init__(self, parent, settings_folder, game_path_var=None, assets_path=None):
        super().__init__(parent)
        self.settings_folder = settings_folder
        self.game_path_var = game_path_var
        self._assets_path = assets_path

        self.profile_label = tk.StringVar(value="No profile loaded")
        self.stopwatch_settings = load_stopwatch(settings_folder)

        self._build_ui()

    # =========================================================================
    # UI Construction
    # =========================================================================

    def _build_ui(self):
        """Build the tab UI with button bar, tip bar, profile bar, and editor."""
        # === BUTTON BAR (top) ===
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill='x', padx=10, pady=(5, 5))

        ttk.Button(btn_frame, text="Reset All", command=self._reset_all,
                   width=BTN_MEDIUM).pack(side='left', padx=2)

        self.build_status = ttk.Label(
            btn_frame, text="",
            font=FONT_SMALL, foreground=THEME_COLORS['muted']
        )
        self.build_status.pack(side='left', padx=(10, 0))

        ttk.Button(btn_frame, text="Build", command=self._build,
                   width=BTN_MEDIUM).pack(side='right', padx=2)
        ttk.Button(btn_frame, text="Export...", command=self._export_settings,
                   width=BTN_MEDIUM).pack(side='right', padx=2)
        ttk.Button(btn_frame, text="Import...", command=self._import_settings,
                   width=BTN_MEDIUM).pack(side='right', padx=2)

        # === TIP BAR + INFO BAR ===
        create_tip_bar(self, "Customize KzStopwatch appearance and preset phase sequences.")
        create_profile_info_bar(self, self.profile_label)

        # === EDITOR PANEL ===
        self.editor = StopwatchEditorPanel(
            self, self.settings_folder,
            appearance_settings=self.stopwatch_settings,
            on_appearance_change=self._on_appearance_change,
            on_preset_change=self._on_preset_change,
        )
        self.editor.pack(fill='both', expand=True, padx=10, pady=5)

    # =========================================================================
    # CRUD handlers (called by editor via parent walk)
    # =========================================================================

    def _add_phase(self):
        """Open PhaseEditorDialog to add a new phase."""
        idx = self.editor.selected_preset_index
        if idx >= len(self.editor.preset_settings.presets):
            return
        preset = self.editor.preset_settings.presets[idx]
        if len(preset.phases) >= MAX_PHASES_PER_PRESET:
            Messagebox.show_warning(
                f"Maximum {MAX_PHASES_PER_PRESET} phases per preset reached.",
                title="Limit Reached"
            )
            return

        from .stopwatch_phase_dialog import PhaseEditorDialog
        dialog = PhaseEditorDialog(self)
        self.wait_window(dialog)
        if dialog.result is not None:
            preset.phases.append(dialog.result)
            self.editor._refresh_phase_list()
            self.editor._update_preset_button_styles()
            self.editor._save_and_notify()

    def _edit_phase(self):
        """Open PhaseEditorDialog to edit the selected phase."""
        idx = self.editor.selected_preset_index
        if idx >= len(self.editor.preset_settings.presets):
            return
        preset = self.editor.preset_settings.presets[idx]

        phase_idx = self.editor.get_selected_phase_index()
        if phase_idx is None or phase_idx >= len(preset.phases):
            Messagebox.show_info("Select a phase to edit.", title="Edit Phase")
            return

        from .stopwatch_phase_dialog import PhaseEditorDialog
        dialog = PhaseEditorDialog(self, phase=preset.phases[phase_idx])
        self.wait_window(dialog)
        if dialog.result is not None:
            preset.phases[phase_idx] = dialog.result
            self.editor._refresh_phase_list()
            self.editor._phase_listbox.selection_set(phase_idx)
            self.editor._save_and_notify()

    # =========================================================================
    # Callbacks from editor
    # =========================================================================

    def _on_appearance_change(self, new_settings):
        """Called by editor when appearance controls change."""
        self.stopwatch_settings = new_settings
        save_stopwatch(self.settings_folder, self.stopwatch_settings)

    def _on_preset_change(self):
        """Called by editor when preset data changes."""
        pass

    # =========================================================================
    # Build
    # =========================================================================

    def _build(self):
        """Build the KzStopwatch SWF from current settings."""
        game_path = self.game_path_var.get() if self.game_path_var else ""

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
        stopwatch_path = base_assets / "flash_stopwatch"
        compiler_path = base_assets / "compiler" / "mtasc.exe"
        output_path = Path(game_path) / "Data" / "Gui" / "Default" / "Flash" / "KzStopwatch.swf"

        base_swf = stopwatch_path / "base.swf"
        if not base_swf.exists():
            Messagebox.show_error(
                f"Stopwatch base.swf not found:\n{base_swf}\n\n"
                "Re-download Kaz Flash Modz if this file is missing.",
                title="Missing base.swf"
            )
            return

        if not compiler_path.exists():
            Messagebox.show_error(
                f"MTASC compiler not found:\n{compiler_path}\n\n"
                "Re-download Kaz Flash Modz if this file is missing.",
                title="Compiler Not Found"
            )
            return

        self.build_status.config(text="Building...", foreground=THEME_COLORS['warning'])
        self.update()

        success, message = build_stopwatch(
            str(stopwatch_path),
            str(output_path),
            self.stopwatch_settings,
            str(compiler_path),
            preset_settings=self.editor.get_preset_settings()
        )

        if success:
            self.build_status.config(text="Build successful!", foreground=THEME_COLORS['success'])
            Messagebox.show_info(
                f"{message}\n\nOutput: {output_path}\n\n"
                "In-game, type /reloadui to load the stopwatch.",
                title="Build Complete"
            )
        else:
            self.build_status.config(text="Build failed", foreground=THEME_COLORS['danger'])
            Messagebox.show_error(message, title="Build Failed")

    # =========================================================================
    # Import / Export
    # =========================================================================

    def _export_settings(self):
        """Export stopwatch settings to JSON file."""
        path = filedialog.asksaveasfilename(
            title="Export Stopwatch Profile",
            defaultextension=".json",
            initialfile="Sw_",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if path:
            try:
                data = self.get_profile_data()
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
            except Exception as e:
                Messagebox.show_error(str(e), title="Export Error")

    def _import_settings(self):
        """Import stopwatch settings from JSON file."""
        path = filedialog.askopenfilename(
            title="Import Stopwatch Profile",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if path:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.load_profile_data(data)
            except Exception as e:
                Messagebox.show_error(str(e), title="Import Error")

    def _reset_all(self):
        """Reset all settings to defaults (button handler)."""
        result = Messagebox.yesno(
            "Reset all stopwatch settings to defaults?",
            title="Reset All"
        )
        if result == "Yes":
            self.reset_to_defaults()

    # =========================================================================
    # Public API (same contract as all tabs)
    # =========================================================================

    def save_settings(self):
        """Save stopwatch settings to disk."""
        save_stopwatch(self.settings_folder, self.stopwatch_settings)
        if hasattr(self, 'editor'):
            self.editor.save_preset_settings()

    def get_profile_data(self) -> dict:
        """Get stopwatch settings dict for global profile.

        New format: {"appearance": {...}, "presets": {...}}
        """
        appearance = dict(self.stopwatch_settings)
        appearance["colors"] = dict(self.stopwatch_settings["colors"])
        appearance["button_colors"] = dict(self.stopwatch_settings["button_colors"])
        return {
            "appearance": appearance,
            "presets": self.editor.get_preset_settings().to_dict(),
        }

    def load_profile_data(self, config: dict):
        """Load stopwatch settings from global profile dict."""
        if not config:
            return

        if "appearance" in config:
            self.stopwatch_settings = validate_stopwatch(config["appearance"])
            save_stopwatch(self.settings_folder, self.stopwatch_settings)
            if hasattr(self, 'editor'):
                self.editor.load_appearance(self.stopwatch_settings)
            if "presets" in config:
                preset_data = config["presets"]
                if hasattr(self, 'editor'):
                    self.editor.load_preset_data(preset_data)
                    self.editor.save_preset_settings()

    def get_preset_settings(self) -> StopwatchPresetSettings:
        """Get preset settings for the generator."""
        if hasattr(self, 'editor'):
            return self.editor.get_preset_settings()
        return create_default_presets()

    def set_profile_name(self, name):
        """Update profile indicator label."""
        self.profile_label.set(name)

    def reset_to_defaults(self):
        """Reset stopwatch to defaults."""
        self.stopwatch_settings = get_default_stopwatch()
        save_stopwatch(self.settings_folder, self.stopwatch_settings)
        if hasattr(self, 'editor'):
            self.editor.load_appearance(self.stopwatch_settings)
            self.editor.preset_settings = create_default_presets()
            self.editor.save_preset_settings()
            self.editor._select_preset(0)

    def cleanup(self):
        """Save settings on close."""
        save_stopwatch(self.settings_folder, self.stopwatch_settings)
        if hasattr(self, 'editor'):
            self.editor.save_preset_settings()
