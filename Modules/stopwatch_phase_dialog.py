"""
Stopwatch Phase Editor Dialog for KzBuilder 3.3.5

Modal dialog for adding/editing a single stopwatch phase.
Follows the TimerEditorDialog pattern: withdraw → build → restore position → deiconify.
"""

import tkinter as tk
from tkinter import ttk
from ttkbootstrap.dialogs import Messagebox

from .ui_helpers import (
    THEME_COLORS, FONT_SUBTITLE, FONT_SMALL, FONT_FORM_LABEL,
    apply_dark_titlebar, restore_window_position, bind_window_position_save,
    add_tooltip, ColorSwatch,
)
from .stopwatch_data import (
    StopwatchPhase, COLOR_GREEN, COLOR_YELLOW, COLOR_RED, COLOR_DEFAULT,
    validate_color,
)

DIALOG_SIZE = (400, 250)


class PhaseEditorDialog(tk.Toplevel):
    """
    Modal dialog for adding or editing a single StopwatchPhase.

    Usage:
        dialog = PhaseEditorDialog(parent, phase=phase_or_None)
        parent.wait_window(dialog)
        if dialog.result is not None:
            # dialog.result is a StopwatchPhase
    """

    def __init__(self, parent, phase=None):
        """
        Args:
            parent: Parent widget
            phase: StopwatchPhase to edit (None = add mode)
        """
        super().__init__(parent)
        self.withdraw()
        apply_dark_titlebar(self)

        self._edit_mode = phase is not None
        self.title("Edit Phase" if self._edit_mode else "Add Phase")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._phase = phase
        self.result = None

        self._create_widgets()
        if self._edit_mode:
            self._load_phase(phase)

        app_window = parent.winfo_toplevel()
        restore_window_position(self, 'phase_editor_dialog', *DIALOG_SIZE,
                                app_window, resizable=False)
        bind_window_position_save(self, 'phase_editor_dialog', save_size=False)
        self.update_idletasks()
        self.deiconify()

    def _create_widgets(self):
        """Build the dialog form."""
        frame = ttk.Frame(self, padding=12)
        frame.pack(fill='both', expand=True)

        # Header
        title_text = "Edit Phase" if self._edit_mode else "Create New Phase"
        ttk.Label(frame, text=title_text, font=FONT_SUBTITLE).pack(pady=(0, 8))

        # Phase Name
        name_frame = ttk.Frame(frame)
        name_frame.pack(fill='x', pady=3)
        ttk.Label(name_frame, text="Name:", font=FONT_FORM_LABEL, width=10).pack(side='left')
        self._name_var = tk.StringVar(value="New Phase" if not self._edit_mode else "")
        ttk.Entry(name_frame, textvariable=self._name_var, width=25).pack(
            side='left', padx=5, fill='x', expand=True)

        # Duration
        dur_frame = ttk.Frame(frame)
        dur_frame.pack(fill='x', pady=3)
        ttk.Label(dur_frame, text="Duration:", font=FONT_FORM_LABEL, width=10).pack(side='left')
        self._duration_var = tk.StringVar(value="10")
        ttk.Entry(dur_frame, textvariable=self._duration_var, width=8).pack(
            side='left', padx=5)
        ttk.Label(dur_frame, text="seconds", font=FONT_SMALL,
                  foreground=THEME_COLORS['muted']).pack(side='left')

        # Color
        color_frame = ttk.Frame(frame)
        color_frame.pack(fill='x', pady=3)
        ttk.Label(color_frame, text="Color:", font=FONT_FORM_LABEL, width=10).pack(side='left')
        self._color_var = tk.StringVar(value=COLOR_GREEN)
        self._color_swatch = ColorSwatch(
            color_frame, color_var=self._color_var,
            on_change=lambda c: self._color_var.set(c.lstrip('#')))
        self._color_swatch.pack(side='left', padx=(5, 6))

        # Quick-pick color swatches
        for color, name in [(COLOR_GREEN, "Green"), (COLOR_YELLOW, "Yellow"),
                            (COLOR_RED, "Red"), (COLOR_DEFAULT, "Gray")]:
            swatch = tk.Canvas(color_frame, width=22, height=18,
                               highlightthickness=1,
                               highlightbackground='#444444', cursor='hand2')
            swatch.configure(bg=f"#{color}")
            swatch.pack(side='left', padx=2)
            swatch.bind('<Button-1>', lambda e, c=color: self._color_var.set(c))
            swatch.bind('<Enter>', lambda e, w=swatch: w.configure(
                highlightbackground='#888888'))
            swatch.bind('<Leave>', lambda e, w=swatch: w.configure(
                highlightbackground='#444444'))
            add_tooltip(swatch, name)

        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)
        ok_text = "Save" if self._edit_mode else "Create"
        ttk.Button(btn_frame, text=ok_text, command=self._on_ok,
                   width=10).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self._on_cancel,
                   width=10).pack(side='left', padx=5)

    def _load_phase(self, phase):
        """Pre-populate fields from an existing phase (edit mode)."""
        self._name_var.set(phase.name)
        self._duration_var.set(str(phase.duration))
        self._color_var.set(phase.color)

    def _on_ok(self):
        """Validate and return the phase."""
        name = self._name_var.get().strip()
        if not name:
            Messagebox.show_warning("Phase name is required.", title="Validation",
                                    parent=self)
            return

        dur_text = self._duration_var.get().strip()
        try:
            duration = float(dur_text)
        except ValueError:
            duration = -1
        if duration <= 0:
            Messagebox.show_warning("Duration must be a positive number.",
                                    title="Validation", parent=self)
            return

        color = self._color_var.get().strip()
        if not validate_color(color):
            Messagebox.show_warning("Invalid color. Use 6-character hex (e.g. FF0000).",
                                    title="Validation", parent=self)
            return

        self.result = StopwatchPhase(
            name=name,
            duration=duration,
            color=color,
        )
        self.destroy()

    def _on_cancel(self):
        """Cancel the dialog."""
        self.result = None
        self.destroy()
