"""
Timer Editor Dialog for KzBuilder 3.3.6

Modal dialog for adding/editing a single cooldown timer.
Follows the AddGridWizard pattern: withdraw → build → restore position → deiconify.
"""

import tkinter as tk
from tkinter import ttk
from ttkbootstrap.dialogs import Messagebox

from .ui_helpers import (
    THEME_COLORS, FONT_SUBTITLE, FONT_SMALL,
    apply_dark_titlebar, restore_window_position, bind_window_position_save,
    add_tooltip, ColorSwatch,
)
from .timers_data import (
    CooldownTimer, TriggerType, BarDirection, CountDirection, RetriggerMode,
    COLOR_DEFAULT, COLOR_WARNING, COLOR_ALERT, COLOR_ACTIVE,
    generate_timer_id, parse_duration_input,
)

# Trigger type display labels
TRIGGER_LABELS = {
    TriggerType.BUFF_ADD.value: "Buff Applied",
    TriggerType.BUFF_REMOVE.value: "Buff Removed",
    TriggerType.CAST_SUCCESS.value: "Cast Success",
}
TRIGGER_LABEL_TO_VALUE = {v: k for k, v in TRIGGER_LABELS.items()}

DIALOG_SIZE = (460, 600)


class TimerEditorDialog(tk.Toplevel):
    """
    Modal dialog for adding or editing a single CooldownTimer.

    Usage:
        dialog = TimerEditorDialog(parent, database=db,
                                    existing_ids=ids, timer=timer_or_None)
        parent.wait_window(dialog)
        if dialog.result is not None:
            # dialog.result is a CooldownTimer
    """

    def __init__(self, parent, database=None, existing_ids=None,
                 timer=None):
        """
        Args:
            parent: Parent widget
            database: BuffDatabase instance for Browse button
            existing_ids: List of existing timer IDs (to prevent duplicates)
            timer: CooldownTimer to edit (None = add mode)
        """
        super().__init__(parent)
        self.withdraw()
        apply_dark_titlebar(self)

        self._edit_mode = timer is not None
        self.title("Edit Timer" if self._edit_mode else "Add Timer")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.database = database
        self.existing_ids = list(existing_ids or [])
        self._timer = timer
        self.result = None

        self._create_widgets()
        if self._edit_mode:
            self._load_timer(timer)

        # Center on app window (toplevel), not the frame widget
        app_window = parent.winfo_toplevel()
        restore_window_position(self, 'timer_editor_dialog', *DIALOG_SIZE,
                                app_window, resizable=False)
        bind_window_position_save(self, 'timer_editor_dialog', save_size=False)
        self.update_idletasks()
        self.deiconify()

    def _create_widgets(self):
        """Build the dialog form with organized LabelFrame sections."""
        frame = ttk.Frame(self, padding=12)
        frame.pack(fill='both', expand=True)

        # Header
        title_text = "Edit Timer" if self._edit_mode else "Create New Timer"
        ttk.Label(frame, text=title_text, font=FONT_SUBTITLE).pack(pady=(0, 8))

        # Timer Name
        name_frame = ttk.Frame(frame)
        name_frame.pack(fill='x', pady=3)
        ttk.Label(name_frame, text="Timer Name:").pack(side='left')
        self._name_var = tk.StringVar(value="New Timer" if not self._edit_mode else "")
        ttk.Entry(name_frame, textvariable=self._name_var, width=25).pack(
            side='left', padx=5, fill='x', expand=True)

        # === TRIGGER SECTION ===
        trigger_lf = ttk.LabelFrame(frame, text="Trigger")
        trigger_lf.configure(padding=5)
        trigger_lf.pack(fill='x', pady=5)

        type_row = ttk.Frame(trigger_lf)
        type_row.pack(fill='x')
        ttk.Label(type_row, text="Type:").pack(side='left')
        self._trigger_display_var = tk.StringVar(
            value=TRIGGER_LABELS[TriggerType.BUFF_ADD.value])
        trigger_combo = ttk.Combobox(
            type_row, textvariable=self._trigger_display_var,
            values=list(TRIGGER_LABELS.values()), state='readonly', width=18)
        trigger_combo.pack(side='left', padx=5)
        trigger_combo.bind("<<ComboboxSelected>>", self._on_trigger_type_change)

        self._trigger_desc = ttk.Label(trigger_lf, text="", font=FONT_SMALL,
                                       foreground=THEME_COLORS['muted'])
        self._trigger_desc.pack(anchor='w', pady=(0, 2))

        ttk.Separator(trigger_lf, orient='horizontal').pack(fill='x', pady=(2, 6))

        # Source
        source_row = ttk.Frame(trigger_lf)
        source_row.pack(fill='x')
        ttk.Label(source_row, text="Source:").pack(side='left')
        self._source_var = tk.StringVar(value="player")
        ttk.Radiobutton(source_row, text="Player", value="player",
                        variable=self._source_var).pack(side='left', padx=(8, 0))
        ttk.Radiobutton(source_row, text="Target", value="target",
                        variable=self._source_var).pack(side='left', padx=(8, 0))

        # Conditional fields container
        self._trigger_fields_frame = ttk.Frame(trigger_lf)
        self._trigger_fields_frame.pack(fill='x')

        # Buff ID row (conditional — shown for buff triggers)
        self._buff_row_frame = ttk.Frame(self._trigger_fields_frame)
        ttk.Label(self._buff_row_frame, text="Buff ID:").pack(side='left')
        self._buff_id_var = tk.StringVar()
        self._buff_id_entry = ttk.Entry(self._buff_row_frame,
                                        textvariable=self._buff_id_var, width=10)
        self._buff_id_entry.pack(side='left', padx=5)
        self._buff_browse_btn = ttk.Button(self._buff_row_frame, text="Browse...",
                                           command=self._browse_buff,
                                           bootstyle="outline-secondary")
        if self.database:
            self._buff_browse_btn.pack(side='left')

        # Buff name display (conditional)
        self._buff_name_frame = ttk.Frame(self._trigger_fields_frame)
        self._buff_name_label = ttk.Label(self._buff_name_frame, text="",
                                          font=FONT_SMALL,
                                          foreground=THEME_COLORS['muted'])
        self._buff_name_label.pack(anchor='w', padx=5)

        # Spell name row (conditional — shown for cast triggers)
        self._spell_row_frame = ttk.Frame(self._trigger_fields_frame)
        ttk.Label(self._spell_row_frame, text="Spell Name:").pack(side='left')
        self._spell_var = tk.StringVar()
        self._spell_entry = ttk.Entry(self._spell_row_frame,
                                      textvariable=self._spell_var, width=25)
        self._spell_entry.pack(side='left', padx=5, fill='x', expand=True)

        # === TIMING SECTION ===
        timing_lf = ttk.LabelFrame(frame, text="Timing")
        timing_lf.configure(padding=5)
        timing_lf.pack(fill='x', pady=5)

        dur_row = ttk.Frame(timing_lf)
        dur_row.pack(fill='x')
        ttk.Label(dur_row, text="Duration:").pack(side='left')
        self._duration_var = tk.StringVar(value="10")
        ttk.Entry(dur_row, textvariable=self._duration_var, width=8).pack(
            side='left', padx=5)
        ttk.Label(dur_row, text="seconds", font=FONT_SMALL,
                  foreground=THEME_COLORS['muted']).pack(side='left')
        add_tooltip(dur_row, "Cooldown duration (e.g. 40, 1m30s, 5000ms)")

        warn_row = ttk.Frame(timing_lf)
        warn_row.pack(fill='x', pady=(3, 0))
        ttk.Label(warn_row, text="Warning at:").pack(side='left')
        self._warning_var = tk.StringVar(value="3")
        ttk.Entry(warn_row, textvariable=self._warning_var, width=8).pack(
            side='left', padx=5)
        ttk.Label(warn_row, text="sec remaining", font=FONT_SMALL,
                  foreground=THEME_COLORS['muted']).pack(side='left')

        # === APPEARANCE SECTION ===
        appear_lf = ttk.LabelFrame(frame, text="Appearance")
        appear_lf.configure(padding=5)
        appear_lf.pack(fill='x', pady=5)

        bc_row = ttk.Frame(appear_lf)
        bc_row.pack(fill='x')
        ttk.Label(bc_row, text="Bar Color:").pack(side='left')
        self._bar_color_var = tk.StringVar(value=COLOR_ACTIVE)
        self._bar_color_swatch = ColorSwatch(
            bc_row, color_var=self._bar_color_var,
            on_change=lambda c: self._bar_color_var.set(c.lstrip('#')))
        self._bar_color_swatch.pack(side='left', padx=(5, 6))
        for color, name in [(COLOR_ACTIVE, "Green"), (COLOR_WARNING, "Yellow"),
                            (COLOR_ALERT, "Red"), (COLOR_DEFAULT, "Gray")]:
            swatch = tk.Canvas(bc_row, width=22, height=18,
                               highlightthickness=1,
                               highlightbackground='#444444', cursor='hand2')
            swatch.configure(bg=f"#{color}")
            swatch.pack(side='left', padx=2)
            swatch.bind('<Button-1>', lambda e, c=color: self._bar_color_var.set(c))
            swatch.bind('<Enter>', lambda e, w=swatch: w.configure(
                highlightbackground='#888888'))
            swatch.bind('<Leave>', lambda e, w=swatch: w.configure(
                highlightbackground='#444444'))
            add_tooltip(swatch, name)

        wc_row = ttk.Frame(appear_lf)
        wc_row.pack(fill='x', pady=(3, 0))
        ttk.Label(wc_row, text="Warning Color:").pack(side='left')
        self._warn_color_var = tk.StringVar(value=COLOR_ALERT)
        self._warn_color_swatch = ColorSwatch(
            wc_row, color_var=self._warn_color_var,
            on_change=lambda c: self._warn_color_var.set(c.lstrip('#')))
        self._warn_color_swatch.pack(side='left', padx=(5, 0))

        # === BEHAVIOR SECTION ===
        behavior_lf = ttk.LabelFrame(frame, text="Behavior")
        behavior_lf.configure(padding=5)
        behavior_lf.pack(fill='x', pady=5)

        style_row = ttk.Frame(behavior_lf)
        style_row.pack(fill='x')
        ttk.Label(style_row, text="Bar Style:").pack(side='left')
        self._direction_var = tk.StringVar(value=BarDirection.EMPTY.value)
        ttk.Radiobutton(style_row, text="Drain (full\u2192empty)", value="empty",
                        variable=self._direction_var).pack(side='left', padx=(8, 0))
        ttk.Radiobutton(style_row, text="Fill (empty\u2192full)", value="fill",
                        variable=self._direction_var).pack(side='left', padx=(8, 0))

        count_row = ttk.Frame(behavior_lf)
        count_row.pack(fill='x', pady=(3, 0))
        ttk.Label(count_row, text="Count:").pack(side='left')
        self._count_dir_var = tk.StringVar(value=CountDirection.DESCENDING.value)
        ttk.Radiobutton(count_row, text="Descending (N\u21920)", value="descending",
                        variable=self._count_dir_var).pack(side='left', padx=(8, 0))
        ttk.Radiobutton(count_row, text="Ascending (0\u2192N)", value="ascending",
                        variable=self._count_dir_var).pack(side='left', padx=(8, 0))

        retrig_row = ttk.Frame(behavior_lf)
        retrig_row.pack(fill='x', pady=(3, 0))
        ttk.Label(retrig_row, text="Retrigger:").pack(side='left')
        self._retrigger_var = tk.StringVar(value=RetriggerMode.RESTART.value)
        ttk.Radiobutton(retrig_row, text="Restart timer", value="restart",
                        variable=self._retrigger_var).pack(side='left', padx=(8, 0))
        ttk.Radiobutton(retrig_row, text="Ignore", value="ignore",
                        variable=self._retrigger_var).pack(side='left', padx=(8, 0))

        # === BUTTONS ===
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)
        ok_text = "Save" if self._edit_mode else "Create"
        ttk.Button(btn_frame, text=ok_text, command=self._on_ok,
                   width=10).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self._on_cancel,
                   width=10).pack(side='left', padx=5)

        # Initial trigger field visibility
        self._update_trigger_fields()

    def _load_timer(self, timer):
        """Pre-populate fields from an existing timer (edit mode)."""
        self._name_var.set(timer.name)
        self._trigger_display_var.set(
            TRIGGER_LABELS.get(timer.trigger_type, timer.trigger_type))
        self._source_var.set(timer.trigger_source)
        self._buff_id_var.set(
            str(timer.trigger_buff_id) if timer.trigger_buff_id is not None else "")
        self._buff_name_label.config(text=timer.trigger_buff_name or "")
        self._spell_var.set(timer.trigger_spell_name or "")
        self._duration_var.set(str(timer.duration))
        self._warning_var.set(str(timer.warning_threshold))
        self._bar_color_var.set(timer.bar_color)
        self._warn_color_var.set(timer.warning_color)
        self._direction_var.set(timer.bar_direction)
        self._count_dir_var.set(timer.count_direction)
        self._retrigger_var.set(timer.retrigger)

        self._update_trigger_fields()

    # =========================================================================
    # Trigger field visibility
    # =========================================================================

    def _on_trigger_type_change(self, event=None):
        """Handle trigger type combobox change."""
        self._update_trigger_fields()

    def _update_trigger_fields(self):
        """Show/hide trigger-specific fields based on selected type."""
        display = self._trigger_display_var.get()
        trigger_type = TRIGGER_LABEL_TO_VALUE.get(display, TriggerType.BUFF_ADD.value)

        desc_map = {
            TriggerType.BUFF_ADD.value: "Timer starts when this buff/debuff is applied",
            TriggerType.BUFF_REMOVE.value: "Timer starts when this buff/debuff is removed",
            TriggerType.CAST_SUCCESS.value: "Timer starts when this spell finishes casting",
        }
        self._trigger_desc.config(text=desc_map.get(trigger_type, ""))

        # Hide all conditional fields
        self._buff_row_frame.pack_forget()
        self._buff_name_frame.pack_forget()
        self._spell_row_frame.pack_forget()

        if trigger_type in (TriggerType.BUFF_ADD.value, TriggerType.BUFF_REMOVE.value):
            self._buff_row_frame.pack(fill='x', pady=(4, 0))
            if self._buff_name_label.cget('text'):
                self._buff_name_frame.pack(fill='x')
        elif trigger_type == TriggerType.CAST_SUCCESS.value:
            self._spell_row_frame.pack(fill='x', pady=(4, 0))

    def _browse_buff(self):
        """Open buff database picker."""
        if not self.database:
            return
        from .grids_tab import BuffSelectorDialog
        dialog = BuffSelectorDialog(self, self.database)
        self.wait_window(dialog)
        if hasattr(dialog, 'result') and dialog.result:
            buff_ids = dialog.result
            if buff_ids:
                buff_id = buff_ids[0]
                buff_name = self.database.get_name(buff_id) or "Unknown Buff"
                self._buff_id_var.set(str(buff_id))
                self._buff_name_label.config(text=buff_name)
                self._buff_name_frame.pack(fill='x')

    # =========================================================================
    # OK / Cancel
    # =========================================================================

    def _on_ok(self):
        """Validate and return the timer."""
        name = self._name_var.get().strip()
        if not name:
            Messagebox.show_warning("Timer name is required.", title="Validation",
                                    parent=self)
            return

        display = self._trigger_display_var.get()
        trigger_type = TRIGGER_LABEL_TO_VALUE.get(display, TriggerType.BUFF_ADD.value)

        # Parse duration
        dur_text = self._duration_var.get().strip()
        duration = parse_duration_input(dur_text)
        if duration is None or duration <= 0:
            Messagebox.show_warning("Duration must be a positive number.",
                                    title="Validation", parent=self)
            return

        # Parse warning
        warn_text = self._warning_var.get().strip()
        warning = parse_duration_input(warn_text)
        if warning is None or warning < 0:
            warning = 0.0

        # Buff ID validation for buff triggers
        buff_id = None
        if trigger_type in (TriggerType.BUFF_ADD.value, TriggerType.BUFF_REMOVE.value):
            buff_str = self._buff_id_var.get().strip()
            if buff_str and buff_str.isdigit():
                buff_id = int(buff_str)
            if buff_id is None:
                Messagebox.show_warning("Buff ID is required for buff triggers.",
                                        title="Validation", parent=self)
                return

        spell_name = self._spell_var.get().strip() or None
        if trigger_type == TriggerType.CAST_SUCCESS.value and not spell_name:
            Messagebox.show_warning("Spell name is required for Cast Success trigger.",
                                    title="Validation", parent=self)
            return

        # Generate or reuse timer ID
        if self._edit_mode:
            timer_id = self._timer.id
        else:
            timer_id = generate_timer_id(name, self.existing_ids)

        bar_color = self._bar_color_var.get()
        warn_color = self._warn_color_var.get()

        self.result = CooldownTimer(
            id=timer_id,
            name=name,
            enabled=True,
            trigger_type=trigger_type,
            trigger_source=self._source_var.get(),
            trigger_buff_id=buff_id,
            trigger_buff_name=self._buff_name_label.cget('text') or None,
            trigger_spell_name=spell_name,
            duration=duration,
            warning_threshold=warning,
            bar_color=bar_color,
            warning_color=warn_color,
            bar_direction=self._direction_var.get(),
            count_direction=self._count_dir_var.get(),
            retrigger=self._retrigger_var.get(),
        )
        self.destroy()

    def _on_cancel(self):
        """Cancel the dialog."""
        self.result = None
        self.destroy()
