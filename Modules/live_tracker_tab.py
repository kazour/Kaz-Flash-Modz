"""
Live Tracker Tab Module for KzBuilder 3.3.6
Ethram-Fal seed timer overlay, combat log monitoring, and overlay controls.
Extracted from timers_tab.py in v3.1.0.
"""

import logging
import tkinter as tk
from tkinter import ttk
from ttkbootstrap.dialogs import Messagebox
from pathlib import Path

logger = logging.getLogger(__name__)

from .live_tracker_settings import (
    load_settings, save_settings, get_default_settings, validate_all_settings,
)
from .boss_timer import BossTimer
from .combat_monitor import CombatLogMonitor
from .timer_overlay import TimerOverlay
from .ui_helpers import (
    THEME_COLORS, FONT_SMALL, FONT_SMALL_BOLD,
    create_tip_bar, create_profile_info_bar, BTN_SMALL, BTN_MEDIUM, add_tooltip,
)


class LiveTrackerTab(ttk.Frame):
    """
    Live Tracker tab UI for KzBuilder.

    Integrates:
    - Ethram-Fal seed timer overlay
    - Combat log monitoring
    - Overlay controls (lock, transparency, opacity, font)

    Usage:
        tab = LiveTrackerTab(notebook, settings_manager)
        notebook.add(tab, text="Live Tracker")
        # On close:
        tab.cleanup()
    """

    def __init__(self, parent, settings_manager, assets_path=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self._assets_path = assets_path

        # Info bar label
        self.profile_label = tk.StringVar(value="No profile loaded")

        # Get settings folder path from settings manager filepath
        self.settings_folder = str(Path(settings_manager.filepath).parent)

        # Load timer-specific settings (overlay position, opacity, etc.)
        self.timer_settings = load_settings(self.settings_folder)

        # Create components (overlay first so we can wire callback)
        self.overlay = None
        self.boss_timer = None
        self.combat_monitor = None
        self._game_loop_id = None

        # Build UI
        self._build_ui()

        # Create overlay (hidden until user clicks Show)
        self._create_overlay()

        # Wire up components
        self.boss_timer = BossTimer(update_callback=self.overlay.update_display)
        self.combat_monitor = CombatLogMonitor(self.boss_timer)

        # Auto-detect log path from game_path setting
        self._update_log_path()

    def _build_ui(self):
        """Build the tab UI."""
        create_tip_bar(self, "Boss timer reads combat logs. Monitor seed cycles and track boss encounters live.")

        create_profile_info_bar(self, self.profile_label)

        # Main panel
        main_frame = ttk.Frame(self)
        main_frame.pack(fill='both', expand=True, padx=10, pady=5)

        left_panel = ttk.Frame(main_frame)
        left_panel.pack(side='left', fill='y', padx=(0, 10))

        self._build_seed_timer_section(left_panel)
        self._build_overlay_controls(left_panel)

    def _build_seed_timer_section(self, parent):
        """Build seed timer monitoring controls with status display."""
        seed_frame = ttk.LabelFrame(parent, text="Seed Timer Controls")
        seed_frame.configure(padding=8)
        seed_frame.pack(fill='x', pady=(0, 5))

        monitor_frame = ttk.Frame(seed_frame)
        monitor_frame.pack(fill='x', pady=(0, 4))

        self.start_btn = ttk.Button(
            monitor_frame, text="Start Monitoring",
            command=self._start_monitoring, width=BTN_MEDIUM
        )
        self.start_btn.pack(side='left', padx=(0, 5))

        self.stop_btn = ttk.Button(
            monitor_frame, text="Stop",
            command=self._stop_monitoring, width=BTN_SMALL,
            state='disabled'
        )
        self.stop_btn.pack(side='left')

        # Status
        status_frame = ttk.Frame(seed_frame)
        status_frame.pack(fill='x', pady=(4, 0))
        ttk.Label(status_frame, text="Monitor:",
                  font=FONT_SMALL, foreground=THEME_COLORS['body']).pack(side='left')
        self.status_label = ttk.Label(status_frame, text="Stopped",
                  font=FONT_SMALL_BOLD, foreground=THEME_COLORS['muted'])
        self.status_label.pack(side='left', padx=(4, 0))

        self.log_status_label = ttk.Label(seed_frame, text="No game path set",
                  font=FONT_SMALL, foreground=THEME_COLORS['muted'])
        self.log_status_label.pack(anchor='w', pady=(2, 0))

    def _build_overlay_controls(self, parent):
        """Build overlay settings (show/lock/test, transparency, opacity, font)."""
        overlay_frame = ttk.LabelFrame(parent, text="Overlay")
        overlay_frame.configure(padding=8)
        overlay_frame.pack(fill='x', pady=(0, 5))

        # Row 1: Show/Lock/Test
        btn_row = ttk.Frame(overlay_frame)
        btn_row.pack(fill='x', pady=(0, 6))

        self.visibility_btn = ttk.Button(
            btn_row, text="Show", command=self._toggle_overlay, width=BTN_SMALL
        )
        self.visibility_btn.pack(side='left', padx=(0, 4))

        self.lock_btn = ttk.Button(
            btn_row, text="Lock", command=self._toggle_lock, width=BTN_SMALL
        )
        self.lock_btn.pack(side='left', padx=(0, 4))

        self.test_btn = ttk.Button(
            btn_row, text="Test Cycle", command=self._toggle_test, width=BTN_MEDIUM
        )
        self.test_btn.pack(side='left')

        # Row 2: Transparent checkbox
        self.transparent_var = tk.BooleanVar(value=self.timer_settings.get('transparent_bg', False))
        self.transparent_cb = ttk.Checkbutton(
            overlay_frame, text="Transparent background",
            variable=self.transparent_var,
            command=self._toggle_transparent,
            bootstyle="success-round-toggle"
        )
        self.transparent_cb.pack(anchor='w', pady=(0, 6))
        add_tooltip(self.transparent_cb, "Make overlay background transparent (click-through when locked)")

        # Row 3: Opacity
        opacity_row = ttk.Frame(overlay_frame)
        opacity_row.pack(fill='x', pady=(0, 4))

        ttk.Label(opacity_row, text="Opacity:",
                  font=FONT_SMALL).pack(side='left')
        self.opacity_var = tk.DoubleVar(value=self.timer_settings.get('opacity', 0.9))
        self.opacity_slider = ttk.Scale(
            opacity_row, from_=0.3, to=1.0,
            variable=self.opacity_var,
            orient='horizontal', length=120,
            command=self._on_opacity_change
        )
        self.opacity_slider.pack(side='left', padx=(5, 0), fill='x', expand=True)
        add_tooltip(self.opacity_slider, "Overlay window transparency (30% to 100%)")

        # Row 4: Font size
        font_row = ttk.Frame(overlay_frame)
        font_row.pack(fill='x')

        ttk.Label(font_row, text="Font size:",
                  font=FONT_SMALL).pack(side='left')
        self.font_var = tk.IntVar(value=self.timer_settings.get('font_size', 11))
        self.font_slider = ttk.Scale(
            font_row, from_=8, to=20,
            variable=self.font_var,
            orient='horizontal', length=120,
            command=self._on_font_change
        )
        self.font_slider.pack(side='left', padx=(5, 0), fill='x', expand=True)
        add_tooltip(self.font_slider, "Timer text size in the overlay (8-20 pt)")

    def _create_overlay(self):
        """Create the overlay window."""
        root = self.winfo_toplevel()

        self.overlay = TimerOverlay(
            root,
            self.timer_settings,
            on_settings_changed=self.save_settings
        )

        # Update UI to match overlay state
        if self.overlay.is_visible:
            self.visibility_btn.config(text="Hide")
        else:
            self.visibility_btn.config(text="Show")

        if self.overlay.is_locked:
            self.lock_btn.config(text="Unlock")
        else:
            self.lock_btn.config(text="Lock")

    def _update_log_path(self):
        """Update combat log path from game_path setting."""
        game_path = self.settings_manager.get("game_path", "")

        if not game_path:
            self.log_status_label.config(
                text="Set game path on the Welcome screen first",
                foreground=THEME_COLORS['warning']
            )
            return

        log_folder = game_path

        if not Path(log_folder).exists():
            self.log_status_label.config(
                text=f"Game folder not found: {log_folder}",
                foreground=THEME_COLORS['danger']
            )
            return

        # Find latest log
        latest = self.combat_monitor.set_log_folder(log_folder) if self.combat_monitor else None

        if latest:
            filename = Path(latest).name
            self.log_status_label.config(
                text=f"Found: {filename}",
                foreground=THEME_COLORS['success']
            )
        else:
            self.log_status_label.config(
                text="No combat logs found. Type /logcombat on in game.",
                foreground=THEME_COLORS['warning']
            )

    def _start_monitoring(self):
        """Start combat log monitoring."""
        self._update_log_path()

        if not self.combat_monitor.log_path:
            Messagebox.show_error(
                "No combat log found.\n\n"
                "1. Set game path on the Welcome screen\n"
                "2. In-game, type: /logcombat on",
                title="Error"
            )
            return

        if self.combat_monitor.start_monitoring():
            self.status_label.config(text="Running", foreground=THEME_COLORS['success'])
            self.start_btn.config(state='disabled')
            self.stop_btn.config(state='normal')
            self._start_game_loop()
        else:
            Messagebox.show_error("Failed to start monitoring", title="Error")

    def _stop_monitoring(self):
        """Stop combat log monitoring."""
        self.combat_monitor.stop_monitoring()
        self.boss_timer.stop_cycle()

        self._stop_game_loop()

        self.status_label.config(text="Stopped", foreground=THEME_COLORS['muted'])
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')

        self._update_log_path()

    def _start_game_loop(self):
        """Start the 50ms update loop."""
        def loop():
            try:
                self.boss_timer.update_display()
            except Exception as e:
                logger.error("Timer loop error: %s", e)
            finally:
                self._game_loop_id = self.after(50, loop)

        self._game_loop_id = self.after(50, loop)

    def _stop_game_loop(self):
        """Stop the update loop."""
        if self._game_loop_id:
            self.after_cancel(self._game_loop_id)
            self._game_loop_id = None

    def _toggle_overlay(self):
        """Toggle overlay visibility."""
        if self.overlay.is_visible:
            self.overlay.hide()
            self.visibility_btn.config(text="Show")
        else:
            self.overlay.show()
            self.visibility_btn.config(text="Hide")

    def _toggle_lock(self):
        """Toggle overlay lock state."""
        self.overlay.toggle_lock()
        if self.overlay.is_locked:
            self.lock_btn.config(text="Unlock")
        else:
            self.lock_btn.config(text="Lock")

    def _toggle_transparent(self):
        """Toggle transparent background."""
        self.overlay.set_transparent(self.transparent_var.get())

    def _on_opacity_change(self, value):
        """Handle opacity slider change."""
        self.overlay.set_opacity(float(value))

    def _on_font_change(self, value):
        """Handle font size slider change."""
        self.overlay.set_font_size(int(float(value)))

    def _toggle_test(self):
        """Toggle test mode (simulate a seed cycle)."""
        if self.boss_timer.timer_active:
            self.boss_timer.stop_cycle()
            self.test_btn.config(text="Test Cycle")
            self._stop_game_loop()
        else:
            self.boss_timer.start_cycle("TestPlayer")
            self.test_btn.config(text="Stop")
            self._start_game_loop()

            def trigger_fixation():
                if self.boss_timer.timer_active:
                    self.boss_timer.update_fixation("FixPlayer")

            def check_reset():
                if not self.boss_timer.timer_active:
                    self.test_btn.config(text="Test Cycle")
                    self._stop_game_loop()
                else:
                    self.after(500, check_reset)

            self.after(4000, trigger_fixation)
            self.after(39500, check_reset)

    # =========================================================================
    # Public API (same contract as all tabs)
    # =========================================================================

    def save_settings(self):
        """Save current overlay settings to disk."""
        if self.overlay:
            settings = self.overlay.get_settings()
            if not save_settings(self.settings_folder, settings):
                Messagebox.show_error("Failed to save timer overlay settings.", title="Save Error")

    def get_profile_data(self) -> dict:
        """Get overlay settings dict for embedding in a global profile."""
        overlay = self.overlay.get_settings() if self.overlay else dict(self.timer_settings)
        return {'overlay': overlay}

    def load_profile_data(self, config: dict):
        """Load live tracker settings from a global profile dict."""
        if not config:
            return
        if 'overlay' in config:
            self.timer_settings = validate_all_settings(config['overlay'])
            if self.overlay:
                self.overlay.apply_settings(self.timer_settings)
            self._sync_overlay_ui()

    def set_profile_name(self, name):
        """Update the profile indicator label."""
        self.profile_label.set(name)

    def reset_to_defaults(self):
        """Reset all live tracker settings to defaults."""
        self.timer_settings = get_default_settings()
        if self.overlay:
            self.overlay.apply_settings(self.timer_settings)
        self._sync_overlay_ui()

    def _sync_overlay_ui(self):
        """Sync overlay control widgets to current timer_settings."""
        self.transparent_var.set(self.timer_settings.get('transparent_bg', False))
        self.opacity_var.set(self.timer_settings.get('opacity', 0.9))
        self.font_var.set(self.timer_settings.get('font_size', 11))
        if self.overlay:
            self.lock_btn.config(text="Unlock" if self.overlay.is_locked else "Lock")
            self.visibility_btn.config(text="Hide" if self.overlay.is_visible else "Show")

    def cleanup(self):
        """Clean up resources when tab/app is closing."""
        if self.combat_monitor:
            self.combat_monitor.stop_monitoring()

        self._stop_game_loop()

        self.save_settings()

        if self.overlay:
            self.overlay.destroy()

    def refresh_log_path(self):
        """Refresh the combat log path (call when game_path changes)."""
        if self.combat_monitor:
            self._update_log_path()
