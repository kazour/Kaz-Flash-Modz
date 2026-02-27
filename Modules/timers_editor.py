"""
Cooldown Editor UI Module for KzBuilder 3.3.5

Visual editor for configuring cooldown tracking timers.
Two-column layout: Preview + Appearance | Presets + Timer List.
Timer details are edited via TimerEditorDialog (modal).
"""

import tkinter as tk
from tkinter import ttk
from ttkbootstrap import Button as ttbButton
from ttkbootstrap.dialogs import Messagebox

from typing import Callable, Optional, List

from .ui_helpers import (
    TK_COLORS, AS2_COLORS, style_tk_listbox, style_tk_canvas,
    blend_alpha, create_rounded_rect,
    FONT_SMALL, FONT_SMALL_BOLD, FONT_FORM_LABEL,
    ColorSwatch,
)
from .timers_appearance import (
    VALID_BUTTON_SHAPES,
    validate_all_settings as validate_appearance,
)

from .timers_data import (
    CooldownSettings, CooldownPreset,
    TriggerType, MAX_PRESETS, MAX_TIMERS_PER_PRESET,
    load_settings, save_settings,
    format_duration_display,
)

# Trigger type abbreviations for listbox display
TRIGGER_ABBREV = {
    TriggerType.BUFF_ADD.value: "B+",
    TriggerType.BUFF_REMOVE.value: "B-",
    TriggerType.CAST_SUCCESS.value: "CS",
}


