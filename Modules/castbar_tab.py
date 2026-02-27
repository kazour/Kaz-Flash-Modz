"""
Castbar Tab UI for KzBuilder 3.3.6
Provides GUI for configuring KzCastbars.swf settings with live preview.
"""

import logging
import tkinter as tk
from tkinter import ttk, filedialog
import json
from pathlib import Path

logger = logging.getLogger(__name__)

from ttkbootstrap.dialogs import Messagebox

from .castbar_generator import build_castbars, write_hide_xml, remove_hide_xml
from .build_utils import update_script_with_marker, find_compiler
from .castbar_settings import (
    CASTBAR_DEFAULTS,
    CASTBAR_FONTS,
    STYLE_COLOR_MULT,
    STYLE_COLOR_OFFS,
    get_default_settings,
    validate_all_settings,
    validate_color,
)
from .ui_helpers import (
    FONT_SMALL_BOLD, FONT_SMALL, THEME_COLORS, TK_COLORS,
    create_tip_bar, create_profile_info_bar, BTN_MEDIUM, add_tooltip,
    ColorSwatch,
)


class CastbarTab(ttk.Frame):
    """Castbar customization tab for KzBuilder."""

    # Preview bar dimensions (pixels on canvas)
    PREVIEW_BAR_W = 250
    PREVIEW_BAR_H = 24
    PREVIEW_PADDING = 20

    def __init__(self, parent, settings_path: str, game_path_var=None, assets_path=None):
        super().__init__(parent)

        self.settings_path = Path(settings_path)
        self.settings_file = self.settings_path / "castbar_settings.json"
        self.game_path_var = game_path_var
        if assets_path is not None:
            self.assets_path = Path(assets_path) / "castbars"
        else:
            self.assets_path = Path(__file__).parent.parent / "assets" / "castbars"

        # Current settings
        self.settings = get_default_settings()

        # Tkinter variables
        self.vars = {}
        self.color_swatches = {}

        # Info bar labels
        self.profile_label = tk.StringVar(value="No profile loaded")
        self.castbar_count_label = tk.StringVar(value="0 / 2 castbars")

        # Art images (loaded later) — dict keyed by style number
        self._frame_pil = {}    # {style: PIL.Image}
        self._frame_tk = {}     # {style: PhotoImage}
        self._color_pil = {}    # {style: PIL.Image}
        self._color_tk = {}     # {style: PhotoImage}
        self._bar_dims = {}     # {style: (width, height)}

        self._load_settings()
        self._create_widgets()
        self._load_to_ui()

        # Secret style activation (Ctrl+Shift+G activates hidden Style 6)
        self.bind_all('<Control-Shift-G>', self._activate_secret_style)
        self.bind_all('<Control-Shift-g>', self._activate_secret_style)

    # =========================================================================
    # UI Construction
    # =========================================================================

    def _create_widgets(self):
        """Create the two-panel layout."""
        # === BUTTONS (top bar) ===
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill='x', padx=10, pady=(5, 5))

        ttk.Button(btn_frame, text="Reset All", command=self._reset_all, width=BTN_MEDIUM).pack(side='left', padx=2)

        self.build_status = ttk.Label(
            btn_frame, text="",
            font=FONT_SMALL, foreground=THEME_COLORS['muted']
        )
        self.build_status.pack(side='left', padx=(10, 0))

        ttk.Button(btn_frame, text="Build", command=self._build, width=BTN_MEDIUM).pack(side='right', padx=2)
        ttk.Button(btn_frame, text="Export...", command=self._export_settings, width=BTN_MEDIUM).pack(side='right', padx=2)
        ttk.Button(btn_frame, text="Import...", command=self._import_settings, width=BTN_MEDIUM).pack(side='right', padx=2)

        # === TIP BAR + INFO BAR ===
        create_tip_bar(self, "Customize player/target casting bars. Preview updates live as you change settings.")

        create_profile_info_bar(self, self.profile_label,
                               extra_labels=[self.castbar_count_label])

        # === MAIN CONTENT: two-panel grid ===
        main_frame = ttk.Frame(self)
        main_frame.pack(fill='both', expand=True, padx=10, pady=5)

        # Left panel: Preview / style selector (fixed width)
        left_panel = ttk.LabelFrame(main_frame, text="Preview — click to select style")
        left_panel.configure(padding=5)
        left_panel.grid(row=0, column=0, sticky='ns', padx=(0, 10))

        self._create_preview_panel(left_panel)

        # Right panel: Settings (expands to fill available width)
        right_panel = ttk.Frame(main_frame)
        right_panel.grid(row=0, column=1, sticky='nsew')

        self._create_settings_panel(right_panel)

        main_frame.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)   # settings expands
        # column 0 has no weight → preview stays at natural width

    def _create_settings_panel(self, parent):
        """Create the settings panel sections."""
        self._create_layout_settings(parent)
        self._create_appearance_settings(parent)

    def _create_layout_settings(self, parent):
        """Create the layout section: style, enable/disable, and positions."""
        layout_frame = ttk.LabelFrame(parent, text="Layout")
        layout_frame.configure(padding=8)
        layout_frame.pack(fill='x', pady=(0, 5))

        # Row 1: Style indicator + Enable checkboxes
        self.vars['bar_style'] = tk.IntVar(value=1)
        row1 = ttk.Frame(layout_frame)
        row1.pack(fill='x', pady=(0, 5))
        ttk.Label(row1, text="Style:", font=FONT_SMALL_BOLD).pack(side='left')
        self._style_label = ttk.Label(row1, text="Style 1",
                                       font=FONT_SMALL_BOLD,
                                       foreground=THEME_COLORS['accent'])
        self._style_label.pack(side='left', padx=(4, 0))
        ttk.Separator(row1, orient='vertical').pack(side='left', fill='y', padx=10, pady=2)
        self.vars['enable_player'] = tk.BooleanVar(value=True)
        player_cb = ttk.Checkbutton(row1, text="Player",
                        variable=self.vars['enable_player'],
                        command=self._on_setting_changed,
                        bootstyle="success-round-toggle")
        player_cb.pack(side='left', padx=(0, 6))
        add_tooltip(player_cb, "Show a custom castbar for your own casts")
        self.vars['enable_target'] = tk.BooleanVar(value=True)
        target_cb = ttk.Checkbutton(row1, text="Target",
                        variable=self.vars['enable_target'],
                        command=self._on_setting_changed,
                        bootstyle="success-round-toggle")
        target_cb.pack(side='left')
        add_tooltip(target_cb, "Show a custom castbar for your target's casts")

        # Row 2: Player position
        row2 = ttk.Frame(layout_frame)
        row2.pack(fill='x', pady=(0, 2))
        ttk.Label(row2, text="Player:", font=FONT_SMALL_BOLD).pack(side='left')
        self._create_spinbox(row2, "X:", "player_x", 0, 2560, side='left')
        self._create_spinbox(row2, "Y:", "player_y", 0, 1440, side='left')

        # Row 3: Target position
        row3 = ttk.Frame(layout_frame)
        row3.pack(fill='x', pady=(0, 5))
        ttk.Label(row3, text="Target:", font=FONT_SMALL_BOLD).pack(side='left')
        self._create_spinbox(row3, "X:", "target_x", 0, 2560, side='left')
        self._create_spinbox(row3, "Y:", "target_y", 0, 1440, side='left')

        # Row 4: Hide default game castbar
        self.vars['hide_default'] = tk.BooleanVar(value=False)
        hide_row = ttk.Frame(layout_frame)
        hide_row.pack(fill='x')
        hide_cb = ttk.Checkbutton(hide_row, text="Hide default game castbar",
                        variable=self.vars['hide_default'],
                        command=self._on_setting_changed,
                        bootstyle="success-round-toggle")
        hide_cb.pack(side='left')
        add_tooltip(hide_cb, "Hides the built-in AoC castbar so only KzCastbars shows")
        ttk.Label(hide_row, text="(writes CommandTimerBar.xml)",
                  font=FONT_SMALL, foreground=THEME_COLORS['muted']).pack(side='left', padx=(6, 0))

    def _create_appearance_settings(self, parent):
        """Create the appearance section: bar colors and all text settings."""
        app_frame = ttk.LabelFrame(parent, text="Appearance")
        app_frame.configure(padding=8)
        app_frame.pack(fill='x', pady=(0, 5))

        # --- Bar Color ---
        ttk.Label(app_frame, text="Bar Color:", font=FONT_SMALL_BOLD).pack(anchor='w')

        color_row = ttk.Frame(app_frame)
        color_row.pack(fill='x', pady=(2, 0))
        self._create_color_inline(color_row, "Player", "player_color", "9C6025")
        self._link_colors = tk.BooleanVar(value=False)
        self._link_btn = tk.Button(
            color_row, text="\U0001F513", font=FONT_SMALL,
            relief='flat', bg=TK_COLORS['input_bg'], activebackground=TK_COLORS['border'],
            cursor='hand2', bd=0, padx=2, pady=0,
            command=self._toggle_link_colors)
        self._link_btn.pack(side='left', padx=(4, 4))
        self._create_color_inline(color_row, "Target", "target_color", "9C6025")

        # --- Separator ---
        ttk.Separator(app_frame, orient='horizontal').pack(fill='x', pady=(8, 6))

        # --- Spell Name ---
        ttk.Label(app_frame, text="Spell Name:", font=FONT_SMALL_BOLD).pack(anchor='w')

        sp_row1 = ttk.Frame(app_frame)
        sp_row1.pack(fill='x', pady=(2, 0))
        ttk.Label(sp_row1, text="Font:").pack(side='left')
        self.vars['spell_font'] = tk.StringVar(value="Arial")
        sp_font_cb = ttk.Combobox(sp_row1, textvariable=self.vars['spell_font'],
                                  values=CASTBAR_FONTS, state='readonly', width=8)
        sp_font_cb.pack(side='left', padx=(0, 5))
        sp_font_cb.bind('<<ComboboxSelected>>', lambda e: self._on_setting_changed())
        self._create_spinbox(sp_row1, "Size:", "spell_font_size", 8, 24, side='left')
        self.vars['spell_bold'] = tk.BooleanVar(value=True)
        ttk.Checkbutton(sp_row1, text="Bold",
                        variable=self.vars['spell_bold'],
                        command=self._on_setting_changed,
                        bootstyle="success-round-toggle").pack(side='left')
        ttk.Separator(sp_row1, orient='vertical').pack(side='left', fill='y', padx=8, pady=2)
        ttk.Label(sp_row1, text="Align:").pack(side='left')
        self.vars['spell_align'] = tk.StringVar(value="left")
        ttk.Radiobutton(sp_row1, text="Left", variable=self.vars['spell_align'],
                        value="left", command=self._on_setting_changed).pack(side='left')
        ttk.Radiobutton(sp_row1, text="Center", variable=self.vars['spell_align'],
                        value="center", command=self._on_setting_changed).pack(side='left')

        sp_row2 = ttk.Frame(app_frame)
        sp_row2.pack(fill='x', pady=(2, 0))
        self._create_color_inline(sp_row2, "Color:", "spell_color", "9F9F9F")
        ttk.Separator(sp_row2, orient='vertical').pack(side='left', fill='y', padx=8, pady=2)
        self._create_spinbox(sp_row2, "X:", "spell_x", -200, 200, side='left')
        self._create_spinbox(sp_row2, "Y:", "spell_y", -100, 100, side='left')

        # --- Separator ---
        ttk.Separator(app_frame, orient='horizontal').pack(fill='x', pady=(8, 6))

        # --- Timer ---
        row_timer_hdr = ttk.Frame(app_frame)
        row_timer_hdr.pack(fill='x')
        ttk.Label(row_timer_hdr, text="Timer:", font=FONT_SMALL_BOLD).pack(side='left')
        ttk.Separator(row_timer_hdr, orient='vertical').pack(side='left', fill='y', padx=8, pady=2)
        self.vars['show_timer'] = tk.BooleanVar(value=True)
        ttk.Checkbutton(row_timer_hdr, text="Show Timer",
                        variable=self.vars['show_timer'],
                        command=self._on_setting_changed,
                        bootstyle="success-round-toggle").pack(side='left', padx=(0, 6))
        self.vars['show_estimate'] = tk.BooleanVar(value=True)
        ttk.Checkbutton(row_timer_hdr, text="Show Estimate",
                        variable=self.vars['show_estimate'],
                        command=self._on_setting_changed,
                        bootstyle="success-round-toggle").pack(side='left')

        tm_row1 = ttk.Frame(app_frame)
        tm_row1.pack(fill='x', pady=(2, 0))
        ttk.Label(tm_row1, text="Font:").pack(side='left')
        self.vars['timer_font'] = tk.StringVar(value="Arial")
        tm_font_cb = ttk.Combobox(tm_row1, textvariable=self.vars['timer_font'],
                                  values=CASTBAR_FONTS, state='readonly', width=8)
        tm_font_cb.pack(side='left', padx=(0, 5))
        tm_font_cb.bind('<<ComboboxSelected>>', lambda e: self._on_setting_changed())
        self._create_spinbox(tm_row1, "Size:", "timer_font_size", 8, 24, side='left')
        self.vars['timer_bold'] = tk.BooleanVar(value=True)
        ttk.Checkbutton(tm_row1, text="Bold",
                        variable=self.vars['timer_bold'],
                        command=self._on_setting_changed,
                        bootstyle="success-round-toggle").pack(side='left')

        tm_row2 = ttk.Frame(app_frame)
        tm_row2.pack(fill='x', pady=(2, 0))
        self._create_color_inline(tm_row2, "Color:", "timer_color", "9F9F9F")
        ttk.Separator(tm_row2, orient='vertical').pack(side='left', fill='y', padx=8, pady=2)
        self._create_spinbox(tm_row2, "X:", "timer_x", -200, 200, side='left')
        self._create_spinbox(tm_row2, "Y:", "timer_y", -100, 100, side='left')

    def _create_color_inline(self, parent, label, key, default_hex):
        """Create an inline color picker (label + entry + swatch) without creating a new row."""
        ttk.Label(parent, text=label).pack(side='left')

        self.vars[key] = tk.StringVar(value=default_hex)

        entry = ttk.Entry(parent, textvariable=self.vars[key], width=7)
        entry.pack(side='left', padx=(2, 2))
        entry.bind('<FocusOut>', lambda e, k=key: self._on_color_entry_changed(k))
        entry.bind('<Return>', lambda e, k=key: self._on_color_entry_changed(k))

        swatch = ColorSwatch(parent, color_var=self.vars[key],
                             on_change=lambda c, k=key: self._on_swatch_pick(k, c))
        swatch.pack(side='left')
        self.color_swatches[key] = swatch

    def _create_spinbox(self, parent, label, key, from_val, to_val, side='left'):
        """Create a labeled spinbox for an integer setting."""
        frame = ttk.Frame(parent)
        frame.pack(side=side, padx=(0, 10))

        ttk.Label(frame, text=label).pack(side='left')

        self.vars[key] = tk.IntVar(value=CASTBAR_DEFAULTS.get(key, 0))
        sb = ttk.Spinbox(frame, from_=from_val, to=to_val, width=6,
                         textvariable=self.vars[key],
                         command=self._on_setting_changed)
        sb.pack(side='left')
        sb.bind('<FocusOut>', lambda e: self._on_setting_changed())
        sb.bind('<Return>', lambda e: self._on_setting_changed())

    # =========================================================================
    # Preview Canvas
    # =========================================================================

    def _create_preview_panel(self, parent):
        """Create the live preview canvas."""
        # 6 style sections × (label + 2 bars + spacing) + separators + padding
        canvas_h = (self.PREVIEW_BAR_H * 2 + 60) * 6 + self.PREVIEW_PADDING * 3
        self.preview_canvas = tk.Canvas(parent, bg=TK_COLORS['bg'], highlightthickness=0,
                                        width=290, height=canvas_h)
        self.preview_canvas.pack(fill='y', expand=True)

        # Click regions for style selection {style_num: (y_top, y_bottom)}
        self._style_regions = {}

        # Try to load art images
        self._load_art_images()

        # Clickable style selection + hover cursor
        self.preview_canvas.bind('<Button-1>', self._on_preview_click)
        self.preview_canvas.bind('<Motion>', self._on_preview_motion)

        # Initial draw
        self._update_preview()

    def _load_art_images(self):
        """Load bar art PNGs for all styles if available."""
        try:
            from PIL import Image, ImageTk
            art_path = self.assets_path / "art"

            for style in range(1, 7):
                frame_path = art_path / f"frame{style}.png"
                color_path = art_path / f"color{style}.png"

                if frame_path.exists():
                    img = Image.open(frame_path)
                    self._frame_pil[style] = img
                    self._frame_tk[style] = ImageTk.PhotoImage(img)
                    self._bar_dims[style] = (img.width, img.height)
                    if style == 1:
                        self.PREVIEW_BAR_W = img.width
                        self.PREVIEW_BAR_H = img.height

                if color_path.exists():
                    img = Image.open(color_path)
                    self._color_pil[style] = img
                    self._color_tk[style] = ImageTk.PhotoImage(img)

        except ImportError:
            pass
        except (OSError, ValueError) as e:
            logger.warning("Could not load castbar color previews: %s", e)

    def _tint_color_pil(self, style, hex_color, clip_width=None):
        """Apply per-channel ColorTransform tint (matches Flash exactly). Returns PIL Image."""
        try:
            from PIL import Image

            pil_img = self._color_pil.get(style)
            if pil_img is None:
                return None

            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)

            mult = STYLE_COLOR_MULT.get(style, 1.0)
            offs = STYLE_COLOR_OFFS.get(style, 0)

            img = pil_img.convert('RGBA')
            w, h = img.size

            # Per-channel ColorTransform (matches Flash's ColorTransform exactly)
            # Flash formula: newChannel = oldChannel * (userColor/255 * styleMult) + (userColor/255 * styleOffs)
            r_ch, g_ch, b_ch, alpha = img.split()

            result = Image.merge('RGBA', (
                r_ch.point(lambda x: max(0, min(255, int(x * mult * r / 255 + offs * r / 255)))),
                g_ch.point(lambda x: max(0, min(255, int(x * mult * g / 255 + offs * g / 255)))),
                b_ch.point(lambda x: max(0, min(255, int(x * mult * b / 255 + offs * b / 255)))),
                alpha
            ))

            # Clip to progress width
            if clip_width is not None and clip_width < w:
                cropped = Image.new('RGBA', (w, h), (0, 0, 0, 0))
                cropped.paste(result.crop((0, 0, min(clip_width, w), h)), (0, 0))
                result = cropped

            return result
        except Exception:
            return None

    def _build_bar_image(self, style, hex_color, progress):
        """Composite frame + tinted color via PIL alpha blending. Returns PhotoImage."""
        try:
            from PIL import Image, ImageTk

            frame_pil = self._frame_pil.get(style)
            if frame_pil is None:
                return None

            frame = frame_pil.convert('RGBA')
            w, h = frame.size
            fill_w = int(w * progress)

            composited = frame.copy()

            tinted = self._tint_color_pil(style, hex_color, clip_width=fill_w)
            if tinted:
                # Style 6 has a +3px color offset
                if style == 6:
                    offset_img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
                    offset_img.paste(tinted, (3, 0))
                    tinted = offset_img

                composited = Image.alpha_composite(composited, tinted)

            return ImageTk.PhotoImage(composited)
        except Exception:
            return None

    def _get_preview_values(self):
        """Read current UI values for preview rendering. Returns dict or None on error."""
        try:
            return {
                'bar_style': self.vars.get('bar_style', tk.IntVar(value=1)).get(),
                'p_color': validate_color(self.vars.get('player_color', tk.StringVar(value='00FF00')).get()),
                't_color': validate_color(self.vars.get('target_color', tk.StringVar(value='FF6600')).get()),
                'text_cfg': {
                    'spell_font': self.vars.get('spell_font', tk.StringVar(value='Arial')).get(),
                    'spell_size': self.vars.get('spell_font_size', tk.IntVar(value=12)).get(),
                    'spell_bold': self.vars.get('spell_bold', tk.BooleanVar(value=True)).get(),
                    'spell_color': validate_color(self.vars.get('spell_color', tk.StringVar(value='FFFFFF')).get()),
                    'spell_align': self.vars.get('spell_align', tk.StringVar(value='left')).get(),
                    'timer_font': self.vars.get('timer_font', tk.StringVar(value='Arial')).get(),
                    'timer_size': self.vars.get('timer_font_size', tk.IntVar(value=12)).get(),
                    'timer_bold': self.vars.get('timer_bold', tk.BooleanVar(value=True)).get(),
                    'timer_color': validate_color(self.vars.get('timer_color', tk.StringVar(value='FFFFFF')).get()),
                    'spell_x': self.vars.get('spell_x', tk.IntVar(value=0)).get(),
                    'spell_y': self.vars.get('spell_y', tk.IntVar(value=0)).get(),
                    'timer_x': self.vars.get('timer_x', tk.IntVar(value=0)).get(),
                    'timer_y': self.vars.get('timer_y', tk.IntVar(value=0)).get(),
                },
                'show_timer': self.vars.get('show_timer', tk.BooleanVar(value=True)).get(),
                'show_est': self.vars.get('show_estimate', tk.BooleanVar(value=True)).get(),
                'enable_p': self.vars.get('enable_player', tk.BooleanVar(value=True)).get(),
                'enable_t': self.vars.get('enable_target', tk.BooleanVar(value=True)).get(),
            }
        except (tk.TclError, ValueError):
            return None

    def _draw_style_section(self, c, pad, y, style_num, vals, dims, canvas_w, is_last):
        """Draw one style section on the preview canvas. Returns new y position."""
        selected = (vals['bar_style'] == style_num)
        bar_w, bar_h = dims[style_num]
        timer_est = ("2.3/5.0" if vals['show_est'] else "2.3") if vals['show_timer'] else ""
        section_top = y

        # Style label
        label_color = '#FFFFFF' if selected else '#666666'
        marker = " \u25C0" if selected else ""
        c.create_text(pad, y, text="Style " + str(style_num) + marker,
                      fill=label_color, anchor='nw', font=FONT_SMALL_BOLD)
        y += 18

        # Player bar row
        if vals['enable_p']:
            spell = "Overcome the Odds" if selected else ""
            timer = timer_est if selected else ""
            self._draw_bar(c, pad, y, bar_w, bar_h, vals['p_color'],
                           spell, timer, vals['text_cfg'], progress=0.6, style=style_num)
        else:
            c.create_text(pad, y + bar_h // 2, text="Player Bar (disabled)",
                          fill='#555555', anchor='w', font=FONT_SMALL)
        y += bar_h + 6

        # Target bar row
        if vals['enable_t']:
            if selected:
                target_timer = ("1.8/3.0" if vals['show_est'] else "1.8") if vals['show_timer'] else ""
                self._draw_bar(c, pad, y, bar_w, bar_h, vals['t_color'],
                               "Time Fades Away", target_timer,
                               vals['text_cfg'], progress=0.4, style=style_num)
            else:
                self._draw_bar(c, pad, y, bar_w, bar_h, vals['t_color'],
                               "", "", vals['text_cfg'], progress=0.4, style=style_num)
        else:
            c.create_text(pad, y + bar_h // 2, text="Target Bar (disabled)",
                          fill='#555555', anchor='w', font=FONT_SMALL)
        y += bar_h + 4

        # Selection border
        if selected:
            c.create_rectangle(pad - 4, section_top - 2, pad + bar_w + 4, y,
                               outline='#4488FF', width=1)
        y += 8

        # Record clickable region for this style
        self._style_regions[style_num] = (section_top, y)

        # Separator after each section except the last
        if not is_last:
            c.create_line(pad, y, canvas_w - pad, y, fill=TK_COLORS['border'], dash=(3, 3))
            y += 12

        return y

    def _update_preview(self):
        """Redraw the preview canvas with current settings."""
        c = self.preview_canvas
        c.delete('all')
        self._preview_refs = []
        self._style_regions = {}

        vals = self._get_preview_values()
        if vals is None:
            return

        pad = self.PREVIEW_PADDING

        c.update_idletasks()
        canvas_w = c.winfo_width()
        if canvas_w < 50:
            canvas_w = 400

        default_dims = (self.PREVIEW_BAR_W, self.PREVIEW_BAR_H)
        dims = {s: self._bar_dims.get(s, default_dims) for s in range(1, 7)}

        # Style 6 only shown if selected via Ctrl+Shift+G
        visible_styles = [1, 2, 3, 4, 5]
        if vals['bar_style'] == 6:
            visible_styles = visible_styles + [6]

        y = pad
        for i, style_num in enumerate(visible_styles):
            is_last = (i == len(visible_styles) - 1)
            y = self._draw_style_section(c, pad, y, style_num, vals, dims, canvas_w, is_last)

    def _draw_bar(self, canvas, x, y, w, h, hex_color, spell_text, timer_text,
                  text_cfg, progress, style=1):
        """Draw a single castbar preview.

        text_cfg keys: spell_font, spell_size, spell_bold, spell_color, spell_align,
                       timer_font, timer_size, timer_bold, timer_color,
                       spell_x, spell_y, timer_x, timer_y
        """
        if not hasattr(self, '_preview_refs'):
            self._preview_refs = []

        drawn = False
        bar_img = self._build_bar_image(style, hex_color, progress)
        if bar_img is not None:
            self._preview_refs.append(bar_img)
            canvas.create_image(x, y, image=bar_img, anchor='nw')
            drawn = True

        if not drawn:
            fill_w = int(w * progress)
            canvas.create_rectangle(x, y, x + w, y + h, fill=TK_COLORS['input_bg'], outline=TK_COLORS['border'], width=2)
            if fill_w > 0:
                canvas.create_rectangle(x + 2, y + 2, x + fill_w - 2, y + h - 2,
                                        fill='#' + hex_color, outline='')

        # Flash renders fmt.size as pixels (1pt=1px), but Tkinter positive
        # sizes are points (12pt=16px at 96 DPI). Use negative size for pixels.
        sp_weight = 'bold' if text_cfg['spell_bold'] else ''
        tm_weight = 'bold' if text_cfg['timer_bold'] else ''
        spell_font = (text_cfg['spell_font'], -text_cfg['spell_size'], sp_weight)
        timer_font = (text_cfg['timer_font'], -text_cfg['timer_size'], tm_weight)

        # Spell name text — centered or left-aligned
        text_cy = y + (h // 2) + text_cfg['spell_y']
        if text_cfg['spell_align'] == "center":
            text_cx = x + (w // 2) + text_cfg['spell_x']
            text_anchor = 'center'
        else:
            text_cx = x + text_cfg['spell_x'] + 2
            text_anchor = 'w'
        canvas.create_text(text_cx + 1, text_cy + 1, text=spell_text, fill='black',
                           anchor=text_anchor, font=spell_font)
        canvas.create_text(text_cx, text_cy, text=spell_text, fill='#' + text_cfg['spell_color'],
                           anchor=text_anchor, font=spell_font)

        # Timer text — right-aligned
        timer_cx = x + text_cfg['timer_x'] + w - 2
        timer_cy = y + (h // 2) + text_cfg['timer_y']
        canvas.create_text(timer_cx + 1, timer_cy + 1, text=timer_text, fill='black',
                           anchor='e', font=timer_font)
        canvas.create_text(timer_cx, timer_cy, text=timer_text, fill='#' + text_cfg['timer_color'],
                           anchor='e', font=timer_font)

    # =========================================================================
    # Event Handlers
    # =========================================================================

    def _on_setting_changed(self, *args):
        """Called when any setting changes — update preview, style label, and castbar count."""
        self._update_preview()
        self._style_label.configure(text=f"Style {self.vars['bar_style'].get()}")
        self._update_castbar_count()

    def _update_castbar_count(self):
        """Update the castbar count label based on enabled bars."""
        count = 0
        if self.vars.get('enable_player') and self.vars['enable_player'].get():
            count += 1
        if self.vars.get('enable_target') and self.vars['enable_target'].get():
            count += 1
        self.castbar_count_label.set(f"{count} / 2 castbars")

    def _on_preview_click(self, event):
        """Select a bar style by clicking on its preview section."""
        for style_num, (y_top, y_bottom) in self._style_regions.items():
            if y_top <= event.y <= y_bottom:
                self.vars['bar_style'].set(style_num)
                self._on_setting_changed()
                return

    def _on_preview_motion(self, event):
        """Change cursor to hand when hovering over a clickable style region."""
        for y_top, y_bottom in self._style_regions.values():
            if y_top <= event.y <= y_bottom:
                self.preview_canvas.configure(cursor='hand2')
                return
        self.preview_canvas.configure(cursor='')

    def _activate_secret_style(self, event=None):
        """Activate hidden Style 6 (secret style)."""
        self.vars['bar_style'].set(6)
        self._on_setting_changed()
        return "break"

    def _toggle_link_colors(self):
        """Toggle color linking and update padlock icon. Syncs target to player when locking."""
        linked = not self._link_colors.get()
        self._link_colors.set(linked)
        self._link_btn.config(text="\U0001F512" if linked else "\U0001F513")
        if linked:
            player_color = validate_color(self.vars['player_color'].get())
            self.vars['target_color'].set(player_color)
            self._update_swatch('target_color')
            self._update_preview()

    def _linked_color_key(self, key):
        """Return the other color key if colors are linked, else None."""
        if not self._link_colors.get():
            return None
        if key == 'player_color':
            return 'target_color'
        if key == 'target_color':
            return 'player_color'
        return None

    def _on_color_entry_changed(self, key):
        """Called when a color hex entry loses focus."""
        val = self.vars[key].get()
        validated = validate_color(val)
        self.vars[key].set(validated)
        self._update_swatch(key)
        other = self._linked_color_key(key)
        if other:
            self.vars[other].set(validated)
            self._update_swatch(other)
        self._update_preview()

    def _on_swatch_pick(self, key, hex_color):
        """Called when user picks a color from the ColorSwatch dialog."""
        hex_val = hex_color.lstrip('#').upper()
        self.vars[key].set(hex_val)
        other = self._linked_color_key(key)
        if other:
            self.vars[other].set(hex_val)
        self._update_preview()

    def _update_swatch(self, key):
        """Update a color swatch display."""
        if key in self.color_swatches:
            swatch = self.color_swatches[key]
            hex_val = validate_color(self.vars[key].get())
            if hasattr(swatch, 'set_color'):
                swatch.set_color(hex_val)
            else:
                swatch.delete('all')
                swatch.create_rectangle(0, 0, 26, 20, fill='#' + hex_val, outline='')

    def _export_settings(self):
        """Export castbar settings to a JSON file."""
        path = filedialog.asksaveasfilename(
            title="Export Castbar Profile",
            defaultextension=".json",
            initialfile="Cb_",
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
        """Import castbar settings from a JSON file."""
        path = filedialog.askopenfilename(
            title="Import Castbar Profile",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if path:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.settings = validate_all_settings(data)
                self._load_to_ui()
            except Exception as e:
                Messagebox.show_error(str(e), title="Import Error")

    def _reset_all(self):
        """Reset all settings to defaults (button handler)."""
        self.reset_to_defaults()

    def reset_to_defaults(self):
        """Reset all settings to defaults."""
        self.settings = get_default_settings()
        self._load_to_ui()

    # =========================================================================
    # Settings Persistence
    # =========================================================================

    def _load_settings(self):
        """Load settings from persistent file."""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.settings = validate_all_settings(data)
            except Exception:
                self.settings = get_default_settings()
        else:
            self.settings = get_default_settings()

        # Reset secret style on startup (Style 6 must be activated via Ctrl+Shift+G)
        if self.settings.get("bar_style") == 6:
            self.settings["bar_style"] = 1

    def save_settings(self):
        """Save current UI state to persistent file."""
        self._save_from_ui()
        try:
            self.settings_path.mkdir(parents=True, exist_ok=True)
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            Messagebox.show_error(f"Failed to save castbar settings:\n{e}", title="Save Error")

    def _build(self):
        """Build KzCastbars.swf."""
        game_path = self.game_path_var.get() if self.game_path_var else ""
        if not game_path:
            Messagebox.show_error(
                "Game path not set.\n\nSet the game path on the Welcome screen first.",
                title="Error"
            )
            return

        compiler_path = find_compiler(self.assets_path.parent, Path(__file__).parent.parent)
        flash_path = Path(game_path) / "Data" / "Gui" / "Default" / "Flash"
        output_path = flash_path / "KzCastbars.swf"

        if not (self.assets_path / "base.swf").exists():
            Messagebox.show_error(
                f"Castbar base.swf not found:\n{self.assets_path / 'base.swf'}",
                title="Missing base.swf"
            )
            return
        if compiler_path is None:
            Messagebox.show_error(
                "MTASC compiler not found.\nCheck that 'compiler/mtasc.exe' exists.",
                title="Compiler Not Found"
            )
            return

        self.save_settings()
        settings = self.get_profile_data()

        flash_path.mkdir(parents=True, exist_ok=True)

        self.build_status.config(text="Building...", foreground=THEME_COLORS['warning'])
        self.update()

        success, message = build_castbars(
            str(self.assets_path), str(output_path), settings, str(compiler_path)
        )

        if success:
            # Side effect: hide default castbar if enabled
            if settings.get('hide_default', False):
                write_hide_xml(game_path)
            else:
                remove_hide_xml(game_path)
            # Update auto_login script
            scripts_path = Path(game_path) / "Data" / "Gui" / "Default" / "Scripts"
            update_script_with_marker(
                scripts_path / "auto_login",
                "# KzCastbars auto-load",
                "/unloadclip KzCastbars.swf\n/delay 100\n/loadclip KzCastbars.swf"
            )
            self.build_status.config(text="Build successful!", foreground=THEME_COLORS['success'])
            Messagebox.show_info(
                f"{message}\n\nIn-game: /reloadui",
                title="Build Complete"
            )
        else:
            self.build_status.config(text="Build failed", foreground=THEME_COLORS['danger'])
            Messagebox.show_error(message, title="Build Failed")

    def _load_to_ui(self):
        """Load settings dict into UI widgets."""
        for key, value in self.settings.items():
            if key in self.vars:
                try:
                    self.vars[key].set(value)
                except tk.TclError:
                    pass

        # Update color swatches
        for key in ('player_color', 'target_color', 'spell_color', 'timer_color'):
            self._update_swatch(key)

        # Clear cached tinted images
        if hasattr(self, '_preview_refs'):
            self._preview_refs.clear()

        self._update_preview()
        self._update_castbar_count()

    def _save_from_ui(self):
        """Read UI widgets into settings dict."""
        for key in self.settings:
            if key in self.vars:
                try:
                    self.settings[key] = self.vars[key].get()
                except tk.TclError:
                    pass
        self.settings = validate_all_settings(self.settings)

    def get_profile_data(self) -> dict:
        """Return current settings as dict (for profile save)."""
        self._save_from_ui()
        return dict(self.settings)

    def load_profile_data(self, config: dict):
        """Load settings from a profile dict."""
        if config:
            self.settings = validate_all_settings(config)
            # Reset secret style (Style 6 must be activated via Ctrl+Shift+G)
            if self.settings.get("bar_style") == 6:
                self.settings["bar_style"] = 1
            self._load_to_ui()

    def set_profile_name(self, name):
        """Update the profile indicator label."""
        self.profile_label.set(name)
