"""
DamageNumber Tab UI for KzBuilder 3.3.5
Provides GUI for customizing DamageInfo.swf settings (global AS2 + per-type XML).
"""

import tkinter as tk
from tkinter import ttk, filedialog
from ttkbootstrap.dialogs import Messagebox
import json
from pathlib import Path

from .ui_helpers import (
    THEME_COLORS, FONT_SMALL,
    create_tip_bar, create_profile_info_bar, BTN_MEDIUM,
    ColorSwatch, create_scrollable_frame,
)
from .damageinfo_settings import (
    GLOBAL_SETTINGS,
    PRESETS,
    PRESET_NAMES,
    get_default_global_settings,
    validate_all_global_settings,
    validate_damageinfo_color
)
from .damageinfo_generator import build_damageinfo
from .damageinfo_xml import (
    DamageType,
    DAMAGE_TYPE_INFO,
    CATEGORY_ORDER,
    get_default_damage_types,
    get_types_by_category,
    get_display_name,
    validate_damage_type,
    damage_type_to_dict,
    dict_to_damage_type,
    parse_textcolors_xml
)


class DamageInfoTab(ttk.Frame):
    """DamageNumber customization tab for KzBuilder."""

    def __init__(self, parent, settings_path: str, game_path_var=None, assets_path=None):
        """
        Initialize DamageNumber tab.

        Args:
            parent: Parent notebook widget
            settings_path: Path to settings folder (will create damageinfo.json there)
            game_path_var: Optional tk.StringVar containing game installation path
            assets_path: Optional path to assets/ directory
        """
        super().__init__(parent)

        self.settings_path = Path(settings_path)
        self.settings_file = self.settings_path / "damageinfo.json"
        self.game_path_var = game_path_var  # For loading from game's Customized folder
        self._assets_path = assets_path

        # Current settings
        self.global_settings = get_default_global_settings()
        self.damage_types = get_default_damage_types()
        self.current_preset = "Default"  # Current preset name

        # Tkinter variables
        self.global_vars = {}      # key -> tk variable
        self.type_vars = {}        # type_name -> {attr -> tk variable}
        self.color_previews = {}   # type_name -> Canvas widget
        self.last_valid_colors = {} # type_name -> last valid 0xRRGGBB string
        self.preset_var = None     # Preset dropdown variable

        # Info bar label
        self.profile_label = tk.StringVar(value="No profile loaded")

        self._load_settings()
        self._create_widgets()
        self._load_to_ui()

    def _create_widgets(self):
        """Create all UI widgets."""
        # === FROZEN TOP: Buttons + Description ===
        # === BUTTONS (top bar) ===
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill='x', padx=10, pady=(5, 5))

        ttk.Button(btn_frame, text="Load from Game", command=self._load_from_game, width=BTN_MEDIUM).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="Reset All", command=self._reset_all, width=BTN_MEDIUM).pack(side='left', padx=2)

        self.build_status = ttk.Label(
            btn_frame, text="",
            font=FONT_SMALL, foreground=THEME_COLORS['muted']
        )
        self.build_status.pack(side='left', padx=(10, 0))

        ttk.Button(btn_frame, text="Build", command=self._build, width=BTN_MEDIUM).pack(side='right', padx=2)
        ttk.Button(btn_frame, text="Export...", command=self._export_colors, width=BTN_MEDIUM).pack(side='right', padx=2)
        ttk.Button(btn_frame, text="Import...", command=self._import_colors, width=BTN_MEDIUM).pack(side='right', padx=2)

        # === TIP BAR + INFO BAR ===
        create_tip_bar(self, "Customize floating damage numbers. Load from Game reads your current setup.")

        create_profile_info_bar(self, self.profile_label)

        # === SCROLLABLE MIDDLE ===
        scroll_container = ttk.Frame(self)
        scroll_container.pack(fill='both', expand=True)

        outer, self.scrollable_frame, self.canvas = create_scrollable_frame(scroll_container)
        outer.pack(fill='both', expand=True)

        # === GLOBAL SETTINGS SECTION ===
        global_frame = ttk.LabelFrame(self.scrollable_frame, text="Global Settings")
        global_frame.configure(padding=10)
        global_frame.pack(fill='x', padx=10, pady=(10, 10))
        self._create_global_settings(global_frame)

        # === PER-TYPE COLORS SECTION ===
        types_frame = ttk.LabelFrame(self.scrollable_frame, text="Per-Type Colors")
        types_frame.configure(padding=10)
        types_frame.pack(fill='x', padx=10, pady=5)
        self._create_type_settings(types_frame)

    def _create_global_settings(self, parent):
        """Create global settings section with clean grid layout."""
        # === STYLE PRESET ===
        preset_row = ttk.Frame(parent)
        preset_row.pack(fill='x', pady=(0, 12))

        ttk.Label(preset_row, text="Animation Style:", width=14, anchor='e').grid(row=0, column=0, sticky='e')
        self.preset_var = tk.StringVar(value=self.current_preset)
        preset_combo = ttk.Combobox(
            preset_row,
            textvariable=self.preset_var,
            values=PRESET_NAMES,
            width=12,
            state='readonly'
        )
        preset_combo.grid(row=0, column=1, padx=(5, 10), sticky='w')
        preset_combo.bind('<<ComboboxSelected>>', self._on_preset_change)
        ttk.Label(preset_row, text="Controls speed, easing, and shadow effects",
                  foreground=THEME_COLORS['muted']).grid(row=0, column=2, sticky='w')

        # Main content frame with 2x2 grid layout for symmetry
        content = ttk.Frame(parent)
        content.pack(fill='x', pady=5)
        content.columnconfigure(0, weight=1)
        content.columnconfigure(1, weight=1)

        # === ROW 0: Floating Numbers | Fixed Columns ===
        # Floating Numbers (top-left)
        float_frame = ttk.LabelFrame(content, text="Floating Numbers")
        float_frame.configure(padding=8)
        float_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 8), pady=(0, 8))
        ttk.Label(float_frame, text="Numbers that float above heads",
                  foreground=THEME_COLORS['muted'], font=FONT_SMALL).pack(anchor='w')

        float_grid = ttk.Frame(float_frame)
        float_grid.pack(fill='x', pady=(5, 0))
        self._create_grid_setting(float_grid, 0, "dir1_x_offset", "X Offset")
        self._create_grid_setting(float_grid, 1, "dir1_y_offset", "Y Offset")

        # Fixed Columns (top-right)
        fixed_frame = ttk.LabelFrame(content, text="Fixed Columns")
        fixed_frame.configure(padding=8)
        fixed_frame.grid(row=0, column=1, sticky='nsew', padx=(8, 0), pady=(0, 8))
        ttk.Label(fixed_frame, text="Numbers at fixed screen positions",
                  foreground=THEME_COLORS['muted'], font=FONT_SMALL).pack(anchor='w')

        col_a_frame = ttk.Frame(fixed_frame)
        col_a_frame.pack(fill='x', pady=(5, 3))
        ttk.Label(col_a_frame, text="Column A:", width=10).pack(side='left')
        self._create_inline_setting(col_a_frame, "fixed_col_x", "X")
        self._create_inline_setting(col_a_frame, "fixed_col_y", "Y")

        col_b_frame = ttk.Frame(fixed_frame)
        col_b_frame.pack(fill='x', pady=(0, 3))
        ttk.Label(col_b_frame, text="Column B:", width=10).pack(side='left')
        self._create_inline_setting(col_b_frame, "col_b_x", "X")
        self._create_inline_setting(col_b_frame, "col_b_y", "Y")

        enable_var = tk.IntVar(value=GLOBAL_SETTINGS["fixed_col_split"]["default"])
        ttk.Checkbutton(col_b_frame, text="Enable", variable=enable_var,
                        bootstyle="success-round-toggle").pack(side='left', padx=(10, 0))
        self.global_vars["fixed_col_split"] = enable_var

        ttk.Label(fixed_frame, text="When enabled, +/- prefixed numbers go to Column B.",
                  foreground=THEME_COLORS['muted'], font=FONT_SMALL).pack(anchor='w', pady=(2, 0))

        # === ROW 1: Static Numbers | Options ===
        # Static Numbers (bottom-left)
        static_frame = ttk.LabelFrame(content, text="Static Numbers")
        static_frame.configure(padding=8)
        static_frame.grid(row=1, column=0, sticky='nsew', padx=(0, 8), pady=(0, 0))
        ttk.Label(static_frame, text="Zig-zag pattern around character",
                  foreground=THEME_COLORS['muted'], font=FONT_SMALL).pack(anchor='w')

        static_grid = ttk.Frame(static_frame)
        static_grid.pack(fill='x', pady=(5, 0))
        self._create_grid_setting(static_grid, 0, "fixed_y_base", "Y Center")
        self._create_grid_setting(static_grid, 1, "fixed_x_offset", "X Spread")
        self._create_grid_setting(static_grid, 2, "fixed_y_spacing", "Spacing")

        # Options (bottom-right)
        options_frame = ttk.LabelFrame(content, text="Options")
        options_frame.configure(padding=8)
        options_frame.grid(row=1, column=1, sticky='nsew', padx=(8, 0), pady=(0, 0))

        titles_var = tk.IntVar(value=GLOBAL_SETTINGS["show_titles"]["default"])
        ttk.Checkbutton(options_frame, text="Show damage type labels",
                        variable=titles_var,
                        bootstyle="success-round-toggle").pack(anchor='w')
        self.global_vars["show_titles"] = titles_var
        ttk.Label(options_frame, text="Display CRITICAL, MANA, STAMINA labels",
                  foreground=THEME_COLORS['muted'], font=FONT_SMALL).pack(anchor='w', padx=(20, 0))

        drain_var = tk.IntVar(value=GLOBAL_SETTINGS["other_resource_loss_to_target"]["default"])
        ttk.Checkbutton(options_frame, text="Split enemy resource drain",
                        variable=drain_var,
                        bootstyle="success-round-toggle").pack(anchor='w', pady=(8, 0))
        self.global_vars["other_resource_loss_to_target"] = drain_var
        ttk.Label(options_frame, text="Separates enemy mana/stamina from yours",
                  foreground=THEME_COLORS['muted'], font=FONT_SMALL).pack(anchor='w', padx=(20, 0))

    def _create_grid_setting(self, parent, row, key, label):
        """Create a setting in grid layout (label + spinbox + unit)."""
        if key not in GLOBAL_SETTINGS:
            return

        meta = GLOBAL_SETTINGS[key]

        ttk.Label(parent, text=label + ":", width=10, anchor='e').grid(row=row, column=0, sticky='e', pady=2)

        if isinstance(meta["default"], float):
            var = tk.DoubleVar(value=meta["default"])
        else:
            var = tk.IntVar(value=meta["default"])

        spinbox = ttk.Spinbox(
            parent,
            textvariable=var,
            from_=meta["min"],
            to=meta["max"],
            increment=meta["step"],
            width=6
        )
        spinbox.grid(row=row, column=1, padx=5, pady=2, sticky='w')
        self.global_vars[key] = var

        if meta.get("unit"):
            ttk.Label(parent, text=meta["unit"], foreground=THEME_COLORS['muted']).grid(row=row, column=2, sticky='w')

    def _create_inline_setting(self, parent, key, label):
        """Create a compact inline setting (label + spinbox)."""
        if key not in GLOBAL_SETTINGS:
            return

        meta = GLOBAL_SETTINGS[key]

        ttk.Label(parent, text=label + ":").pack(side='left', padx=(5, 2))

        if isinstance(meta["default"], float):
            var = tk.DoubleVar(value=meta["default"])
        else:
            var = tk.IntVar(value=meta["default"])

        spinbox = ttk.Spinbox(
            parent,
            textvariable=var,
            from_=meta["min"],
            to=meta["max"],
            increment=meta["step"],
            width=5
        )
        spinbox.pack(side='left')
        self.global_vars[key] = var

        if meta.get("unit"):
            ttk.Label(parent, text=meta["unit"], foreground=THEME_COLORS['muted']).pack(side='left', padx=(0, 5))

    def _on_preset_change(self, event=None):
        """Handle preset dropdown change - apply preset values to hidden settings."""
        preset_name = self.preset_var.get()
        if preset_name not in PRESETS:
            return

        self.current_preset = preset_name
        preset_values = PRESETS[preset_name]

        # Apply preset values to global_settings (for hidden categories)
        for key, value in preset_values.items():
            self.global_settings[key] = value

    def _create_type_settings(self, parent):
        """Create per-type color settings with table-like layout."""
        # Column headers (full width)
        header = ttk.Frame(parent)
        header.pack(fill='x', pady=(0, 2))

        ttk.Label(header, text="Type", width=18, anchor='w',
                  font=('Arial', 9, 'bold')).pack(side='left')
        ttk.Label(header, text="Color", width=14, anchor='center',
                  font=('Arial', 9, 'bold')).pack(side='left')
        ttk.Label(header, text="Size", width=9, anchor='center',
                  font=('Arial', 9, 'bold')).pack(side='left')
        ttk.Label(header, text="Font", width=11, anchor='center',
                  font=('Arial', 9, 'bold')).pack(side='left')
        ttk.Label(header, text="Speed", width=6, anchor='center',
                  font=('Arial', 9, 'bold')).pack(side='left')
        ttk.Label(header, text="Duration", width=8, anchor='center',
                  font=('Arial', 9, 'bold')).pack(side='left')
        ttk.Label(header, text="Dir", width=5, anchor='center',
                  font=('Arial', 9, 'bold')).pack(side='left')

        # Master controls row (full width)
        master_row = ttk.Frame(parent)
        master_row.pack(fill='x', pady=(0, 5))

        ttk.Label(master_row, text="Set All:", width=18, anchor='w',
                  font=('Arial', 8), foreground=THEME_COLORS['body']).pack(side='left')
        # Color spacer
        ttk.Frame(master_row, width=112).pack(side='left')

        size_master = ttk.Combobox(master_row, values=["", "small", "medium", "large"],
                                   width=7, state='readonly')
        size_master.pack(side='left', padx=2)
        size_master.bind('<<ComboboxSelected>>', lambda e: self._apply_master('font_size', size_master.get()))

        font_master = ttk.Combobox(master_row, values=["", "hyborian", "hyborian3"],
                                   width=9, state='readonly')
        font_master.pack(side='left', padx=2)
        font_master.bind('<<ComboboxSelected>>', lambda e: self._apply_master('font_family', font_master.get()))

        speed_master = ttk.Combobox(master_row, values=["", "50", "100", "150", "200"],
                                    width=5, state='readonly')
        speed_master.pack(side='left', padx=2)
        speed_master.bind('<<ComboboxSelected>>', lambda e: self._apply_master('speed', speed_master.get()))

        duration_master = ttk.Combobox(master_row, values=["", "1.0", "2.0", "3.0", "4.0", "5.0"],
                                       width=5, state='readonly')
        duration_master.pack(side='left', padx=2)
        duration_master.bind('<<ComboboxSelected>>', lambda e: self._apply_master('waitonscreen', duration_master.get()))

        dir_master = ttk.Combobox(master_row, values=["", "-1", "0", "1"],
                                  width=3, state='readonly')
        dir_master.pack(side='left', padx=2)
        dir_master.bind('<<ComboboxSelected>>', lambda e: self._apply_master('direction', dir_master.get()))

        # Separator after master controls (full width)
        ttk.Separator(parent, orient='horizontal').pack(fill='x', pady=2)

        # Below separator: table (left) + help box (right)
        main_container = ttk.Frame(parent)
        main_container.pack(fill='both', expand=True)

        # Left side: type rows
        table_frame = ttk.Frame(main_container)
        table_frame.pack(side='left', fill='both', expand=True)

        types_by_cat = get_types_by_category()
        for category in CATEGORY_ORDER:
            if category in types_by_cat and types_by_cat[category]:
                self._create_category_section(table_frame, category, types_by_cat[category])

        # Right side: help box
        self._create_type_help_box(main_container)

    def _create_category_section(self, parent, category: str, type_names: list):
        """Create a section for a category of damage types."""
        # Category label
        cat_label = ttk.Label(parent, text=category, font=('Arial', 9, 'bold'),
                              foreground=THEME_COLORS['heading'])
        cat_label.pack(anchor='w', pady=(8, 2))

        for type_name in type_names:
            self._create_type_row(parent, type_name)

    def _create_type_row(self, parent, type_name: str):
        """Create a row for editing a single damage type."""
        row = ttk.Frame(parent)
        row.pack(fill='x', pady=1)

        # Initialize vars dict for this type
        self.type_vars[type_name] = {}

        # Get current or default values
        dtype = self.damage_types.get(type_name) or DamageType(type_name)

        # Type name label
        display_name = get_display_name(type_name)
        ttk.Label(row, text=display_name, width=18, anchor='w').pack(side='left')

        # Color: Entry + Preview + Picker button
        color_frame = ttk.Frame(row)
        color_frame.pack(side='left')

        color_var = tk.StringVar(value=dtype.color)
        color_entry = ttk.Entry(color_frame, textvariable=color_var, width=10)
        color_entry.pack(side='left')
        self.type_vars[type_name]['color'] = color_var
        self.last_valid_colors[type_name] = dtype.color

        # Validate on focus loss or Enter
        color_entry.bind('<FocusOut>', lambda e, tn=type_name: self._validate_color_entry(tn))
        color_entry.bind('<Return>', lambda e, tn=type_name: self._validate_color_entry(tn))

        # Color swatch (clickable — opens color picker)
        swatch = ColorSwatch(color_frame, color_var=color_var,
                             on_change=lambda c, tn=type_name: self._on_swatch_pick(tn, c))
        swatch.pack(side='left', padx=(2, 0))
        self.color_previews[type_name] = swatch

        # Font size dropdown
        size_var = tk.StringVar(value=dtype.font_size)
        size_combo = ttk.Combobox(row, textvariable=size_var,
                                  values=["small", "medium", "large"],
                                  width=7, state='readonly')
        size_combo.pack(side='left', padx=2)
        self.type_vars[type_name]['font_size'] = size_var

        # Font family dropdown
        family_var = tk.StringVar(value=dtype.font_family)
        family_combo = ttk.Combobox(row, textvariable=family_var,
                                    values=["hyborian", "hyborian3"],
                                    width=9, state='readonly')
        family_combo.pack(side='left', padx=2)
        self.type_vars[type_name]['font_family'] = family_var

        # Speed spinbox
        speed_var = tk.IntVar(value=dtype.speed)
        speed_spin = ttk.Spinbox(row, textvariable=speed_var, from_=1, to=200,
                                 increment=10, width=5)
        speed_spin.pack(side='left', padx=2)
        self.type_vars[type_name]['speed'] = speed_var

        # Duration spinbox
        duration_var = tk.DoubleVar(value=dtype.waitonscreen)
        duration_spin = ttk.Spinbox(row, textvariable=duration_var, from_=0.5, to=10.0,
                                    increment=0.5, width=5)
        duration_spin.pack(side='left', padx=2)
        self.type_vars[type_name]['waitonscreen'] = duration_var

        # Direction dropdown
        dir_var = tk.IntVar(value=dtype.direction)
        dir_combo = ttk.Combobox(row, textvariable=dir_var,
                                 values=[-1, 0, 1], width=3, state='readonly')
        dir_combo.pack(side='left', padx=2)
        self.type_vars[type_name]['direction'] = dir_var

    def _create_type_help_box(self, parent):
        """Create help box on the right side of the type settings table."""
        help_frame = ttk.LabelFrame(parent, text="Column Guide")
        help_frame.configure(padding=10)
        help_frame.pack(side='right', fill='y', padx=(15, 0), anchor='n')

        # Field descriptions
        ttk.Label(help_frame, text="Field Guide",
                  font=('Segoe UI', 9, 'bold'), foreground=THEME_COLORS['heading']).pack(anchor='w')

        ttk.Label(help_frame, text="Speed",
                  font=('Segoe UI', 8, 'bold'), foreground=THEME_COLORS['accent']).pack(anchor='w', pady=(4, 0))
        ttk.Label(help_frame, text="How fast the number moves\nHigher = faster movement",
                  font=FONT_SMALL, foreground=THEME_COLORS['body']).pack(anchor='w', padx=(8, 0))

        ttk.Label(help_frame, text="Duration",
                  font=('Segoe UI', 8, 'bold'), foreground=THEME_COLORS['accent']).pack(anchor='w', pady=(6, 0))
        ttk.Label(help_frame, text="How long number stays visible\nValue in seconds (e.g. 2.0s)",
                  font=FONT_SMALL, foreground=THEME_COLORS['body']).pack(anchor='w', padx=(8, 0))

        ttk.Label(help_frame, text="Dir (Direction)",
                  font=('Segoe UI', 8, 'bold'), foreground=THEME_COLORS['accent']).pack(anchor='w', pady=(6, 0))
        ttk.Label(help_frame, text="-1 = Float down from top",
                  font=FONT_SMALL, foreground=THEME_COLORS['body']).pack(anchor='w', padx=(8, 0))
        ttk.Label(help_frame, text="      \u2192 Column B (if enabled)",
                  font=FONT_SMALL, foreground=THEME_COLORS['body']).pack(anchor='w', padx=(8, 0))
        ttk.Label(help_frame, text=" 0 = Static zig-zag pattern",
                  font=FONT_SMALL, foreground=THEME_COLORS['body']).pack(anchor='w', padx=(8, 0))
        ttk.Label(help_frame, text="+1 = Float up from heads",
                  font=FONT_SMALL, foreground=THEME_COLORS['body']).pack(anchor='w', padx=(8, 0))
        ttk.Label(help_frame, text="      \u2192 Column A",
                  font=FONT_SMALL, foreground=THEME_COLORS['body']).pack(anchor='w', padx=(8, 0))

        # Separator
        ttk.Separator(help_frame, orient='horizontal').pack(fill='x', pady=10)

        # Quick Setup
        ttk.Label(help_frame, text="Quick Setup",
                  font=('Segoe UI', 9, 'bold'), foreground=THEME_COLORS['heading']).pack(anchor='w')
        ttk.Label(help_frame, text="Separate self/heals/resources\nfrom incoming damage:",
                  font=FONT_SMALL, foreground=THEME_COLORS['body']).pack(anchor='w', pady=(4, 0))

        ttk.Label(help_frame, text="\u2022  Self types \u2192 Dir -1",
                  font=FONT_SMALL, foreground=THEME_COLORS['body']).pack(anchor='w', padx=(4, 0), pady=(4, 0))
        ttk.Label(help_frame, text="\u2022  Mana/Stamina lost \u2192 Dir -1",
                  font=FONT_SMALL, foreground=THEME_COLORS['body']).pack(anchor='w', padx=(4, 0))
        ttk.Label(help_frame, text="\u2022  Enemy resources \u2192 split",
                  font=FONT_SMALL, foreground=THEME_COLORS['body']).pack(anchor='w', padx=(4, 0))
        ttk.Label(help_frame, text="\u2022  Column B enabled (X=70)",
                  font=FONT_SMALL, foreground=THEME_COLORS['body']).pack(anchor='w', padx=(4, 0))

        ttk.Button(help_frame, text="Apply Recommended",
                   command=self._apply_recommended_setup, width=18).pack(anchor='w', pady=(8, 0))

    # Recommended per-type values (font_size, font_family, speed, waitonscreen, direction).
    # Colors are intentionally excluded — user keeps their own color choices.
    RECOMMENDED_TYPES = {
        "self_healed":                   ("small", "hyborian", 100, 2.0, -1),
        "other_healed":                  ("small", "hyborian", 100, 2.0, -1),
        "self_healed_critical":          ("large", "hyborian",  80, 3.0, -1),
        "other_healed_critical":         ("large", "hyborian",  80, 3.0, -1),
        "self_attacked":                 ("medium", "hyborian", 100, 2.0, -1),
        "other_attacked":                ("medium", "hyborian", 100, 2.0,  1),
        "self_attacked_unshielded":      ("medium", "hyborian", 100, 2.0, -1),
        "other_attacked_unshielded":     ("medium", "hyborian", 100, 2.0,  1),
        "self_attacked_critical":        ("large", "hyborian",   80, 3.0, -1),
        "other_attacked_critical":       ("large", "hyborian",   50, 3.0,  0),
        "self_attacked_spell":           ("medium", "hyborian", 100, 2.0, -1),
        "other_attacked_spell":          ("medium", "hyborian", 100, 2.0,  1),
        "self_attacked_spell_critical":  ("large", "hyborian",   80, 3.0, -1),
        "other_attacked_spell_critical": ("large", "hyborian",   50, 3.0,  0),
        "self_attacked_combo":           ("medium", "hyborian", 100, 2.0, -1),
        "other_attacked_combo":          ("medium", "hyborian", 100, 2.0,  1),
        "self_attacked_combo_critical":  ("large", "hyborian",   80, 3.0, -1),
        "other_attacked_combo_critical": ("large", "hyborian",   50, 3.0,  0),
        "self_combo_name":               ("small", "hyborian",  100, 3.0, -1),
        "other_combo_name":              ("small", "hyborian",  100, 3.0,  1),
        "self_dodged":                   ("medium", "hyborian",  80, 3.0, -1),
        "other_dodged":                  ("large", "hyborian",   80, 3.0,  1),
        "self_attacked_environment":     ("small", "hyborian",  100, 2.0, -1),
        "other_attacked_environment":    ("small", "hyborian",  100, 2.0,  1),
        "stamina_gained":                ("small", "hyborian",  120, 2.0, -1),
        "stamina_lost":                  ("small", "hyborian",  100, 2.0, -1),
        "mana_gained":                   ("small", "hyborian",  120, 2.0, -1),
        "mana_lost":                     ("small", "hyborian",  100, 2.0, -1),
        "stamina_gained_critical":       ("large", "hyborian",   80, 3.0, -1),
        "mana_gained_critical":          ("large", "hyborian",   80, 3.0, -1),
        "stamina_loss_critical":         ("large", "hyborian",   80, 3.0, -1),
        "mana_loss_critical":            ("large", "hyborian",   80, 3.0, -1),
        "xp_gained":                     ("large", "hyborian",  100, 3.0, -1),
        "murder_points_gained":          ("medium", "hyborian", 100, 2.0, -1),
        "murder_points_gained_murderer": ("medium", "hyborian", 100, 2.0, -1),
    }

    def _apply_recommended_setup(self):
        """Apply recommended type settings (size/font/speed/duration/dir) and global options."""
        changes_made = []

        # 1. Apply recommended per-type values (everything except color)
        fields = ('font_size', 'font_family', 'speed', 'waitonscreen', 'direction')
        types_changed = 0
        for type_name, values in self.RECOMMENDED_TYPES.items():
            vars_dict = self.type_vars.get(type_name, {})
            changed = False
            for key, target in zip(fields, values):
                if key in vars_dict:
                    current = vars_dict[key].get()
                    if current != target:
                        vars_dict[key].set(target)
                        changed = True
            if changed:
                types_changed += 1
        if types_changed > 0:
            changes_made.append(f"Updated {types_changed} damage types")

        # 2. Enable "Split enemy resource drain" if not already
        if "other_resource_loss_to_target" in self.global_vars:
            if self.global_vars["other_resource_loss_to_target"].get() == 0:
                self.global_vars["other_resource_loss_to_target"].set(1)
                changes_made.append("Enabled split enemy resource drain")

        # 3. Enable Column B with X=70 if not already
        if "fixed_col_split" in self.global_vars:
            if self.global_vars["fixed_col_split"].get() == 0:
                self.global_vars["fixed_col_split"].set(1)
                changes_made.append("Enabled Column B")

        if "col_b_x" in self.global_vars:
            current_x = self.global_vars["col_b_x"].get()
            if current_x != 70:
                self.global_vars["col_b_x"].set(70)
                changes_made.append("Set Column B X to 70")

        # Show result
        if changes_made:
            Messagebox.show_info(
                "Changes made:\n\u2022  " + "\n\u2022  ".join(changes_made),
                title="Recommended Setup Applied"
            )
        else:
            Messagebox.show_info(
                "All recommended settings are already applied.",
                title="Already Configured"
            )

    def _update_color_preview(self, type_name: str, color: str):
        """Update the color preview for a damage type."""
        if type_name not in self.color_previews:
            return
        swatch = self.color_previews[type_name]
        if hasattr(swatch, 'set_color'):
            swatch.set_color(color)
        else:
            canvas = swatch
            canvas.delete('all')
            try:
                if color.startswith('0x'):
                    hex_color = '#' + color[2:]
                elif color.startswith('#'):
                    hex_color = color
                else:
                    hex_color = '#' + color
                canvas.create_rectangle(0, 0, 26, 20, fill=hex_color, outline='')
            except (tk.TclError, ValueError):
                canvas.create_rectangle(0, 0, 26, 20, fill='#FFFFFF', outline='')

    def _validate_color_entry(self, type_name: str):
        """Validate color entry on focus loss or Enter. Reverts to last valid color if invalid."""
        if type_name not in self.type_vars:
            return
        raw = self.type_vars[type_name]['color'].get()
        validated = validate_damageinfo_color(raw)
        if validated is not None:
            self.last_valid_colors[type_name] = validated
            self.type_vars[type_name]['color'].set(validated)
        else:
            self.type_vars[type_name]['color'].set(self.last_valid_colors[type_name])

    def _on_color_change(self, type_name: str):
        """Handle color entry change."""
        if type_name not in self.type_vars:
            return
        color = self.type_vars[type_name]['color'].get()
        self._update_color_preview(type_name, color)

    def _on_swatch_pick(self, type_name: str, hex_color: str):
        """Called when user picks a color from ColorSwatch dialog."""
        # Convert #RRGGBB to 0xRRGGBB
        new_color = '0x' + hex_color.lstrip('#').upper()
        self.last_valid_colors[type_name] = new_color
        self.type_vars[type_name]['color'].set(new_color)

    def _apply_master(self, field: str, value: str):
        """Apply a master value to all damage types for a specific field."""
        if not value:
            return
        for type_name, vars_dict in self.type_vars.items():
            if field in vars_dict:
                try:
                    if field == 'speed':
                        vars_dict[field].set(int(value))
                    elif field == 'waitonscreen':
                        vars_dict[field].set(float(value))
                    elif field == 'direction':
                        vars_dict[field].set(int(value))
                    else:
                        vars_dict[field].set(value)
                except (ValueError, tk.TclError):
                    pass

    def _load_settings(self):
        """Load settings from file."""
        if not self.settings_file.exists():
            return

        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Load preset selection
            if 'preset' in data and data['preset'] in PRESETS:
                self.current_preset = data['preset']

            # Load global settings
            if 'global' in data:
                self.global_settings = validate_all_global_settings(data['global'])

            # Load damage types
            if 'types' in data:
                for name, type_data in data['types'].items():
                    if name in DAMAGE_TYPE_INFO:
                        dtype = dict_to_damage_type(type_data)
                        self.damage_types[name] = validate_damage_type(dtype)

        except Exception as e:
            print(f"Error loading DamageInfo settings: {e}")

    def _load_to_ui(self):
        """Load current settings to UI variables."""
        # Preset dropdown
        if self.preset_var:
            self.preset_var.set(self.current_preset)

        # Global settings (visible ones only - hidden are controlled by preset)
        for key, var in self.global_vars.items():
            if key in self.global_settings:
                var.set(self.global_settings[key])

        # Damage types
        for type_name, vars_dict in self.type_vars.items():
            dtype = self.damage_types.get(type_name)
            if dtype:
                if 'color' in vars_dict:
                    vars_dict['color'].set(dtype.color)
                    self._update_color_preview(type_name, dtype.color)
                if 'font_size' in vars_dict:
                    vars_dict['font_size'].set(dtype.font_size)
                if 'font_family' in vars_dict:
                    vars_dict['font_family'].set(dtype.font_family)
                if 'speed' in vars_dict:
                    vars_dict['speed'].set(dtype.speed)
                if 'waitonscreen' in vars_dict:
                    vars_dict['waitonscreen'].set(dtype.waitonscreen)
                if 'direction' in vars_dict:
                    vars_dict['direction'].set(dtype.direction)

    def _get_from_ui(self):
        """Get current values from UI variables."""
        # Global settings
        global_settings = {}
        for key, var in self.global_vars.items():
            try:
                global_settings[key] = var.get()
            except tk.TclError:
                global_settings[key] = GLOBAL_SETTINGS[key]["default"]
        self.global_settings = validate_all_global_settings(global_settings)

        # Damage types
        for type_name, vars_dict in self.type_vars.items():
            try:
                # Get values safely - don't use 'or' which treats 0 as falsy!
                color_val = vars_dict.get('color', tk.StringVar()).get()
                size_val = vars_dict.get('font_size', tk.StringVar()).get()
                family_val = vars_dict.get('font_family', tk.StringVar()).get()
                speed_val = vars_dict.get('speed', tk.IntVar()).get()
                duration_val = vars_dict.get('waitonscreen', tk.DoubleVar()).get()
                direction_val = vars_dict.get('direction', tk.IntVar()).get()

                # Preserve font_style from existing data (no UI control for it)
                existing = self.damage_types.get(type_name)
                existing_style = existing.font_style if existing else "bold"

                dtype = DamageType(
                    name=type_name,
                    color=color_val if color_val else "0xFFFFFF",
                    font_size=size_val if size_val else "small",
                    font_family=family_val if family_val else "hyborian3",
                    font_style=existing_style,
                    speed=speed_val,
                    waitonscreen=duration_val,
                    direction=direction_val,
                )
                self.damage_types[type_name] = validate_damage_type(dtype)
            except Exception as e:
                print(f"Error reading type {type_name}: {e}")

    def _apply_preset(self):
        """Apply current preset values to global_settings hidden fields."""
        if self.preset_var:
            self.current_preset = self.preset_var.get()
        if self.current_preset in PRESETS:
            for key, value in PRESETS[self.current_preset].items():
                self.global_settings[key] = value

    def save_settings(self) -> bool:
        """Save current settings to file."""
        self._get_from_ui()
        self._apply_preset()

        try:
            self.settings_path.mkdir(exist_ok=True)

            data = {
                'preset': self.current_preset,
                'global': self.global_settings,
                'types': {name: damage_type_to_dict(dtype)
                          for name, dtype in self.damage_types.items()}
            }

            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

            return True
        except Exception as e:
            Messagebox.show_error(f"Failed to save settings:\n{e}", title="Error")
            return False

    def _build(self):
        """Build DamageInfo.swf."""
        game_path = self.game_path_var.get() if self.game_path_var else ""
        if not game_path:
            Messagebox.show_error(
                "Game path not set.\n\nSet the game path on the Welcome screen first.",
                title="Error"
            )
            return

        if self._assets_path:
            base_assets = Path(self._assets_path)
        else:
            base_assets = Path(__file__).parent.parent / "assets"

        damageinfo_path = base_assets / "damageinfo"
        source_path = damageinfo_path / "src" / "__Packages"
        if not source_path.exists():
            source_path = damageinfo_path / "scripts phase 5" / "__Packages"
        backup_swf = damageinfo_path / "DamageInfo_backup.swf"
        compiler_path = base_assets / "compiler" / "mtasc.exe"
        flash_path = Path(game_path) / "Data" / "Gui" / "Default" / "Flash"
        output_path = flash_path / "DamageInfo.swf"

        if not source_path.exists():
            Messagebox.show_error(
                f"DamageInfo sources not found:\n{source_path}",
                title="Missing Sources"
            )
            return
        if not backup_swf.exists():
            Messagebox.show_error(
                f"DamageInfo_backup.swf not found:\n{backup_swf}",
                title="Missing Backup SWF"
            )
            return
        if not compiler_path.exists():
            Messagebox.show_error(
                f"MTASC compiler not found:\n{compiler_path}",
                title="Compiler Not Found"
            )
            return

        self.save_settings()
        global_settings = self.get_global_settings()

        flash_path.mkdir(parents=True, exist_ok=True)

        self.build_status.config(text="Building...", foreground=THEME_COLORS['warning'])
        self.update()

        success, message = build_damageinfo(
            str(source_path), str(backup_swf), str(output_path),
            global_settings, str(compiler_path)
        )

        if success:
            # Side effect: generate TextColors.xml
            damage_types = self.get_damage_types()
            default_xml = Path(game_path) / "Data" / "Gui" / "Default" / "TextColors.xml"
            customized_path = Path(game_path) / "Data" / "Gui" / "Customized"
            customized_path.mkdir(parents=True, exist_ok=True)
            output_xml = customized_path / "TextColors.xml"

            if default_xml.exists():
                from .damageinfo_xml import generate_textcolors_xml
                generate_textcolors_xml(
                    damage_types, str(output_xml), str(default_xml),
                    assets_path=str(base_assets)
                )

            self.build_status.config(text="Build successful!", foreground=THEME_COLORS['success'])
            Messagebox.show_info(
                f"{message}\n\nIn-game: /reloadui",
                title="Build Complete"
            )
        else:
            self.build_status.config(text="Build failed", foreground=THEME_COLORS['danger'])
            Messagebox.show_error(message, title="Build Failed")

    def _reset_global(self):
        """Reset global settings to defaults."""
        if Messagebox.yesno("Reset all global settings to defaults?", title="Reset") == "Yes":
            self.global_settings = get_default_global_settings()
            self.current_preset = "Default"
            self._load_to_ui()

    def _reset_colors(self):
        """Reset per-type colors to defaults."""
        if Messagebox.yesno("Reset all per-type settings to defaults?", title="Reset") == "Yes":
            self.damage_types = get_default_damage_types()
            self._load_to_ui()

    def _reset_all(self):
        """Reset all settings to defaults (button handler with prompt)."""
        if Messagebox.yesno("Reset ALL DamageNumber settings to defaults?", title="Reset") == "Yes":
            self.reset_to_defaults()

    def reset_to_defaults(self):
        """Reset all settings to defaults."""
        self.global_settings = get_default_global_settings()
        self.damage_types = get_default_damage_types()
        self.current_preset = "Default"
        self._load_to_ui()

    def _load_from_game(self):
        """Load per-type colors from the game's TextColors.xml."""
        # Check if game path is set
        if not self.game_path_var:
            Messagebox.show_error("Game path not configured.\nSet it on the Welcome screen first.", title="Error")
            return

        game_path = self.game_path_var.get()
        if not game_path:
            Messagebox.show_error("Game path not configured.\nSet it on the Welcome screen first.", title="Error")
            return

        # Check for Customized TextColors.xml first, then Default
        customized_xml = Path(game_path) / "Data" / "Gui" / "Customized" / "TextColors.xml"
        default_xml = Path(game_path) / "Data" / "Gui" / "Default" / "TextColors.xml"

        xml_path = None
        source = ""

        if customized_xml.exists():
            xml_path = customized_xml
            source = "Customized"
        elif default_xml.exists():
            xml_path = default_xml
            source = "Default"

        if not xml_path:
            # No XML found, load defaults
            if Messagebox.yesno(
                "No TextColors.xml found in your game folder.\n\n"
                "Load default settings instead?",
                title="Not Found"
            ) == "Yes":
                self.damage_types = get_default_damage_types()
                self._load_to_ui()
                Messagebox.show_info("Default color settings loaded.", title="Loaded")
            return

        # Parse the XML file
        try:
            loaded_types = parse_textcolors_xml(str(xml_path))

            if not loaded_types:
                Messagebox.show_warning(f"No damage types found in:\n{xml_path}", title="Warning")
                return

            # Update damage types with loaded values
            for name, dtype in loaded_types.items():
                self.damage_types[name] = dtype

            self._load_to_ui()
            Messagebox.show_info(
                f"Loaded {len(loaded_types)} color settings from:\n"
                f"{source}/TextColors.xml",
                title="Loaded"
            )

        except Exception as e:
            Messagebox.show_error(f"Failed to parse TextColors.xml:\n{e}", title="Error")

    def _export_colors(self):
        """Export per-type colors to a JSON file."""
        self._get_from_ui()

        filepath = filedialog.asksaveasfilename(
            title="Export Color Profile",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile="Dn_"
        )

        if not filepath:
            return

        try:
            data = {
                "version": "1.0",
                "description": "KzGrids DamageNumber color profile",
                "types": {name: damage_type_to_dict(dtype)
                          for name, dtype in self.damage_types.items()}
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

            Messagebox.show_info(f"Color profile exported to:\n{filepath}", title="Export")
        except Exception as e:
            Messagebox.show_error(f"Failed to export colors:\n{e}", title="Error")

    def _import_colors(self):
        """Import per-type colors from a JSON file."""
        filepath = filedialog.askopenfilename(
            title="Import Color Profile",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if not filepath:
            return

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if 'types' not in data:
                Messagebox.show_error("Invalid color profile: missing 'types' section", title="Error")
                return

            # Load damage types from file
            imported_count = 0
            for name, type_data in data['types'].items():
                if name in DAMAGE_TYPE_INFO:
                    dtype = dict_to_damage_type(type_data)
                    self.damage_types[name] = validate_damage_type(dtype)
                    imported_count += 1

            self._load_to_ui()
            Messagebox.show_info(f"Imported {imported_count} color settings from:\n{Path(filepath).name}", title="Import")

        except json.JSONDecodeError:
            Messagebox.show_error("Invalid JSON file", title="Error")
        except Exception as e:
            Messagebox.show_error(f"Failed to import colors:\n{e}", title="Error")

    def get_profile_data(self) -> dict:
        """Get full settings dict for embedding in a global profile."""
        self._get_from_ui()
        self._apply_preset()

        return {
            'preset': self.current_preset,
            'global': dict(self.global_settings),
            'types': {name: damage_type_to_dict(dtype)
                      for name, dtype in self.damage_types.items()}
        }

    def load_profile_data(self, config: dict):
        """Load damageinfo settings from a global profile dict."""
        if not config:
            return

        if 'preset' in config and config['preset'] in PRESETS:
            self.current_preset = config['preset']

        if 'global' in config:
            self.global_settings = validate_all_global_settings(config['global'])

        if 'types' in config:
            for name, type_data in config['types'].items():
                if name in DAMAGE_TYPE_INFO:
                    dtype = dict_to_damage_type(type_data)
                    self.damage_types[name] = validate_damage_type(dtype)

        self._load_to_ui()

    def set_profile_name(self, name):
        """Update the profile indicator label."""
        self.profile_label.set(name)

    def get_global_settings(self) -> dict:
        """Get current global settings (from UI, validated, with preset applied)."""
        self._get_from_ui()
        self._apply_preset()
        return self.global_settings

    def get_damage_types(self) -> dict:
        """Get current damage types (from UI, validated)."""
        self._get_from_ui()
        return self.damage_types