class TimersEditorPanel(ttk.Frame):
    """
    Cooldown Editor panel — preview + appearance settings (Col 0),
    presets + timer list (Col 1). Timer details edited via dialog.
    """

    def __init__(self, parent, settings_folder: str, on_change: Optional[Callable] = None,
                 database=None, appearance_settings=None, on_appearance_change: Optional[Callable] = None):
        super().__init__(parent)
        self.settings_folder = settings_folder
        self.on_change = on_change
        self.database = database
        self._on_appearance_change = on_appearance_change

        # Load settings
        self.settings = load_settings(settings_folder)

        # Custom appearance settings (None = use AS2_COLORS defaults)
        self._appearance = appearance_settings

        # Currently selected timer
        self.selected_timer_index: Optional[int] = None

        # Currently selected preset for editing
        self.selected_preset_index: int = 0

        # Suppress event handlers during programmatic updates
        self._updating = False

        # Maps listbox position -> index in settings.timers for the active preset
        self._preset_timer_indices: List[int] = []

        # Guard to suppress _on_timer_select during programmatic selection_set calls
        self._programmatic_select = False

        # Build UI
        self._build_ui()

        # Load initial data
        self._refresh_timer_list()
        self._select_preset(0)
        self._select_first_preset_timer()

    # =========================================================================
    # UI BUILD
    # =========================================================================

    def _build_ui(self):
        """Build the editor UI — 2 columns: preview+appearance | presets+timers."""
        cols_frame = ttk.Frame(self)
        cols_frame.pack(fill='both', expand=True, padx=2, pady=2)
        cols_frame.rowconfigure(0, weight=1)
        cols_frame.columnconfigure(0, weight=1)
        cols_frame.columnconfigure(1, weight=1)

        # ---------- COL 0: Preview + Appearance Settings (scrollable) ----------
        col0_frame = ttk.Frame(cols_frame)
        col0_frame.grid(row=0, column=0, sticky='nsew')
        self._build_preview_column(col0_frame)

        # ---------- COL 1: Presets + Timer List ----------
        mid_frame = ttk.Frame(cols_frame)
        mid_frame.grid(row=0, column=1, sticky='nsew', padx=(2, 0))
        mid_frame.columnconfigure(0, weight=1)
        mid_frame.rowconfigure(2, weight=1)  # list_frame row fills remaining height

        # Preset buttons row
        preset_btn_row = ttk.Frame(mid_frame)
        preset_btn_row.grid(row=0, column=0, sticky='ew', pady=(2, 0))

        self._preset_buttons = []
        for i in range(MAX_PRESETS):
            btn = ttbButton(preset_btn_row, text=f"P{i+1}",
                            command=lambda idx=i: self._select_preset(idx),
                            bootstyle="outline-secondary")
            btn.pack(side='left', padx=1, expand=True, fill='x')
            self._preset_buttons.append(btn)

        # Preset label edit row
        label_row = ttk.Frame(mid_frame)
        label_row.grid(row=1, column=0, sticky='ew', pady=(4, 0))
        ttk.Label(label_row, text="Label:", font=FONT_FORM_LABEL).pack(side='left', padx=(0, 4))
        self._preset_label_var = tk.StringVar()
        self._preset_label_var.trace_add("write", self._on_preset_label_change)
        self._preset_label_entry = ttk.Entry(label_row, textvariable=self._preset_label_var, width=6)
        self._preset_label_entry.pack(side='left')

        # Timer list (fills remaining space)
        self._timer_list_frame = ttk.LabelFrame(mid_frame, text="Timers", padding=5)
        self._timer_list_frame.grid(row=2, column=0, sticky='nsew', pady=(4, 0))

        listbox_frame = ttk.Frame(self._timer_list_frame)
        listbox_frame.pack(fill='both', expand=True)

        self._timer_listbox = tk.Listbox(
            listbox_frame, selectmode='single', height=4, exportselection=False)
        style_tk_listbox(self._timer_listbox)
        self._timer_listbox.pack(side='left', fill='both', expand=True)
        self._timer_listbox.bind("<<ListboxSelect>>", self._on_timer_select)
        self._timer_listbox.bind("<Double-Button-1>", self._on_timer_double_click)

        sb = ttk.Scrollbar(listbox_frame, orient='vertical',
                           command=self._timer_listbox.yview)
        sb.pack(side='right', fill='y')
        self._timer_listbox.configure(yscrollcommand=sb.set)

        btn_bar = ttk.Frame(self._timer_list_frame)
        btn_bar.pack(fill='x', pady=(4, 0))

        ttk.Button(btn_bar, text="Add", command=self._add_timer_via_parent,
                   ).pack(side='left', padx=1)
        ttk.Button(btn_bar, text="Edit", command=self._edit_timer_via_parent,
                   ).pack(side='left', padx=1)
        ttk.Button(btn_bar, text="Delete", command=self._delete_timer,
                   ).pack(side='left', padx=1)
        ttk.Button(btn_bar, text="Delete All", command=self._delete_all_via_parent,
                   ).pack(side='left', padx=1)
        ttk.Button(btn_bar, text="Database", command=self._open_database_via_parent,
                   ).pack(side='right', padx=1)

    # =========================================================================
    # PREVIEW
    # =========================================================================

    def _build_preview_column(self, parent):
        """Build column 0: preview canvas + appearance settings."""
        inner_frame = ttk.Frame(parent)
        inner_frame.pack(fill='both', expand=True)

        # Preview canvas at top (with scrollbar for many timers)
        preview_lf = ttk.LabelFrame(inner_frame, text="Preview", padding=5)
        preview_lf.pack(fill='x', padx=2, pady=(2, 0))

        canvas_frame = ttk.Frame(preview_lf)
        canvas_frame.pack(fill='x')

        self.preview_canvas = tk.Canvas(canvas_frame, width=260, height=260,
                                        highlightthickness=0)
        style_tk_canvas(self.preview_canvas)
        self.preview_canvas.pack(side='left', fill='x', expand=True)

        self._preview_sb = ttk.Scrollbar(canvas_frame, orient='vertical',
                                         command=self.preview_canvas.yview)
        self.preview_canvas.configure(yscrollcommand=self._preview_sb.set)

        self.preview_canvas.bind('<Configure>', lambda _e: self._update_preview())
        self.preview_canvas.bind('<MouseWheel>',
                                 lambda e: self.preview_canvas.yview_scroll(
                                     -1 if e.delta > 0 else 1, 'units'))

        # Appearance settings below preview
        self._build_appearance_settings(inner_frame)

    def _build_appearance_settings(self, parent):
        """Build appearance controls below preview — Layout, Panel, Bar, Buttons sections."""
        s = self._appearance or {}

        # Storage for appearance UI vars
        self._app_vars = {}
        self._app_color_vars = {}
        self._app_swatches = {}

        # === LAYOUT ===
        layout_lf = ttk.LabelFrame(parent, text="Layout")
        layout_lf.configure(padding=8)
        layout_lf.pack(fill='x', padx=2, pady=(4, 2))

        pos_row = ttk.Frame(layout_lf)
        pos_row.pack(fill='x')
        ttk.Label(pos_row, text="Position:", font=FONT_SMALL_BOLD).pack(side='left')
        self._app_spinbox(pos_row, "X:", 'pos_x', 0, 3840, 5, s.get('pos_x', 100))
        self._app_spinbox(pos_row, "Y:", 'pos_y', 0, 2160, 5, s.get('pos_y', 100))

        # === PANEL ===
        panel_lf = ttk.LabelFrame(parent, text="Panel")
        panel_lf.configure(padding=8)
        panel_lf.pack(fill='x', padx=2, pady=2)

        bg_row = ttk.Frame(panel_lf)
        bg_row.pack(fill='x', pady=(0, 2))
        self._app_color_inline(bg_row, "Background", 'background',
                               s.get('colors', {}).get('background', '0D0D0D'))
        self._app_spinbox(bg_row, "Opacity:", 'bg_opacity', 0, 100, 4,
                          s.get('bg_opacity', 85))
        ttk.Label(bg_row, text="%", font=FONT_SMALL).pack(side='left', padx=(1, 0))

        ttk.Separator(panel_lf, orient='horizontal').pack(fill='x', pady=(8, 6))

        bw_row = ttk.Frame(panel_lf)
        bw_row.pack(fill='x')
        self._app_color_inline(bw_row, "Border", 'border',
                               s.get('colors', {}).get('border', '3A3A30'))
        self._app_spinbox(bw_row, "Width:", 'border_width', 1, 4, 3,
                          s.get('border_width', 2))
        self._app_spinbox(bw_row, "Radius:", 'corner_radius', 0, 12, 3,
                          s.get('corner_radius', 0))

        # === BAR ===
        bar_lf = ttk.LabelFrame(parent, text="Bar")
        bar_lf.configure(padding=8)
        bar_lf.pack(fill='x', padx=2, pady=2)

        sz_row = ttk.Frame(bar_lf)
        sz_row.pack(fill='x')
        self._app_spinbox(sz_row, "Height:", 'bar_height', 14, 28, 4,
                          s.get('bar_height', 20))
        ttk.Label(sz_row, text="px", font=FONT_SMALL).pack(side='left', padx=(1, 8))
        self._app_spinbox(sz_row, "Font Size:", 'font_size', 8, 20, 4,
                          s.get('font_size', 11))
        ttk.Label(sz_row, text="px", font=FONT_SMALL).pack(side='left', padx=(1, 8))
        self._app_vars['font_bold'] = tk.BooleanVar(value=s.get('font_bold', True))
        ttk.Checkbutton(sz_row, text="Bold", variable=self._app_vars['font_bold'],
                        command=self._on_app_change).pack(side='left')
        self._app_vars['show_decimals'] = tk.BooleanVar(value=s.get('show_decimals', True))
        ttk.Checkbutton(sz_row, text="Decimals", variable=self._app_vars['show_decimals'],
                        command=self._on_app_change).pack(side='left', padx=(8, 0))

        ttk.Separator(bar_lf, orient='horizontal').pack(fill='x', pady=(8, 6))

        ttk.Label(bar_lf, text="Text:", font=FONT_SMALL_BOLD).pack(anchor='w')
        tc_row = ttk.Frame(bar_lf)
        tc_row.pack(fill='x', pady=(2, 0))
        self._app_color_inline(tc_row, "Color", 'text',
                               s.get('colors', {}).get('text', 'FFFFFF'))
        ttk.Separator(tc_row, orient='vertical').pack(side='left', fill='y', padx=8, pady=2)
        self._app_vars['shadow_enabled'] = tk.BooleanVar(value=s.get('shadow_enabled', False))
        ttk.Checkbutton(tc_row, text="Shadow", variable=self._app_vars['shadow_enabled'],
                        command=self._on_app_change).pack(side='left', padx=(0, 4))
        self._app_color_vars['shadow'] = tk.StringVar(value=s.get('shadow_color', '111111'))
        self._app_swatches['shadow'] = ColorSwatch(
            tc_row, color_var=self._app_color_vars['shadow'],
            on_change=lambda c: self._on_app_color('shadow', c))
        self._app_swatches['shadow'].pack(side='left', padx=(0, 8))
        ttk.Label(tc_row, text="Offset:", font=FONT_SMALL_BOLD).pack(side='left')
        self._app_spinbox(tc_row, "X:", 'text_offset_x', -10, 10, 4,
                          s.get('text_offset_x', 0))
        self._app_spinbox(tc_row, "Y:", 'text_offset_y', -10, 10, 4,
                          s.get('text_offset_y', 0))

        # === BUTTONS ===
        btn_lf = ttk.LabelFrame(parent, text="Buttons")
        btn_lf.configure(padding=8)
        btn_lf.pack(fill='x', padx=2, pady=(2, 4))

        sh_row = ttk.Frame(btn_lf)
        sh_row.pack(fill='x')
        ttk.Label(sh_row, text="Shape:", font=FONT_SMALL_BOLD).pack(side='left')
        self._app_vars['button_shape'] = tk.StringVar(
            value=s.get('button_shape', 'rounded'))
        shape_combo = ttk.Combobox(sh_row, textvariable=self._app_vars['button_shape'],
                                   values=list(VALID_BUTTON_SHAPES), state='readonly', width=10)
        shape_combo.pack(side='left', padx=(4, 0))
        self._app_vars['button_shape'].trace_add('write', self._on_app_change)

        ttk.Separator(btn_lf, orient='horizontal').pack(fill='x', pady=(8, 6))

        ttk.Label(btn_lf, text="Colors:", font=FONT_SMALL_BOLD).pack(anchor='w')
        btn_colors = s.get('button_colors', {})

        bc_row = ttk.Frame(btn_lf)
        bc_row.pack(fill='x', pady=(2, 0))
        for key, label, default in [("bg", "Bg", '000000'), ("border", "Border", '000000'),
                                     ("hover", "Hover", '000000'), ("active_text", "Active", 'CCCCCC'),
                                     ("inactive", "Inactive", 'CCCCCC')]:
            self._app_btn_color_inline(bc_row, label, key,
                                       btn_colors.get(key, default))

        # Trace all spinbox vars for live update
        for key, var in self._app_vars.items():
            if key not in ('button_shape', 'shadow_enabled', 'font_bold', 'show_decimals'):
                var.trace_add('write', self._on_app_change)

    def _app_spinbox(self, parent, label, key, from_val, to_val, width, default):
        """Create a labeled spinbox for appearance settings."""
        frame = ttk.Frame(parent)
        frame.pack(side='left', padx=(0, 10))
        ttk.Label(frame, text=label).pack(side='left')
        self._app_vars[key] = tk.StringVar(value=str(default))
        ttk.Spinbox(frame, from_=from_val, to=to_val, width=width,
                    textvariable=self._app_vars[key],
                    command=self._on_app_change).pack(side='left')

    def _app_color_inline(self, parent, label, color_key, default_hex):
        """Create inline color label + swatch for panel/bar colors."""
        ttk.Label(parent, text=label).pack(side='left')
        self._app_color_vars[color_key] = tk.StringVar(value=default_hex)
        swatch = ColorSwatch(parent, color_var=self._app_color_vars[color_key],
                             on_change=lambda c, k=color_key: self._on_app_color(k, c))
        swatch.pack(side='left', padx=(2, 8))
        self._app_swatches[color_key] = swatch

    def _app_btn_color_inline(self, parent, label, btn_key, default_hex):
        """Create inline color label + swatch for button colors."""
        ttk.Label(parent, text=label, font=FONT_SMALL).pack(side='left')
        self._app_color_vars[f'btn_{btn_key}'] = tk.StringVar(value=default_hex)
        swatch = ColorSwatch(parent, color_var=self._app_color_vars[f'btn_{btn_key}'],
                             on_change=lambda c, k=btn_key: self._on_app_btn_color(k, c))
        swatch.pack(side='left', padx=(2, 6))
        self._app_swatches[f'btn_{btn_key}'] = swatch

    def _update_preview(self):
        """Redraw KzTimers preview with appearance settings."""
        c = self.preview_canvas
        c.delete("all")

        # Resolve appearance settings
        app = self._appearance
        if app:
            bg_hex = f"#{app['colors']['background']}"
            txt_hex = f"#{app['colors']['text']}"
            border_hex = f"#{app['colors']['border']}"
            bg_opacity = app.get("bg_opacity", 85)
            border_w = app.get("border_width", 2)
            corner_r = app.get("corner_radius", 0)
            font_size = app.get("font_size", 11)
            bar_h = app.get("bar_height", 20)
            text_ox = app.get("text_offset_x", 0)
            text_oy = app.get("text_offset_y", 0)
            font_bold = app.get("font_bold", True)
            shadow_on = app.get("shadow_enabled", False)
            shadow_hex = f"#{app.get('shadow_color', '111111')}"
            show_decimals = app.get("show_decimals", True)
            btn_shape = app.get("button_shape", "rounded")
            btn_colors = app.get("button_colors", {})
            btn_bg_hex = f"#{btn_colors.get('bg', '1A1A18')}"
            btn_border_hex = f"#{btn_colors.get('border', '4A4A40')}"
            active_txt_hex = f"#{btn_colors.get('active_text', 'FF6666')}"
            inactive_txt_hex = f"#{btn_colors.get('inactive', 'CCCCCC')}"
        else:
            bg_hex = AS2_COLORS["bg"]
            txt_hex = "#FFFFFF"
            border_hex = AS2_COLORS["border"]
            bg_opacity = 85
            border_w = 2
            corner_r = 0
            font_size = 11
            bar_h = 20
            text_ox = 0
            text_oy = 0
            font_bold = True
            shadow_on = False
            shadow_hex = "#111111"
            show_decimals = True
            btn_shape = "rounded"
            btn_bg_hex = AS2_COLORS["button_bg"]
            btn_border_hex = AS2_COLORS["button_border"]
            active_txt_hex = "#FF6666"
            inactive_txt_hex = "#CCCCCC"

        font_family = "Arial"
        canvas_bg = TK_COLORS['bg']
        blended_bg = blend_alpha(bg_hex, canvas_bg, bg_opacity)

        cw = c.winfo_width()
        ch = c.winfo_height()
        if cw < 50 or ch < 50:
            c.after(100, self._update_preview)
            return

        # Button radius based on shape (preview uses 5 instead of AS2's 3 for visibility)
        btn_h = 20
        if btn_shape == "pill":
            btn_r = btn_h // 2
        elif btn_shape == "rounded":
            btn_r = 5
        else:
            btn_r = 0

        # Panel dimensions
        panel_w = min(cw - 10, 240)
        panel_x = (cw - panel_w) // 2
        panel_y = 5
        inset = border_w

        # Preset buttons row
        btn_gap = 2
        btn_row_y = panel_y + inset + 4
        btn_start_x = panel_x + inset + 10
        num_presets = min(len(self.settings.presets), MAX_PRESETS)
        if num_presets == 0:
            num_presets = 3
        total_gap = btn_gap * (num_presets - 1)
        btn_w = (panel_w - inset * 2 - 20 - total_gap) // num_presets

        # Calculate content height
        bar_gap = 2
        if self.selected_preset_index < len(self.settings.presets):
            preset = self.settings.presets[self.selected_preset_index]
            preset_ids = set(preset.timer_ids)
            timers_to_show = [t for t in self.settings.timers if t.id in preset_ids][:10]
        else:
            timers_to_show = []
        bars_height = len(timers_to_show) * (bar_h + bar_gap) if timers_to_show else 30
        panel_h = (btn_row_y - panel_y) + btn_h + 10 + bars_height + 8

        # Border
        create_rounded_rect(c, panel_x, panel_y, panel_x + panel_w, panel_y + panel_h,
                            corner_r, fill='', outline=border_hex, width=border_w)
        # Background
        inner_r = max(0, corner_r - border_w)
        create_rounded_rect(c, panel_x + inset, panel_y + inset,
                            panel_x + panel_w - inset, panel_y + panel_h - inset,
                            inner_r, fill=blended_bg, outline='')

        # Draw preset buttons
        for i in range(num_presets):
            bx = btn_start_x + i * (btn_w + btn_gap)
            by = btn_row_y
            create_rounded_rect(c, bx, by, bx + btn_w, by + btn_h,
                                btn_r, fill=btn_bg_hex, outline=btn_border_hex, width=1)
            if i < len(self.settings.presets):
                label = self.settings.presets[i].label or f"P{i+1}"
            else:
                label = f"P{i+1}"
            is_active = i == self.selected_preset_index
            lbl_color = active_txt_hex if is_active else inactive_txt_hex
            btn_font_size = -10 if is_active else -9
            c.create_text(bx + btn_w // 2, by + btn_h // 2, text=label,
                          anchor='center', fill=lbl_color,
                          font=(font_family, btn_font_size, 'bold'))

        # Divider line
        div_y = btn_row_y + btn_h + 5
        div_x1 = panel_x + inset + 8
        div_x2 = panel_x + panel_w - inset - 8
        c.create_line(div_x1, div_y, div_x2, div_y, fill=border_hex, width=1)

        # Sample bars
        bar_y = btn_row_y + btn_h + 10
        bar_x = panel_x + inset + 4
        bar_w = panel_w - inset * 2 - 8
        bar_font = (font_family, -max(8, font_size - 1), 'bold') if font_bold else (font_family, -max(8, font_size - 1))

        if not timers_to_show:
            c.create_text(panel_x + panel_w // 2, bar_y + 12,
                          text="(No timers in preset)", anchor='center',
                          fill='gray', font=(font_family, -max(8, font_size - 1)))
        else:
            for i, timer in enumerate(timers_to_show):
                y = bar_y + i * (bar_h + bar_gap)

                track_color = blend_alpha('#222222', canvas_bg, 60)
                c.create_rectangle(bar_x, y, bar_x + bar_w, y + bar_h,
                                   fill=track_color, outline='')

                progress = max(0.15, 1.0 - (i * 0.09))
                fill_w = max(0, int(bar_w * progress))
                if fill_w > 0:
                    bar_fill = blend_alpha(f"#{timer.bar_color}", canvas_bg, 80)
                    c.create_rectangle(bar_x, y, bar_x + fill_w, y + bar_h,
                                       fill=bar_fill, outline='')

                # Time string: respect count_direction and show_decimals
                if timer.count_direction == "ascending":
                    display_sec = timer.duration * (1.0 - progress)
                else:
                    display_sec = timer.duration * progress
                if show_decimals:
                    time_str = format_duration_display(display_sec)
                else:
                    time_str = f"{int(display_sec)}s" if display_sec < 60 else format_duration_display(display_sec)

                if shadow_on:
                    c.create_text(bar_x + 4 + text_ox + 1, y + bar_h // 2 + text_oy + 1,
                                  text=timer.name, anchor='w', fill=shadow_hex, font=bar_font)
                    c.create_text(bar_x + bar_w - 4 + text_ox + 1, y + bar_h // 2 + text_oy + 1,
                                  text=time_str, anchor='e', fill=shadow_hex, font=bar_font)

                c.create_text(bar_x + 4 + text_ox, y + bar_h // 2 + text_oy,
                              text=timer.name, anchor='w', fill=txt_hex, font=bar_font)
                c.create_text(bar_x + bar_w - 4 + text_ox, y + bar_h // 2 + text_oy,
                              text=time_str, anchor='e', fill=txt_hex, font=bar_font)

        # Update scroll region and show/hide scrollbar
        content_h = panel_y + panel_h + 5
        c.configure(scrollregion=(0, 0, cw, content_h))
        if content_h > ch:
            self._preview_sb.pack(side='right', fill='y')
        else:
            self._preview_sb.pack_forget()

    # =========================================================================
    # TIMER LIST
    # =========================================================================

    def _refresh_timer_list(self):
        """Refresh the timer listbox — shows only timers in the current preset."""
        self._timer_listbox.delete(0, 'end')

        # Build filtered index list: listbox pos -> actual index in settings.timers
        if self.selected_preset_index < len(self.settings.presets):
            preset_ids = set(self.settings.presets[self.selected_preset_index].timer_ids)
        else:
            preset_ids = set()
        self._preset_timer_indices = [
            i for i, t in enumerate(self.settings.timers) if t.id in preset_ids
        ]

        for idx in self._preset_timer_indices:
            timer = self.settings.timers[idx]
            abbrev = TRIGGER_ABBREV.get(timer.trigger_type, "?")
            dur = format_duration_display(timer.duration)
            arrow = "\u2191" if timer.count_direction == "ascending" else "\u2193"
            self._timer_listbox.insert('end', f"[{abbrev}] {timer.name} ({dur} {arrow})")

        self._update_preset_button_styles()
        count = len(self._preset_timer_indices)
        self._timer_list_frame.configure(text=f"Timers ({count} / {MAX_TIMERS_PER_PRESET})")
        if hasattr(self, 'preview_canvas'):
            self._update_preview()

    def _select_first_preset_timer(self):
        """Select the first timer in the current preset, or clear selection."""
        if self._preset_timer_indices:
            self._select_timer(self._preset_timer_indices[0])
        else:
            self.selected_timer_index = None

    # =========================================================================
    # TIMER SELECTION
    # =========================================================================

    def _on_timer_select(self, event):
        """Handle timer selection in listbox."""
        if self._programmatic_select:
            return
        sel = self._timer_listbox.curselection()
        if sel:
            filtered_idx = sel[0]
            if filtered_idx < len(self._preset_timer_indices):
                self._select_timer(self._preset_timer_indices[filtered_idx])

    def _on_timer_double_click(self, event):
        """Handle double-click on timer — open edit dialog."""
        sel = self._timer_listbox.curselection()
        if not sel:
            return
        filtered_idx = sel[0]
        if filtered_idx >= len(self._preset_timer_indices):
            return
        timer_idx = self._preset_timer_indices[filtered_idx]
        self._select_timer(timer_idx)
        # Open edit dialog via parent tab
        # Walk up to find TimersTab
        p = self.master
        while p is not None:
            if hasattr(p, '_edit_timer') and callable(getattr(p, '_edit_timer', None)):
                getattr(p, '_edit_timer')()
                return
            p = getattr(p, 'master', None)

    def _select_timer(self, index: int):
        """Select a timer in the listbox."""
        if index < 0 or index >= len(self.settings.timers):
            return

        self.selected_timer_index = index

        # Highlight in listbox using filtered position
        self._programmatic_select = True
        self._timer_listbox.selection_clear(0, 'end')
        if index in self._preset_timer_indices:
            filtered_pos = self._preset_timer_indices.index(index)
            self._timer_listbox.selection_set(filtered_pos)
            self._timer_listbox.see(filtered_pos)
        self._programmatic_select = False

    # =========================================================================
    # TIMER CRUD
    # =========================================================================

    def _add_timer_via_parent(self):
        """Open add dialog via parent tab."""
        p = self.master
        while p is not None:
            if hasattr(p, '_add_timer') and callable(getattr(p, '_add_timer', None)):
                getattr(p, '_add_timer')()
                return
            p = getattr(p, 'master', None)

    def _edit_timer_via_parent(self):
        """Open edit dialog for selected timer via parent tab."""
        p = self.master
        while p is not None:
            if hasattr(p, '_edit_timer') and callable(getattr(p, '_edit_timer', None)):
                getattr(p, '_edit_timer')()
                return
            p = getattr(p, 'master', None)

    def _delete_all_via_parent(self):
        """Delete all timers in the current preset."""
        if self.selected_preset_index >= len(self.settings.presets):
            return
        
        preset = self.settings.presets[self.selected_preset_index]
        if not preset.timer_ids:
            return
        
        result = Messagebox.yesno(
            f"Delete all {len(preset.timer_ids)} timers from this preset?",
            title="Delete All Timers", parent=self)
        if result != "Yes":
            return
        
        # Remove all timers from current preset
        timer_ids_to_remove = preset.timer_ids.copy()
        preset.timer_ids.clear()
        
        # Remove timers that aren't referenced by any other preset
        timers_to_delete = []
        for timer_id in timer_ids_to_remove:
            if not any(timer_id in p.timer_ids for p in self.settings.presets):
                timers_to_delete.append(next((t for t in self.settings.timers if t.id == timer_id), None))
        
        for timer in timers_to_delete:
            if timer is not None:
                self.settings.timers.remove(timer)
        
        self.selected_timer_index = None
        self._refresh_timer_list()
        self._select_first_preset_timer()
        self._save_and_notify()

    def _open_database_via_parent(self):
        """Open database editor via parent tab."""
        p = self.master
        while p is not None:
            if hasattr(p, '_open_database') and callable(getattr(p, '_open_database', None)):
                getattr(p, '_open_database')()
                return
            p = getattr(p, 'master', None)

    def _delete_timer(self):
        """Remove the selected timer from the current preset (and globally if unreferenced)."""
        if self.selected_timer_index is None:
            return

        timer = self.settings.timers[self.selected_timer_index]

        result = Messagebox.yesno(
            f"Remove timer '{timer.name}' from this preset?",
            title="Remove Timer", parent=self)
        if result != "Yes":
            return

        # Remove from current preset
        if self.selected_preset_index < len(self.settings.presets):
            preset = self.settings.presets[self.selected_preset_index]
            if timer.id in preset.timer_ids:
                preset.timer_ids.remove(timer.id)

        # If no other preset references this timer, remove it globally
        if not any(timer.id in p.timer_ids for p in self.settings.presets):
            self.settings.timers.remove(timer)

        self.selected_timer_index = None

        self._refresh_timer_list()
        self._select_first_preset_timer()
        self._save_and_notify()

    # =========================================================================
    # PRESET MANAGEMENT
    # =========================================================================

    def _select_preset(self, index: int):
        """Switch preset — refreshes timer list to show only this preset's timers."""
        self.selected_preset_index = index
        # Ensure preset exists
        while len(self.settings.presets) <= index:
            self.settings.presets.append(CooldownPreset())
        self._update_preset_button_styles()
        # Update label field for selected preset
        self._updating = True
        try:
            self._preset_label_var.set(self.settings.presets[index].label[:4])
        finally:
            self._updating = False
        # Clear selection and refresh list for the new preset
        self.selected_timer_index = None
        if hasattr(self, '_timer_listbox'):
            self._refresh_timer_list()
            self._select_first_preset_timer()
        if self.on_change:
            self.on_change()

    def _update_preset_button_styles(self):
        """Update preset button text and highlight."""
        for i, btn in enumerate(self._preset_buttons):
            if i < len(self.settings.presets):
                preset = self.settings.presets[i]
                label = preset.label if preset.label else f"P{i+1}"
                count = len(preset.timer_ids)
                text = f"{label} ({count})" if count > 0 else label
            else:
                text = f"P{i+1}"

            btn.configure(text=text)
            if i == self.selected_preset_index:
                btn.configure(bootstyle="info")
            else:
                btn.configure(bootstyle="outline-secondary")

    def _on_preset_label_change(self, *args):
        """Handle preset label entry change."""
        if self._updating:
            return
        if self.selected_preset_index >= len(self.settings.presets):
            return
        value = self._preset_label_var.get()
        if len(value) > 4:
            self._updating = True
            self._preset_label_var.set(value[:4])
            self._updating = False
            return
        self.settings.presets[self.selected_preset_index].label = value.strip()
        self._update_preset_button_styles()
        self._save_and_notify()

    # =========================================================================
    # SAVE / PUBLIC API
    # =========================================================================

    def _save_and_notify(self):
        """Save settings and notify parent."""
        save_settings(self.settings_folder, self.settings)
        if hasattr(self, 'preview_canvas'):
            self._update_preview()
        if self.on_change:
            self.on_change()

    def get_settings(self) -> CooldownSettings:
        """Get current settings."""
        return self.settings

    def save_settings(self):
        """Save settings to disk."""
        save_settings(self.settings_folder, self.settings)

    def load_appearance(self, settings):
        """Load appearance settings into UI controls."""
        self._appearance = settings
        if hasattr(self, '_app_vars'):
            old_updating = self._updating
            self._updating = True
            try:
                self._app_vars['bar_height'].set(str(settings.get('bar_height', 20)))
                self._app_vars['font_size'].set(str(settings.get('font_size', 11)))
                self._app_vars['text_offset_x'].set(str(settings.get('text_offset_x', 0)))
                self._app_vars['text_offset_y'].set(str(settings.get('text_offset_y', 0)))
                self._app_vars['bg_opacity'].set(str(settings.get('bg_opacity', 85)))
                self._app_vars['border_width'].set(str(settings.get('border_width', 2)))
                self._app_vars['corner_radius'].set(str(settings.get('corner_radius', 0)))
                self._app_vars['pos_x'].set(str(settings.get('pos_x', 100)))
                self._app_vars['pos_y'].set(str(settings.get('pos_y', 100)))
                self._app_vars['button_shape'].set(settings.get('button_shape', 'rounded'))
                self._app_vars['shadow_enabled'].set(settings.get('shadow_enabled', False))
                self._app_vars['font_bold'].set(settings.get('font_bold', True))
                self._app_vars['show_decimals'].set(settings.get('show_decimals', True))

                colors = settings.get('colors', {})
                self._app_color_vars['text'].set(colors.get('text', 'FFFFFF'))
                self._app_color_vars['background'].set(colors.get('background', '0D0D0D'))
                self._app_color_vars['border'].set(colors.get('border', '3A3A30'))
                self._app_color_vars['shadow'].set(settings.get('shadow_color', '111111'))

                btn_colors = settings.get('button_colors', {})
                for k in ('bg', 'border', 'hover', 'active_text', 'inactive'):
                    var_key = f'btn_{k}'
                    if var_key in self._app_color_vars:
                        self._app_color_vars[var_key].set(btn_colors.get(k, '000000'))
            finally:
                self._updating = old_updating
        if hasattr(self, 'preview_canvas'):
            self._update_preview()

    # =========================================================================
    # APPEARANCE EVENT HANDLERS
    # =========================================================================

    def _on_app_change(self, *args):
        """Handle any appearance setting change."""
        if self._updating:
            return
        new_settings = self._collect_appearance_settings()
        if new_settings is None:
            return
        self._appearance = new_settings
        self._update_preview()
        if self._on_appearance_change:
            self._on_appearance_change(new_settings)

    def _on_app_color(self, color_key, hex_color):
        """Handle panel/bar color swatch pick."""
        hex_val = hex_color.lstrip('#').upper()
        if color_key in self._app_color_vars:
            self._app_color_vars[color_key].set(hex_val)
        self._on_app_change()

    def _on_app_btn_color(self, btn_key, hex_color):
        """Handle button color swatch pick."""
        hex_val = hex_color.lstrip('#').upper()
        var_key = f'btn_{btn_key}'
        if var_key in self._app_color_vars:
            self._app_color_vars[var_key].set(hex_val)
        self._on_app_change()

    def _collect_appearance_settings(self):
        """Read all appearance UI controls into a validated settings dict."""
        try:
            s = {
                'bar_height': int(self._app_vars['bar_height'].get()),
                'font_size': int(self._app_vars['font_size'].get()),
                'text_offset_x': int(self._app_vars['text_offset_x'].get()),
                'text_offset_y': int(self._app_vars['text_offset_y'].get()),
                'bg_opacity': int(self._app_vars['bg_opacity'].get()),
                'border_width': int(self._app_vars['border_width'].get()),
                'corner_radius': int(self._app_vars['corner_radius'].get()),
                'pos_x': int(self._app_vars['pos_x'].get()),
                'pos_y': int(self._app_vars['pos_y'].get()),
                'button_shape': self._app_vars['button_shape'].get(),
                'font_bold': self._app_vars['font_bold'].get(),
                'show_decimals': self._app_vars['show_decimals'].get(),
                'shadow_enabled': self._app_vars['shadow_enabled'].get(),
                'shadow_color': self._app_color_vars['shadow'].get(),
                'colors': {
                    'background': self._app_color_vars['background'].get(),
                    'text': self._app_color_vars['text'].get(),
                    'border': self._app_color_vars['border'].get(),
                },
                'button_colors': {
                    'bg': self._app_color_vars['btn_bg'].get(),
                    'border': self._app_color_vars['btn_border'].get(),
                    'hover': self._app_color_vars['btn_hover'].get(),
                    'active_text': self._app_color_vars['btn_active_text'].get(),
                    'inactive': self._app_color_vars['btn_inactive'].get(),
                },
            }
            return validate_appearance(s)
        except (ValueError, tk.TclError):
            return None
