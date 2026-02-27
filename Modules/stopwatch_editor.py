"""
Stopwatch Editor UI Module for KzBuilder 3.3.4

Two-column editor for stopwatch presets and appearance.
Column 0: Preview canvas + appearance settings (scrollable).
Column 1: Preset selection + phase list with CRUD.
Phase details are edited via PhaseEditorDialog (modal).
"""

import tkinter as tk
from tkinter import ttk
from ttkbootstrap.dialogs import Messagebox

from typing import Callable, Optional

from .ui_helpers import (
    TK_COLORS, style_tk_listbox, style_tk_canvas,
    blend_alpha, create_rounded_rect,
    FONT_SMALL, FONT_SMALL_BOLD, FONT_FORM_LABEL,
    ColorSwatch,
)
from .stopwatch_settings import (
    STOPWATCH_RANGES, VALID_LAYOUTS, VALID_BUTTON_SHAPES,
    validate_all_settings as validate_appearance,
)
from .stopwatch_data import (
    StopwatchPresetSettings, StopwatchPreset, StopwatchPhase,
    MAX_PRESETS, MAX_PHASES_PER_PRESET,
    load_settings as load_preset_settings,
    save_settings as save_preset_settings,
    format_duration_display,
)


class StopwatchEditorPanel(ttk.Frame):
    """
    Stopwatch editor panel — preview + appearance settings (Col 0),
    presets + phase list (Col 1). Phase details edited via dialog.
    """

    def __init__(self, parent, settings_folder: str,
                 appearance_settings: dict,
                 on_appearance_change: Optional[Callable] = None,
                 on_preset_change: Optional[Callable] = None):
        super().__init__(parent)
        self.settings_folder = settings_folder
        self._appearance = appearance_settings
        self._on_appearance_change = on_appearance_change
        self._on_preset_change = on_preset_change

        # Load preset settings
        self.preset_settings = load_preset_settings(settings_folder)

        # Ensure 3 presets exist
        while len(self.preset_settings.presets) < MAX_PRESETS:
            self.preset_settings.presets.append(StopwatchPreset())

        # Currently selected preset
        self.selected_preset_index: int = 0

        # Suppress event handlers during programmatic updates
        self._updating = False

        # Build UI
        self._build_ui()

        # Load initial state
        self._select_preset(0)
        self._update_layout_state()

    # =========================================================================
    # UI BUILD
    # =========================================================================

    def _build_ui(self):
        """Build the editor UI — 2 columns: preview+appearance | presets+phases."""
        cols_frame = ttk.Frame(self)
        cols_frame.pack(fill='both', expand=True, padx=2, pady=2)
        cols_frame.rowconfigure(0, weight=1)
        cols_frame.columnconfigure(0, weight=1, minsize=460)
        cols_frame.columnconfigure(1, weight=1)

        # ---------- COL 0: Preview + Appearance ----------
        col0_frame = ttk.Frame(cols_frame)
        col0_frame.grid(row=0, column=0, sticky='nsew')
        self._build_preview_column(col0_frame)

        # ---------- COL 1: Presets + Phase List (matches timers_editor) ----------
        self._col1_frame = ttk.Frame(cols_frame)
        self._col1_frame.grid(row=0, column=1, sticky='nsew', padx=(2, 0))
        self._col1_frame.columnconfigure(0, weight=1)
        self._col1_frame.rowconfigure(2, weight=1)  # phase list fills remaining height

        # Preset buttons row
        preset_btn_row = ttk.Frame(self._col1_frame)
        preset_btn_row.grid(row=0, column=0, sticky='ew', pady=(2, 0))

        self._preset_buttons = []
        for i in range(MAX_PRESETS):
            btn = ttk.Button(preset_btn_row, text=f"P{i+1}",
                             command=lambda idx=i: self._select_preset(idx),
                             bootstyle="outline-secondary")
            btn.pack(side='left', padx=1, expand=True, fill='x')
            self._preset_buttons.append(btn)

        # Preset settings LabelFrame
        preset_lf = ttk.LabelFrame(self._col1_frame, text="Preset")
        preset_lf.configure(padding=8)
        preset_lf.grid(row=1, column=0, sticky='ew', pady=(4, 0))

        label_row = ttk.Frame(preset_lf)
        label_row.pack(fill='x')
        ttk.Label(label_row, text="Label:", font=FONT_SMALL_BOLD).pack(side='left', padx=(0, 4))
        self._preset_label_var = tk.StringVar()
        self._preset_label_var.trace_add("write", self._on_preset_label_change)
        self._preset_label_entry = ttk.Entry(label_row, textvariable=self._preset_label_var, width=6)
        self._preset_label_entry.pack(side='left')

        ttk.Separator(preset_lf, orient='horizontal').pack(fill='x', pady=(8, 6))

        end_row = ttk.Frame(preset_lf)
        end_row.pack(fill='x')
        self._end_behavior_var = tk.StringVar(value="loop")
        ttk.Label(end_row, text="End:", font=FONT_SMALL_BOLD).pack(side='left', padx=(0, 6))
        ttk.Radiobutton(end_row, text="Loop", value="loop",
                        variable=self._end_behavior_var,
                        command=self._on_preset_prop_change).pack(side='left', padx=(0, 4))
        ttk.Radiobutton(end_row, text="End", value="end",
                        variable=self._end_behavior_var,
                        command=self._on_preset_prop_change).pack(side='left', padx=(0, 4))
        ttk.Radiobutton(end_row, text="Continue", value="continue",
                        variable=self._end_behavior_var,
                        command=self._on_preset_prop_change).pack(side='left')

        dir_row = ttk.Frame(preset_lf)
        dir_row.pack(fill='x', pady=(4, 0))
        self._count_dir_var = tk.StringVar(value="ascending")
        ttk.Label(dir_row, text="Direction:", font=FONT_SMALL_BOLD).pack(side='left', padx=(0, 6))
        ttk.Radiobutton(dir_row, text="\u2191 Ascending", value="ascending",
                        variable=self._count_dir_var,
                        command=self._on_preset_prop_change).pack(side='left', padx=(0, 4))
        ttk.Radiobutton(dir_row, text="\u2193 Descending", value="descending",
                        variable=self._count_dir_var,
                        command=self._on_preset_prop_change).pack(side='left')

        # Phase list
        self._phase_list_frame = ttk.LabelFrame(self._col1_frame, text="Phases (0/10)", padding=5)
        self._phase_list_frame.grid(row=2, column=0, sticky='nsew', pady=(4, 0))

        listbox_frame = ttk.Frame(self._phase_list_frame)
        listbox_frame.pack(fill='both', expand=True)

        self._phase_listbox = tk.Listbox(
            listbox_frame, selectmode='single', height=4, exportselection=False)
        style_tk_listbox(self._phase_listbox)
        self._phase_listbox.pack(side='left', fill='both', expand=True)
        self._phase_listbox.bind("<Double-Button-1>", self._on_phase_double_click)

        sb = ttk.Scrollbar(listbox_frame, orient='vertical',
                           command=self._phase_listbox.yview)
        sb.pack(side='right', fill='y')
        self._phase_listbox.configure(yscrollcommand=sb.set)

        # Button bar
        btn_bar = ttk.Frame(self._phase_list_frame)
        btn_bar.pack(fill='x', pady=(4, 0))

        ttk.Button(btn_bar, text="Add", command=self._add_phase_via_parent,
                   ).pack(side='left', padx=1)
        ttk.Button(btn_bar, text="Edit", command=self._edit_phase_via_parent,
                   ).pack(side='left', padx=1)
        ttk.Button(btn_bar, text="Delete", command=self._delete_phase,
                   ).pack(side='left', padx=1)
        ttk.Button(btn_bar, text="\u25B2", width=3, command=self._move_phase_up,
                   ).pack(side='left', padx=1)
        ttk.Button(btn_bar, text="\u25BC", width=3, command=self._move_phase_down,
                   ).pack(side='left', padx=1)

    # =========================================================================
    # PREVIEW
    # =========================================================================

    def _build_preview_column(self, parent):
        """Build column 0: layout radios + preview canvas + appearance settings (scrollable)."""
        inner_frame = ttk.Frame(parent)
        inner_frame.pack(fill='both', expand=True)

        # Layout radios above preview (not inside any LabelFrame)
        s = self._appearance or {}
        ly_row = ttk.Frame(inner_frame)
        ly_row.pack(fill='x', padx=2, pady=(2, 0))
        self._app_vars = {}
        self._app_color_vars = {}
        self._app_swatches = {}
        self._app_vars['layout'] = tk.StringVar(value=s.get('layout', 'standard'))
        ttk.Radiobutton(ly_row, text="Standard", value="standard",
                        variable=self._app_vars['layout'],
                        command=self._on_layout_change).pack(side='left', padx=(0, 8))
        ttk.Radiobutton(ly_row, text="Compact", value="compact",
                        variable=self._app_vars['layout'],
                        command=self._on_layout_change).pack(side='left')

        # Preview canvas
        preview_lf = ttk.LabelFrame(inner_frame, text="Preview", padding=5)
        preview_lf.pack(fill='x', padx=2, pady=(2, 0))

        self.preview_canvas = tk.Canvas(preview_lf, width=260, height=220,
                                        highlightthickness=0)
        style_tk_canvas(self.preview_canvas)
        self.preview_canvas.pack(fill='x', expand=True)
        self.preview_canvas.bind('<Configure>', lambda _e: self._update_preview())

        # Appearance settings below preview (scrollable)
        self._build_appearance_settings(inner_frame)

    def _build_appearance_settings(self, parent):
        """Build appearance controls below preview — matches timers_editor pattern."""
        s = self._appearance or {}

        # === LAYOUT (Position) ===
        layout_lf = ttk.LabelFrame(parent, text="Layout")
        layout_lf.configure(padding=8)
        layout_lf.pack(fill='x', padx=2, pady=2)

        pos_row = ttk.Frame(layout_lf)
        pos_row.pack(fill='x')
        ttk.Label(pos_row, text="Position:", font=FONT_SMALL_BOLD).pack(side='left')
        self._app_spinbox(pos_row, "X:", 'pos_x', 0, 3840, 5, s.get('pos_x', 400))
        self._app_spinbox(pos_row, "Y:", 'pos_y', 0, 2160, 5, s.get('pos_y', 300))

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

        # === DISPLAY (equivalent of timers' Bar section) ===
        display_lf = ttk.LabelFrame(parent, text="Display")
        display_lf.configure(padding=8)
        display_lf.pack(fill='x', padx=2, pady=2)

        sz_row = ttk.Frame(display_lf)
        sz_row.pack(fill='x')
        self._app_spinbox(sz_row, "W:", 'width', 120, 400, 5, s.get('width', 240))
        self._app_spinbox(sz_row, "H:", 'height', 40, 200, 5, s.get('height', 110))

        ttk.Separator(display_lf, orient='horizontal').pack(fill='x', pady=(8, 6))

        ttk.Label(display_lf, text="Text:", font=FONT_SMALL_BOLD).pack(anchor='w')
        tc_row = ttk.Frame(display_lf)
        tc_row.pack(fill='x', pady=(2, 0))
        self._app_color_inline(tc_row, "Color", 'text',
                               s.get('colors', {}).get('text', 'CCCCCC'))
        self._app_spinbox(tc_row, "Font:", 'font_size', 12, 48, 4, s.get('font_size', 28))
        self._app_spinbox(tc_row, "Phase:", 'phase_font_size', 8, 24, 3, s.get('phase_font_size', 12))

        shadow_row = ttk.Frame(display_lf)
        shadow_row.pack(fill='x', pady=(2, 0))
        self._app_vars['shadow_enabled'] = tk.BooleanVar(value=s.get('shadow_enabled', True))
        ttk.Checkbutton(shadow_row, text="Shadow", variable=self._app_vars['shadow_enabled'],
                        command=self._on_app_change).pack(side='left', padx=(0, 4))
        self._app_color_vars['shadow'] = tk.StringVar(value=s.get('shadow_color', '111111'))
        self._app_swatches['shadow'] = ColorSwatch(
            shadow_row, color_var=self._app_color_vars['shadow'],
            on_change=lambda c: self._on_app_color('shadow', c))
        self._app_swatches['shadow'].pack(side='left', padx=(0, 8))

        # === BUTTONS ===
        btn_lf = ttk.LabelFrame(parent, text="Buttons")
        btn_lf.configure(padding=8)
        btn_lf.pack(fill='x', padx=2, pady=(2, 4))

        sh_row = ttk.Frame(btn_lf)
        sh_row.pack(fill='x')
        ttk.Label(sh_row, text="Shape:", font=FONT_SMALL_BOLD).pack(side='left')
        self._app_vars['button_shape'] = tk.StringVar(value=s.get('button_shape', 'rounded'))
        shape_combo = ttk.Combobox(sh_row, textvariable=self._app_vars['button_shape'],
                                   values=list(VALID_BUTTON_SHAPES), state='readonly', width=10)
        shape_combo.pack(side='left', padx=(4, 0))
        self._app_vars['button_shape'].trace_add('write', self._on_app_change)

        ttk.Separator(btn_lf, orient='horizontal').pack(fill='x', pady=(8, 6))

        ttk.Label(btn_lf, text="Colors:", font=FONT_SMALL_BOLD).pack(anchor='w')
        btn_colors = s.get('button_colors', {})

        bc_row = ttk.Frame(btn_lf)
        bc_row.pack(fill='x', pady=(2, 0))
        for key, label, default in [("bg", "Bg", '1A1A18'), ("border", "Border", '4A4A40'),
                                     ("hover", "Hover", '2A2A24'),
                                     ("preset_active", "Active", 'FF6666'),
                                     ("preset_inactive", "Inactive", 'CCCCCC')]:
            self._app_btn_color_inline(bc_row, label, key, btn_colors.get(key, default))

        state_row = ttk.Frame(btn_lf)
        state_row.pack(fill='x', pady=(2, 0))
        for key, label, default in [("start", "Start", '99DD66'), ("pause", "Pause", 'FFE066'),
                                     ("stop", "Stop", 'FF7744'), ("disabled", "Off", '555555')]:
            self._app_btn_color_inline(state_row, label, key, btn_colors.get(key, default))

        # Trace all spinbox vars for live update
        for key, var in self._app_vars.items():
            if key not in ('layout', 'button_shape', 'shadow_enabled'):
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
        """Create inline color label + swatch for panel/text colors."""
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

    # =========================================================================
    # PREVIEW DRAWING
    # =========================================================================

    def _update_preview(self):
        """Redraw stopwatch preview — pixel-accurate match of AS2 layout."""
        canvas = self.preview_canvas
        canvas.delete('all')

        s = self._appearance
        if not s:
            return

        layout = s.get('layout', 'standard')
        w = s.get('width', 240)
        h = s.get('height', 110)
        font_size = s.get('font_size', 28)
        phase_font_size = s.get('phase_font_size', 12)
        opacity = s.get('bg_opacity', 85)
        bg_color = '#' + s.get('colors', {}).get('background', '0D0D0D')
        text_color = '#' + s.get('colors', {}).get('text', 'CCCCCC')
        border_color = '#' + s.get('colors', {}).get('border', '3A3A30')
        border_w = s.get('border_width', 2)
        corner_r = s.get('corner_radius', 0)
        font_family = s.get('font_family', 'Arial')
        shadow_on = s.get('shadow_enabled', True)
        shadow_color = '#' + s.get('shadow_color', '111111')
        btn_shape = s.get('button_shape', 'rounded')
        btn_colors = s.get('button_colors', {})

        # Get preset info
        preset = None
        if self.selected_preset_index < len(self.preset_settings.presets):
            preset = self.preset_settings.presets[self.selected_preset_index]
        has_phases = preset is not None and len(preset.phases) > 0 if preset else False

        # Canvas dimensions
        cw = canvas.winfo_width()
        ch = canvas.winfo_height()
        if cw < 10 or ch < 10:
            canvas.after(100, self._update_preview)
            return

        canvas_bg = TK_COLORS['bg']

        # Scale to fit canvas
        max_w = cw - 20
        max_h = ch - 36
        scale = min(max_w / max(w, 1), max_h / max(h, 1), 1.0)

        def sx(v):
            return round(v * scale)

        sw = sx(w)
        sh = sx(h)
        x0 = (cw - sw) // 2
        y0 = 5

        blended_bg = blend_alpha(bg_color, canvas_bg, opacity)
        timer_font = -max(7, round(font_size * scale))
        scaled_cr = max(0, round(corner_r * scale))
        scaled_bw = max(1, round(border_w * scale))
        # AS2: inner rect at (1,1) to (W-2,H-2) with radius cr-1
        bg_inset = max(1, sx(1))
        scaled_inner_r = max(1, scaled_cr - 1) if scaled_cr > 1 else 0

        btn_bg_hex = '#' + btn_colors.get('bg', '1A1A18')
        btn_border_hex = '#' + btn_colors.get('border', '4A4A40')
        start_hex = '#' + btn_colors.get('start', '99DD66')
        disabled_hex = '#' + btn_colors.get('disabled', '555555')
        preset_active_hex = '#' + btn_colors.get('preset_active', 'FF6666')
        preset_inactive_hex = '#' + btn_colors.get('preset_inactive', 'CCCCCC')

        # Button radius (preview uses 5 instead of AS2's 3 for visibility)
        def get_btn_r(btn_h):
            if btn_shape == "pill":
                return max(0, round(btn_h / 2))
            if btn_shape == "rounded":
                return max(0, round(5 * scale))
            return 0

        if layout == "standard":
            # AS2 layout constants (scaled)
            BTN_HEIGHT = sx(20)
            HEADER_HT = sx(4)
            PRESET_ROW_HT = sx(30)

            # Border (AS2: lineStyle(bw, COLOR_BORDER) at 0,0 to W,H)
            create_rounded_rect(canvas, x0, y0, x0 + sw, y0 + sh,
                                scaled_cr, fill='', outline=border_color, width=scaled_bw)
            # Background (AS2: beginFill at 1,1 to W-2,H-2)
            create_rounded_rect(canvas, x0 + bg_inset, y0 + bg_inset,
                                x0 + sw - bg_inset, y0 + sh - bg_inset,
                                scaled_inner_r, fill=blended_bg, outline='')

            # Control buttons row (bottom, AS2: y=H-BTN_HEIGHT-4, startX=10, gap=2)
            ctrl_btn_h = BTN_HEIGHT
            ctrl_btn_y = y0 + sh - ctrl_btn_h - sx(4)
            ctrl_gap = sx(2)
            ctrl_avail_w = sw - sx(20)
            ctrl_btn_w = min(sx(80), max(1, (ctrl_avail_w - ctrl_gap * 2) // 3))
            ctrl_total_w = ctrl_btn_w * 3 + ctrl_gap * 2
            ctrl_start_x = x0 + (sw - ctrl_total_w) // 2
            ctrl_btn_r = get_btn_r(ctrl_btn_h)

            # Preset buttons row (always 3, centered — matches KzTimers)
            gap = sx(2)
            avail_w = sw - sx(20)
            pb_w = min(sx(80), max(sx(30), (avail_w - gap * (MAX_PRESETS - 1)) // MAX_PRESETS))
            total_btn_w = pb_w * MAX_PRESETS + gap * (MAX_PRESETS - 1)
            start_x = x0 + (sw - total_btn_w) // 2
            start_y = y0 + HEADER_HT

            for idx in range(MAX_PRESETS):
                bx = start_x + idx * (pb_w + gap)
                create_rounded_rect(canvas, bx, start_y,
                                    bx + pb_w, start_y + BTN_HEIGHT,
                                    get_btn_r(BTN_HEIGHT), fill=btn_bg_hex,
                                    outline=btn_border_hex, width=1)
                if idx < len(self.preset_settings.presets):
                    p = self.preset_settings.presets[idx]
                    lbl = p.label or f"P{idx+1}"
                else:
                    lbl = f"P{idx+1}"
                is_active = idx == self.selected_preset_index
                lbl_color = preset_active_hex if is_active else preset_inactive_hex
                # AS2: active size=10, inactive size=9
                pfont = -max(6, round((10 if is_active else 9) * scale))
                canvas.create_text(bx + pb_w // 2, start_y + BTN_HEIGHT // 2,
                                   text=lbl, fill=lbl_color,
                                   font=(font_family, pfont, 'bold'))

            content_top = y0 + HEADER_HT + PRESET_ROW_HT

            # Divider line (AS2: y=contentTop-5, x=8 to W-8, 50% alpha border)
            div_y = content_top - sx(5)
            div_color = blend_alpha(border_color, canvas_bg, 50)
            canvas.create_line(x0 + sx(8), div_y, x0 + sw - sx(8), div_y,
                               fill=div_color, width=1)

            # Bottom divider (above control buttons, mirrors top divider)
            div2_y = ctrl_btn_y - sx(5)
            canvas.create_line(x0 + sx(8), div2_y, x0 + sw - sx(8), div2_y,
                               fill=div_color, width=1)

            # Center phase+timer as a single block between the two dividers
            phase_h = sx(phase_font_size + 4)
            timer_h = sx(font_size + 4)
            block_h = phase_h + timer_h
            area_h = div2_y - content_top
            block_y = content_top + (area_h - block_h) // 2

            # Phase name text
            if has_phases and preset is not None:
                phase_name = preset.phases[0].name
                phase_color = '#' + preset.phases[0].color
                phase_font = -max(6, round(phase_font_size * scale))
                canvas.create_text(x0 + sw // 2, block_y + phase_h // 2,
                                   text=phase_name, fill=phase_color,
                                   font=(font_family, phase_font))

            # Timer text (directly below phase text)
            text_center_y = block_y + phase_h + timer_h // 2

            if shadow_on:
                shadow_off = max(1, round(scale))
                canvas.create_text(x0 + sw // 2 + shadow_off, text_center_y + shadow_off,
                                   text="0:00:00", fill=shadow_color,
                                   font=(font_family, timer_font, 'bold'))
            canvas.create_text(x0 + sw // 2, text_center_y,
                               text="0:00:00", fill=text_color,
                               font=(font_family, timer_font, 'bold'))

            # Control buttons (AS2: same style as preset buttons)
            btn_font = -max(6, round(9 * scale))
            btn_configs = [("Start", start_hex), ("Pause", disabled_hex), ("Stop", disabled_hex)]
            for i, (label, label_color) in enumerate(btn_configs):
                bx = ctrl_start_x + i * (ctrl_btn_w + ctrl_gap)
                create_rounded_rect(canvas, bx, ctrl_btn_y,
                                    bx + ctrl_btn_w, ctrl_btn_y + ctrl_btn_h,
                                    ctrl_btn_r, fill=btn_bg_hex, outline=btn_border_hex, width=1)
                canvas.create_text(bx + ctrl_btn_w // 2, ctrl_btn_y + ctrl_btn_h // 2,
                                   text=label, fill=label_color,
                                   font=(font_family, btn_font, 'bold'))

        else:
            # Compact layout
            create_rounded_rect(canvas, x0, y0, x0 + sw, y0 + sh,
                                scaled_cr, fill='', outline=border_color, width=scaled_bw)
            create_rounded_rect(canvas, x0 + bg_inset, y0 + bg_inset,
                                x0 + sw - bg_inset, y0 + sh - bg_inset,
                                scaled_inner_r, fill=blended_bg, outline='')

            # Control buttons on right (AS2: bSize=min(22, H*0.55), min 12)
            b_size_real = min(22, int(h * 0.55))
            if b_size_real < 12:
                b_size_real = 12
            b_size = sx(b_size_real)
            b_gap = sx(2)
            b_y = y0 + (sh - b_size) // 2
            b_start_x = x0 + sw - (b_size * 3 + b_gap * 2 + sx(border_w) + sx(4))
            b_r = get_btn_r(b_size)

            # Timer text (centered in available space left of control buttons)
            text_start_x = x0 + sx(border_w) + sx(4)
            text_end_x = b_start_x - sx(4)
            text_cx = text_start_x + (text_end_x - text_start_x) // 2
            text_cy = y0 + sh // 2
            if shadow_on:
                shadow_off = max(1, round(scale))
                canvas.create_text(text_cx + shadow_off, text_cy + shadow_off,
                                   text="0:00:00", fill=shadow_color,
                                   font=(font_family, timer_font, 'bold'))
            canvas.create_text(text_cx, text_cy,
                               text="0:00:00", fill=text_color,
                               font=(font_family, timer_font, 'bold'))

            compact_btns = [("S", start_hex), ("P", disabled_hex), ("X", disabled_hex)]
            for idx, (label, label_color) in enumerate(compact_btns):
                bx = b_start_x + idx * (b_size + b_gap)
                create_rounded_rect(canvas, bx, b_y, bx + b_size, b_y + b_size,
                                    b_r, fill=btn_bg_hex, outline=btn_border_hex, width=1)
                canvas.create_text(bx + b_size // 2, b_y + b_size // 2,
                                   text=label, fill=label_color,
                                   font=(font_family, -max(6, round(b_size_real * 0.45 * scale)), 'bold'))

        # Dimension label
        canvas.create_text(cw // 2, y0 + sh + 12,
                           text=f"{w} x {h} px",
                           fill=TK_COLORS['select_bg'],
                           font=FONT_SMALL)

    # =========================================================================
    # PHASE LIST
    # =========================================================================

    def _refresh_phase_list(self):
        """Refresh the phase listbox for the current preset."""
        self._phase_listbox.delete(0, 'end')

        if self.selected_preset_index >= len(self.preset_settings.presets):
            return

        preset = self.preset_settings.presets[self.selected_preset_index]
        i = 0
        while i < len(preset.phases):
            phase = preset.phases[i]
            dur = format_duration_display(phase.duration)
            self._phase_listbox.insert('end', f"{phase.name} ({dur})")
            i += 1

        count = len(preset.phases)
        self._phase_list_frame.configure(text=f"Phases ({count}/{MAX_PHASES_PER_PRESET})")

        if hasattr(self, 'preview_canvas'):
            self._update_preview()

    # =========================================================================
    # PRESET MANAGEMENT
    # =========================================================================

    def _select_preset(self, index: int):
        """Switch to a different preset."""
        self.selected_preset_index = index

        # Ensure preset exists
        while len(self.preset_settings.presets) <= index:
            self.preset_settings.presets.append(StopwatchPreset())

        preset = self.preset_settings.presets[index]

        self._updating = True
        try:
            self._preset_label_var.set(preset.label[:4])
            self._end_behavior_var.set(preset.end_behavior)
            self._count_dir_var.set(preset.count_direction)
        finally:
            self._updating = False

        self._update_preset_button_styles()
        if hasattr(self, '_phase_listbox'):
            self._refresh_phase_list()
        if self._on_preset_change:
            self._on_preset_change()

    def _update_preset_button_styles(self):
        """Update preset button text and highlight."""
        for i, btn in enumerate(self._preset_buttons):
            if i < len(self.preset_settings.presets):
                preset = self.preset_settings.presets[i]
                label = preset.label if preset.label else f"P{i+1}"
                count = len(preset.phases)
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
        if self.selected_preset_index >= len(self.preset_settings.presets):
            return
        value = self._preset_label_var.get()
        if len(value) > 4:
            self._updating = True
            self._preset_label_var.set(value[:4])
            self._updating = False
            return
        self.preset_settings.presets[self.selected_preset_index].label = value.strip()
        self._update_preset_button_styles()
        self._save_and_notify()

    def _on_preset_prop_change(self):
        """Handle end_behavior or count_direction radio change."""
        if self._updating:
            return
        if self.selected_preset_index >= len(self.preset_settings.presets):
            return
        preset = self.preset_settings.presets[self.selected_preset_index]
        preset.end_behavior = self._end_behavior_var.get()
        preset.count_direction = self._count_dir_var.get()
        self._save_and_notify()

    # =========================================================================
    # PHASE CRUD
    # =========================================================================

    def _add_phase_via_parent(self):
        """Open add dialog via parent tab."""
        p = self.master
        while p is not None:
            if hasattr(p, '_add_phase'):
                getattr(p, '_add_phase')()
                return
            p = getattr(p, 'master', None)

    def _edit_phase_via_parent(self):
        """Open edit dialog via parent tab."""
        p = self.master
        while p is not None:
            if hasattr(p, '_edit_phase'):
                getattr(p, '_edit_phase')()
                return
            p = getattr(p, 'master', None)

    def _on_phase_double_click(self, event):
        """Handle double-click on phase — open edit dialog."""
        sel = self._phase_listbox.curselection()
        if not sel:
            return
        self._edit_phase_via_parent()

    def _delete_phase(self):
        """Remove the selected phase from the current preset."""
        sel = self._phase_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        if self.selected_preset_index >= len(self.preset_settings.presets):
            return
        preset = self.preset_settings.presets[self.selected_preset_index]
        if idx >= len(preset.phases):
            return

        phase = preset.phases[idx]
        result = Messagebox.yesno(
            f"Delete phase '{phase.name}'?",
            title="Delete Phase", parent=self)
        if result != "Yes":
            return

        preset.phases.pop(idx)
        self._refresh_phase_list()
        # Re-select nearest
        if preset.phases:
            new_idx = min(idx, len(preset.phases) - 1)
            self._phase_listbox.selection_set(new_idx)
        self._save_and_notify()

    def _move_phase_up(self):
        """Move selected phase up in the list."""
        sel = self._phase_listbox.curselection()
        if not sel or sel[0] == 0:
            return
        idx = sel[0]
        if self.selected_preset_index >= len(self.preset_settings.presets):
            return
        phases = self.preset_settings.presets[self.selected_preset_index].phases
        if idx >= len(phases):
            return
        phases[idx], phases[idx - 1] = phases[idx - 1], phases[idx]
        self._refresh_phase_list()
        self._phase_listbox.selection_set(idx - 1)
        self._save_and_notify()

    def _move_phase_down(self):
        """Move selected phase down in the list."""
        sel = self._phase_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        if self.selected_preset_index >= len(self.preset_settings.presets):
            return
        phases = self.preset_settings.presets[self.selected_preset_index].phases
        if idx >= len(phases) - 1:
            return
        phases[idx], phases[idx + 1] = phases[idx + 1], phases[idx]
        self._refresh_phase_list()
        self._phase_listbox.selection_set(idx + 1)
        self._save_and_notify()

    def get_selected_phase_index(self) -> Optional[int]:
        """Get the index of the currently selected phase, or None."""
        sel = self._phase_listbox.curselection()
        if not sel:
            return None
        return sel[0]

    # =========================================================================
    # APPEARANCE EVENT HANDLERS
    # =========================================================================

    def _on_layout_change(self):
        """Handle layout radio change — set dimensions to layout-appropriate defaults."""
        if self._updating:
            return
        layout = self._app_vars['layout'].get()
        self._updating = True
        try:
            if layout == 'compact':
                self._app_vars['width'].set('220')
                self._app_vars['height'].set('40')
            else:
                self._app_vars['width'].set('220')
                self._app_vars['height'].set('120')
        finally:
            self._updating = False
        self._on_app_change()

    def _on_app_change(self, *args):
        """Handle any appearance setting change."""
        if self._updating:
            return
        new_settings = self._collect_appearance_settings()
        if new_settings is None:
            return
        self._appearance = new_settings
        self._update_preview()
        self._update_layout_state()
        if self._on_appearance_change:
            self._on_appearance_change(new_settings)

    def _update_layout_state(self):
        """Enable/disable right column based on layout — compact has no presets."""
        if not hasattr(self, '_col1_frame'):
            return
        is_compact = self._app_vars.get('layout', tk.StringVar()).get() == 'compact'
        state = 'disabled' if is_compact else 'normal'
        for child in self._col1_frame.winfo_children():
            self._set_state_recursive(child, state)

    def _set_state_recursive(self, widget, state):
        """Recursively set state on all children that support it."""
        try:
            widget.configure(state=state)
        except (tk.TclError, AttributeError):
            pass
        for child in widget.winfo_children():
            self._set_state_recursive(child, state)

    def _on_app_color(self, color_key, hex_color):
        """Handle panel/text color swatch pick."""
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
                'layout': self._app_vars['layout'].get(),
                'width': int(self._app_vars['width'].get()),
                'height': int(self._app_vars['height'].get()),
                'font_size': int(self._app_vars['font_size'].get()),
                'phase_font_size': int(self._app_vars['phase_font_size'].get()),
                'bg_opacity': int(self._app_vars['bg_opacity'].get()),
                'border_width': int(self._app_vars['border_width'].get()),
                'corner_radius': int(self._app_vars['corner_radius'].get()),
                'pos_x': int(self._app_vars['pos_x'].get()),
                'pos_y': int(self._app_vars['pos_y'].get()),
                'font_family': 'Arial',
                'shadow_enabled': self._app_vars['shadow_enabled'].get(),
                'shadow_color': self._app_color_vars['shadow'].get(),
                'button_shape': self._app_vars['button_shape'].get(),
                'colors': {
                    'background': self._app_color_vars['background'].get(),
                    'text': self._app_color_vars['text'].get(),
                    'border': self._app_color_vars['border'].get(),
                },
                'button_colors': {
                    'bg': self._app_color_vars['btn_bg'].get(),
                    'border': self._app_color_vars['btn_border'].get(),
                    'hover': self._app_color_vars['btn_hover'].get(),
                    'start': self._app_color_vars['btn_start'].get(),
                    'pause': self._app_color_vars['btn_pause'].get(),
                    'stop': self._app_color_vars['btn_stop'].get(),
                    'disabled': self._app_color_vars['btn_disabled'].get(),
                    'preset_active': self._app_color_vars['btn_preset_active'].get(),
                    'preset_inactive': self._app_color_vars['btn_preset_inactive'].get(),
                },
            }
            return validate_appearance(s)
        except (ValueError, tk.TclError, KeyError):
            return None

    def load_appearance(self, settings):
        """Load appearance settings into UI controls."""
        self._appearance = settings
        if not hasattr(self, '_app_vars'):
            return
        old_updating = self._updating
        self._updating = True
        try:
            self._app_vars['layout'].set(settings.get('layout', 'standard'))
            self._app_vars['width'].set(str(settings.get('width', 240)))
            self._app_vars['height'].set(str(settings.get('height', 110)))
            self._app_vars['font_size'].set(str(settings.get('font_size', 28)))
            self._app_vars['phase_font_size'].set(str(settings.get('phase_font_size', 12)))
            self._app_vars['bg_opacity'].set(str(settings.get('bg_opacity', 85)))
            self._app_vars['border_width'].set(str(settings.get('border_width', 2)))
            self._app_vars['corner_radius'].set(str(settings.get('corner_radius', 0)))
            self._app_vars['pos_x'].set(str(settings.get('pos_x', 400)))
            self._app_vars['pos_y'].set(str(settings.get('pos_y', 300)))
            self._app_vars['shadow_enabled'].set(settings.get('shadow_enabled', True))
            self._app_vars['button_shape'].set(settings.get('button_shape', 'rounded'))

            colors = settings.get('colors', {})
            self._app_color_vars['background'].set(colors.get('background', '0D0D0D'))
            self._app_color_vars['text'].set(colors.get('text', 'CCCCCC'))
            self._app_color_vars['border'].set(colors.get('border', '3A3A30'))
            self._app_color_vars['shadow'].set(settings.get('shadow_color', '111111'))

            btn_colors = settings.get('button_colors', {})
            for k in ('bg', 'border', 'hover', 'start', 'pause', 'stop', 'disabled',
                      'preset_active', 'preset_inactive'):
                var_key = f'btn_{k}'
                if var_key in self._app_color_vars:
                    self._app_color_vars[var_key].set(btn_colors.get(k, '000000'))
        finally:
            self._updating = old_updating
        if hasattr(self, 'preview_canvas'):
            self._update_preview()
        self._update_layout_state()

    # =========================================================================
    # SAVE / PUBLIC API
    # =========================================================================

    def _save_and_notify(self):
        """Save preset settings and update preview."""
        save_preset_settings(self.settings_folder, self.preset_settings)
        if hasattr(self, 'preview_canvas'):
            self._update_preview()
        if self._on_preset_change:
            self._on_preset_change()

    def get_preset_settings(self) -> StopwatchPresetSettings:
        """Get current preset settings."""
        return self.preset_settings

    def save_preset_settings(self):
        """Save preset settings to disk."""
        save_preset_settings(self.settings_folder, self.preset_settings)

    def load_preset_data(self, data: dict):
        """Load preset settings from dict."""
        self.preset_settings = StopwatchPresetSettings.from_dict(data)
        while len(self.preset_settings.presets) < MAX_PRESETS:
            self.preset_settings.presets.append(StopwatchPreset())
        self._select_preset(0)
