"""
Kaz Flash Modz v3.3.4
Multi-module SWF mod builder for Age of Conan.
Builds KzGrids, KzCastbars, KzTimers, KzStopwatch, and DamageInfo.
"""

import ttkbootstrap as ttb
import tkinter as tk
from tkinter import ttk, filedialog
from ttkbootstrap.dialogs import Messagebox
import json
import sys
import shutil
import tempfile
from pathlib import Path

# Import database editor module
from Modules.database_editor import BuffDatabase, DatabaseEditorTab

# Import DamageInfo modules
from Modules.damageinfo_tab import DamageInfoTab
from Modules.damageinfo_generator import build_damageinfo
from Modules.damageinfo_xml import generate_textcolors_xml

# Import Castbar modules
from Modules.castbar_tab import CastbarTab
from Modules.castbar_generator import build_castbars, write_hide_xml, remove_hide_xml

# Import Timers modules
from Modules.timers_tab import TimersTab
from Modules.live_tracker_tab import LiveTrackerTab
from Modules.stopwatch_tab import StopwatchTab
from Modules.stopwatch_generator import build_stopwatch

# Import Grids modules
from Modules.grids_tab import GridsTab, MAX_TOTAL_SLOTS
from Modules.grids_generator import build_grids
from Modules.build_utils import find_compiler, strip_marker_block, update_script_with_marker
from Modules.ui_helpers import (
    init_settings, disable_mousewheel_on_inputs, setup_custom_styles,
    restore_window_position, bind_window_position_save,
    FONT_TITLE, FONT_SECTION, FONT_BODY, FONT_SMALL_BOLD, FONT_SMALL,
    THEME_COLORS, TK_COLORS, apply_dark_titlebar,
    PAD_TAB, PAD_INNER, BTN_MEDIUM, BTN_LARGE,
    MODULE_COLORS, add_tooltip, bind_card_events,
)

APP_NAME = "Kaz Flash Modz"
APP_VERSION = "3.3.4"
SETTINGS_FILE = "kzbuilder_settings.json"
PROFILES_DIR = "profiles"

# ============================================================================
# SETTINGS MANAGER
# ============================================================================
class SettingsManager:
    def __init__(self, filepath):
        self.filepath = Path(filepath)
        self.data = {}
        self.load()

    def load(self):
        if self.filepath.exists():
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            except (json.JSONDecodeError, IOError, OSError) as e:
                print(f"Warning: Could not load settings from {self.filepath}: {e}")
                self.data = {}

    def save(self):
        try:
            self.filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value


# ============================================================================
# MAIN APPLICATION
# ============================================================================
class KzBuilder(ttb.Window):
    def __init__(self):
        super().__init__(themename="darkly")
        self.withdraw()  # Hide during setup to prevent position jump
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.minsize(1000, 900)
        self.resizable(False, False)
        apply_dark_titlebar(self)

        # Handle both script and PyInstaller frozen executable
        if getattr(sys, 'frozen', False):
            self.app_path = Path(sys.executable).parent
        else:
            self.app_path = Path(__file__).parent
        self.profiles_path = self.app_path / PROFILES_DIR
        self.profiles_path.mkdir(exist_ok=True)
        self.settings_path = self.app_path / "settings"
        self.settings_path.mkdir(exist_ok=True)
        self.assets_path = self.app_path / "assets"
        self.assets_path.mkdir(exist_ok=True)
        self._compiler_path = None

        self.settings = SettingsManager(self.settings_path / SETTINGS_FILE)
        init_settings(self.settings)
        setup_custom_styles(self)
        disable_mousewheel_on_inputs(self)

        self.database = BuffDatabase()
        self.db_path = None

        db_path = self.assets_path / "kzgrids" / "Database.json"
        if db_path.exists():
            self.database.load(db_path)
            self.db_path = db_path
        if self.db_path is None:
            self.db_path = self.assets_path / "kzgrids" / "Database.json"

        self.current_profile = None
        self.modified = False

        self.create_widgets()
        restore_window_position(self, 'main_window', 1000, 900, resizable=False)
        bind_window_position_save(self, 'main_window', save_size=False)

        last_profile = self.settings.get('last_profile')
        if last_profile and Path(last_profile).exists():
            self.load_profile(last_profile)

        self.deiconify()  # Show window at correct position

        # First launch: ask for game directory
        if not self.game_path.get():
            self.after(100, self._show_first_launch_dialog)

    def create_widgets(self):
        # Build menu bar (hidden by default, shown on Alt press)
        self._menubar = tk.Menu(self)

        file_menu = tk.Menu(self._menubar, tearoff=0)
        self._menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Profile", command=self.new_profile)
        file_menu.add_command(label="Load Profile...", command=self.open_profile, accelerator="Ctrl+O")
        file_menu.add_command(label="Save Profile", command=self.save_profile, accelerator="Ctrl+S")
        file_menu.add_command(label="Save Profile As...", command=self.save_profile_as, accelerator="Ctrl+Shift+S")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_close)

        # Menu starts hidden; Alt toggles it
        self._menu_visible = False
        self.bind('<Alt_L>', self._toggle_menu)
        self.bind('<Alt_R>', self._toggle_menu)

        self.bind_all('<Control-o>', lambda e: self.open_profile())
        self.bind_all('<Control-s>', lambda e: self.save_profile())
        self.bind_all('<Control-Shift-S>', lambda e: self.save_profile_as())

        # Create game_path early (used by multiple tabs)
        self.game_path = tk.StringVar(value=self.settings.get('game_path', ''))

        # Module enable flags
        self.build_grids_var = tk.BooleanVar(value=True)
        self.build_castbars_var = tk.BooleanVar(value=True)
        self.build_timers_var = tk.BooleanVar(value=True)
        self.build_damageinfo_var = tk.BooleanVar(value=True)
        self.build_stopwatch_var = tk.BooleanVar(value=True)

        # Build-related state (was on Build tab, now global)
        self.status_var = tk.StringVar(value="Ready")
        self.restore_castbar_var = tk.BooleanVar(value=False)
        self.restore_textcolors_var = tk.BooleanVar(value=False)

        # Global status bar (packed before notebook so it stays at bottom)
        status_bar = ttk.Label(self, textvariable=self.status_var, style='StatusBar.TLabel')
        status_bar.pack(fill='x', side='bottom')
        # Thin separator line above status bar
        sep = tk.Canvas(self, height=1, highlightthickness=0)
        sep.pack(fill='x', side='bottom')
        from Modules.ui_helpers import fill_canvas_solid
        fill_canvas_solid(sep, '#333333')

        # Notebook fills remaining space
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)

        # === TAB ORDER (v3.2.0) ===

        # === TAB: Welcome ===
        self._create_welcome_tab()

        # === TAB: Grids ===
        self.grids_tab = GridsTab(
            self.notebook,
            database=self.database,
            app_version=APP_VERSION,
            profiles_path=self.profiles_path,
            on_modified=self._mark_modified,
            on_open_database=self._open_database_window,
            status_var=self.status_var,
            game_path_var=self.game_path,
            assets_path=self.assets_path
        )
        self.notebook.add(self.grids_tab, text="  Grids  ")

        # === TAB: Castbars ===
        self.castbar_tab = CastbarTab(self.notebook, str(self.settings_path), self.game_path, assets_path=self.assets_path)
        self.notebook.add(self.castbar_tab, text="  Castbars  ")

        # === TAB: Timers ===
        self.timers_tab = TimersTab(self.notebook, self.settings, assets_path=self.assets_path, database=self.database, on_open_database=self._open_database_window)
        self.notebook.add(self.timers_tab, text="  Timers  ")

        # === TAB: Stopwatch === (NEW in v3.2.0)
        self.stopwatch_tab = StopwatchTab(
            self.notebook,
            settings_folder=str(self.settings_path),
            game_path_var=self.game_path,
            assets_path=self.assets_path
        )
        self.notebook.add(self.stopwatch_tab, text="  Stopwatch  ")

        # === TAB: DamageNumbers ===
        self.damageinfo_tab = DamageInfoTab(self.notebook, str(self.settings_path), self.game_path, assets_path=self.assets_path)
        self.notebook.add(self.damageinfo_tab, text="  DamageNumbers  ")

        # Live Tracker — independent window, launched from Welcome tab
        self._live_tracker_settings = {}
        self._live_tracker_window = None
        self.live_tracker_tab = None

        # === Database editor (child window, not a tab) ===
        self.db_editor = None
        self._db_window = None

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _create_welcome_tab(self):
        """Create the Welcome tab — dashboard with module cards and quick start."""
        welcome_tab = ttk.Frame(self.notebook)
        self.notebook.add(welcome_tab, text="  Welcome  ")

        # --- Header ---
        header_frame = ttk.Frame(welcome_tab)
        header_frame.pack(fill='x', padx=15, pady=(15, 10))

        title_row = ttk.Frame(header_frame)
        title_row.pack(fill='x')
        ttk.Label(title_row, text="Kaz Flash Modz",
                  font=FONT_TITLE).pack(side='left')
        ttk.Label(title_row, text=f"v{APP_VERSION}",
                  font=FONT_SMALL_BOLD, foreground=THEME_COLORS['accent']).pack(side='left', padx=(8, 0), anchor='s', pady=(0, 4))

        ttk.Label(header_frame, text="Age of Conan UI Mod Suite",
                  font=('Segoe UI', 10), foreground=THEME_COLORS['body']).pack(anchor='w')

        # --- Bottom section (packed from bottom first to guarantee visibility) ---
        bottom_frame = ttk.Frame(welcome_tab)
        bottom_frame.pack(side='bottom', fill='x', padx=15, pady=(0, 10))

        # Game path
        qs_frame = ttk.LabelFrame(bottom_frame, text="Quick Start")
        qs_frame.configure(padding=PAD_INNER)
        qs_frame.pack(fill='x')

        path_row = ttk.Frame(qs_frame)
        path_row.pack(fill='x')
        ttk.Label(path_row, text="Game Path:", font=FONT_SECTION).pack(side='left', padx=(0, 5))
        ttk.Entry(path_row, textvariable=self.game_path).pack(side='left', fill='x', expand=True)
        ttk.Button(path_row, text="Browse...", command=self.browse_game,
                   width=BTN_MEDIUM).pack(side='right', padx=(5, 0))

        # Restore options
        restore_frame = ttk.LabelFrame(bottom_frame, text="Restore Options (when module is unchecked)")
        restore_frame.configure(padding=PAD_INNER)
        restore_frame.pack(fill='x', pady=(5, 0))

        self._restore_castbar_cb = ttk.Checkbutton(
            restore_frame, text="Restore castbar XML from backup",
            variable=self.restore_castbar_var, style="success-round-toggle")
        self._restore_castbar_cb.pack(side='left', padx=(0, 20))
        add_tooltip(self._restore_castbar_cb, "Restore CommandTimerBar.xml when KzCastbars is disabled")

        self._restore_textcolors_cb = ttk.Checkbutton(
            restore_frame, text="Restore TextColors from backup",
            variable=self.restore_textcolors_var, style="success-round-toggle")
        self._restore_textcolors_cb.pack(side='left')
        add_tooltip(self._restore_textcolors_cb, "Restore TextColors.xml when DamageInfo is disabled")

        # Build All button
        build_row = ttk.Frame(bottom_frame)
        build_row.pack(fill='x', pady=(5, 0))
        build_btn = ttk.Button(build_row, text="Build & Install All",
                               command=self.build, width=BTN_LARGE)
        build_btn.pack()
        add_tooltip(build_btn, "Compile all enabled modules and install SWFs to your AoC game directory")

        ttk.Label(bottom_frame,
                  text="After building:  /reloadui  >  /reloadgrids   |   Preview: Ctrl+Shift+Alt",
                  font=FONT_SMALL, foreground=THEME_COLORS['muted']).pack(pady=(5, 0))

        # --- Module Cards (3x2 grid, fills remaining space) ---
        cards_frame = ttk.Frame(welcome_tab)
        cards_frame.pack(fill='both', expand=True, padx=15, pady=(0, 10))
        cards_frame.columnconfigure(0, weight=1)
        cards_frame.columnconfigure(1, weight=1)
        cards_frame.columnconfigure(2, weight=1)

        modules = [
            ("KzGrids",     "grids",      "Buff/debuff tracking grids\nwith whitelist filtering",        "KzGrids.swf",     self.build_grids_var,      0, 0),
            ("KzCastbars",  "castbars",   "Custom player/target cast bars\nwith style and color options", "KzCastbars.swf",  self.build_castbars_var,   0, 1),
            ("KzTimers",    "timers",     "Loop timer presets with\ncustomizable panel appearance",      "KzTimers.swf",    self.build_timers_var,     0, 2),
            ("KzStopwatch", "stopwatch",  "Standalone timer panel\nwith custom layout and style",        "KzStopwatch.swf", self.build_stopwatch_var,  1, 0),
            ("DamageInfo",  "damageinfo", "Damage number customization\nwith per-type color and sizing", "DamageInfo.swf",  self.build_damageinfo_var, 1, 1),
        ]

        for name, color_key, desc, swf, var, row, col in modules:
            mod_color = MODULE_COLORS[color_key]
            # Colored border card
            card_border = tk.Frame(cards_frame,
                                   highlightbackground=mod_color,
                                   highlightcolor=mod_color,
                                   highlightthickness=1,
                                   bg=TK_COLORS['bg'])
            card_border.grid(row=row, column=col, padx=5, pady=5, sticky='nsew')

            card = ttk.Frame(card_border)
            card.pack(fill='both', expand=True, padx=10, pady=10)

            # Module name as heading
            ttk.Label(card, text=name, font=FONT_SECTION,
                      foreground=THEME_COLORS['heading']).pack(anchor='w')

            enable_row = ttk.Frame(card)
            enable_row.pack(fill='x', pady=(4, 0))
            cb = ttk.Checkbutton(enable_row, text="Enable", variable=var,
                                 style="success-round-toggle")
            cb.pack(side='left')
            add_tooltip(cb, f"Include {name} in Build & Install All")
            ttk.Label(enable_row, text=swf,
                      font=FONT_SMALL, foreground=THEME_COLORS['muted']).pack(side='right')

            ttk.Label(card, text=desc,
                      font=FONT_BODY, foreground=THEME_COLORS['body']).pack(anchor='w', pady=(4, 0))

            # Hover highlight + click-to-toggle on entire card area
            bind_card_events(card_border, mod_color, var)

        # Live Tracker launcher card (row 1, col 2)
        tracker_color = THEME_COLORS['warning']
        tracker_border = tk.Frame(cards_frame,
                                  highlightbackground=tracker_color,
                                  highlightcolor=tracker_color,
                                  highlightthickness=1,
                                  bg=TK_COLORS['bg'])
        tracker_border.grid(row=1, column=2, padx=5, pady=5, sticky='nsew')

        tracker_card = ttk.Frame(tracker_border)
        tracker_card.pack(fill='both', expand=True, padx=10, pady=10)

        ttk.Label(tracker_card, text="Live Tracker", font=FONT_SECTION,
                  foreground=THEME_COLORS['heading']).pack(anchor='w')

        ttk.Button(tracker_card, text="Open Tracker",
                   command=self._open_live_tracker, width=BTN_MEDIUM).pack(anchor='w', pady=(4, 0))
        ttk.Label(tracker_card, text="Boss timer, combat log\nmonitoring, overlay",
                  font=FONT_BODY, foreground=THEME_COLORS['body']).pack(anchor='w', pady=(4, 0))

        # Hover highlight only (no click-to-toggle — tracker has its own button)
        bind_card_events(tracker_border, tracker_color)

        cards_frame.rowconfigure(0, weight=1)
        cards_frame.rowconfigure(1, weight=1)

        # Wire restore option updates to module checkboxes
        self.build_castbars_var.trace_add('write', self._update_restore_options)
        self.build_damageinfo_var.trace_add('write', self._update_restore_options)
        self._update_restore_options()

    def _update_restore_options(self, *args):
        """Update restore option availability based on module checkboxes."""
        if not hasattr(self, '_restore_castbar_cb'):
            return

        backups = self.settings_path / "backups"

        # Castbar restore
        castbar_backup = (backups / "CommandTimerBar.xml").exists()
        if not self.build_castbars_var.get() and castbar_backup:
            self._restore_castbar_cb.configure(state='normal')
        else:
            self._restore_castbar_cb.configure(state='disabled')
            self.restore_castbar_var.set(False)

        # TextColors restore
        tc_backup = (backups / "TextColors.xml").exists()
        if not self.build_damageinfo_var.get() and tc_backup:
            self._restore_textcolors_cb.configure(state='normal')
        else:
            self._restore_textcolors_cb.configure(state='disabled')
            self.restore_textcolors_var.set(False)

    def _show_first_launch_dialog(self):
        """Show modal dialog asking for game directory on first launch."""
        dialog = tk.Toplevel(self)
        dialog.title("Welcome to Kaz Flash Modz")
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(False, False)
        apply_dark_titlebar(dialog)

        w, h = 500, 310
        x = (dialog.winfo_screenwidth() - w) // 2
        y = (dialog.winfo_screenheight() - h) // 2
        dialog.geometry(f"{w}x{h}+{x}+{y}")

        frame = ttk.Frame(dialog, padding=20)
        frame.pack(fill='both', expand=True)

        ttk.Label(frame, text="Welcome to Kaz Flash Modz!",
                  font=('Segoe UI', 14, 'bold')).pack(pady=(0, 10))
        ttk.Label(frame,
                  text="To get started, select your Age of Conan\ninstallation folder (the main game directory).",
                  font=('Segoe UI', 10), foreground=THEME_COLORS['body']).pack(pady=(0, 15))

        path_frame = ttk.Frame(frame)
        path_frame.pack(fill='x', pady=(0, 15))
        path_var = tk.StringVar()
        ttk.Entry(path_frame, textvariable=path_var, width=50).pack(side='left', fill='x', expand=True)

        def browse():
            path = filedialog.askdirectory(title="Select Age of Conan Folder", parent=dialog)
            if path:
                path_var.set(path)

        ttk.Button(path_frame, text="Browse...", command=browse).pack(side='right', padx=(5, 0))

        # Backup options
        backup_frame = ttk.Frame(frame)
        backup_frame.pack(fill='x', pady=(0, 10))
        ttk.Label(backup_frame, text="Back up your current game customizations:",
                  font=FONT_SMALL_BOLD).pack(anchor='w')
        backup_castbar_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(backup_frame, text="Castbar settings (CommandTimerBar.xml)",
                        variable=backup_castbar_var, style="success-round-toggle").pack(anchor='w', padx=(15, 0))
        backup_textcolors_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(backup_frame, text="Damage number colors (TextColors.xml)",
                        variable=backup_textcolors_var, style="success-round-toggle").pack(anchor='w', padx=(15, 0))

        def confirm():
            path = path_var.get()
            if path and Path(path).is_dir():
                self.game_path.set(path)
                self.settings.set('game_path', path)
                self.settings.save()

                # Create backups if requested
                game = Path(path)
                backups_dir = self.settings_path / "backups"
                not_found = []

                if backup_castbar_var.get():
                    src = game / "Data" / "Gui" / "Customized" / "Views" / "CommandTimerBar.xml"
                    if src.exists():
                        backups_dir.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src, backups_dir / "CommandTimerBar.xml")
                    else:
                        not_found.append("CommandTimerBar.xml")

                if backup_textcolors_var.get():
                    src = game / "Data" / "Gui" / "Customized" / "TextColors.xml"
                    if src.exists():
                        backups_dir.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src, backups_dir / "TextColors.xml")
                    else:
                        not_found.append("TextColors.xml")

                if not_found:
                    Messagebox.show_info(
                        "No custom setup found for:\n  - " + "\n  - ".join(not_found)
                        + "\n\nThis is normal if you haven't customized these files.",
                        title="Backup Info", parent=dialog)

                dialog.destroy()
            elif path:
                Messagebox.show_warning("The selected folder does not exist.", title="Invalid Path", parent=dialog)

        def skip():
            dialog.destroy()

        btn_frame = ttk.Frame(frame)
        btn_frame.pack()
        ttk.Button(btn_frame, text="Continue", command=confirm, width=12).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Skip", command=skip, width=12).pack(side='left', padx=5)

        dialog.protocol("WM_DELETE_WINDOW", skip)
        self.wait_window(dialog)

    def _toggle_menu(self, event=None):
        """Toggle menu bar visibility on Alt key press."""
        if self._menu_visible:
            self.config(menu=None)
            self._menu_visible = False
        else:
            self.config(menu=self._menubar)
            self._menu_visible = True

    def _mark_modified(self):
        self.modified = True

    def _open_database_window(self):
        """Open the Database Editor in a child window."""
        if self._db_window is not None and self._db_window.winfo_exists():
            self._db_window.lift()
            self._db_window.focus_force()
            return

        self._db_window = tk.Toplevel(self)
        self._db_window.withdraw()  # Hide during setup
        self._db_window.title("Kaz Flash Modz - Database Editor")
        self._db_window.geometry("900x600")
        self._db_window.transient(self)
        apply_dark_titlebar(self._db_window)

        self.db_editor = DatabaseEditorTab(self._db_window, self.database, self.assets_path / "kzgrids")
        self.db_editor.pack(fill='both', expand=True)

        restore_window_position(self._db_window, 'database_window', 900, 600, parent=self)
        bind_window_position_save(self._db_window, 'database_window')
        self._db_window.deiconify()

    def _open_live_tracker(self):
        """Open Live Tracker in an independent window."""
        if self._live_tracker_window is not None:
            try:
                if self._live_tracker_window.winfo_exists():
                    self._live_tracker_window.lift()
                    self._live_tracker_window.focus_force()
                    return
            except tk.TclError:
                pass

        self._live_tracker_window = tk.Toplevel(self)
        self._live_tracker_window.withdraw()  # Hide during setup
        self._live_tracker_window.title("Kaz Flash Modz - Live Tracker")
        self._live_tracker_window.geometry("450x400")
        apply_dark_titlebar(self._live_tracker_window)

        self.live_tracker_tab = LiveTrackerTab(
            self._live_tracker_window,
            self.settings,
            assets_path=str(self.assets_path)
        )
        self.live_tracker_tab.pack(fill='both', expand=True)

        # Load saved settings
        if self._live_tracker_settings:
            self.live_tracker_tab.load_profile_data({'overlay': self._live_tracker_settings})

        # Set profile name
        if self.current_profile:
            name = Path(self.current_profile).stem
            self.live_tracker_tab.set_profile_name(f"Profile: {name}")

        # Update log path from current game_path
        self.live_tracker_tab.refresh_log_path()

        # Window position persistence
        restore_window_position(self._live_tracker_window, 'live_tracker_window', 450, 400, parent=self)
        bind_window_position_save(self._live_tracker_window, 'live_tracker_window')

        # Handle window close
        self._live_tracker_window.protocol("WM_DELETE_WINDOW", self._close_live_tracker)
        self._live_tracker_window.deiconify()

    def _close_live_tracker(self):
        """Close Live Tracker window gracefully."""
        if self.live_tracker_tab:
            self._live_tracker_settings = self.live_tracker_tab.get_profile_data().get('overlay', {})
            self.live_tracker_tab.cleanup()
        if self._live_tracker_window:
            self._live_tracker_window.destroy()
            self._live_tracker_window = None
            self.live_tracker_tab = None

    def _set_profile_name_all_tabs(self, name):
        """Update profile name on all tab indicators."""
        self.grids_tab.set_profile_name(name)
        self.castbar_tab.set_profile_name(name)
        self.damageinfo_tab.set_profile_name(name)
        self.timers_tab.set_profile_name(name)
        self.stopwatch_tab.set_profile_name(name)
        if self.live_tracker_tab:
            self.live_tracker_tab.set_profile_name(name)

    def save_all_panels(self):
        errors = []
        tabs = [
            ("Grids", self.grids_tab),
            ("Castbars", self.castbar_tab),
            ("DamageInfo", self.damageinfo_tab),
            ("Timers", self.timers_tab),
            ("Stopwatch", self.stopwatch_tab),
        ]
        for name, tab in tabs:
            try:
                tab.save_settings()
            except Exception as e:
                errors.append(f"{name}: {e}")
        if self.live_tracker_tab:
            try:
                self.live_tracker_tab.save_settings()
            except Exception as e:
                errors.append(f"LiveTracker: {e}")
        if errors:
            Messagebox.show_error(
                f"Some tabs failed to save:\n\n" + "\n".join(errors),
                title="Save Error"
            )

    def new_profile(self):
        if self.modified:
            if Messagebox.yesno("Discard unsaved changes?", title="Unsaved Changes") == "No":
                return
        self.grids_tab.load_profile_data([])
        self.castbar_tab.reset_to_defaults()
        self.damageinfo_tab.reset_to_defaults()
        self.timers_tab.reset_to_defaults()
        self.stopwatch_tab.reset_to_defaults()
        self._live_tracker_settings = {}
        if self.live_tracker_tab:
            self.live_tracker_tab.reset_to_defaults()
        self.build_grids_var.set(True)
        self.build_castbars_var.set(True)
        self.build_timers_var.set(True)
        self.build_damageinfo_var.set(True)
        self.build_stopwatch_var.set(True)
        self.current_profile = None
        self.modified = False
        self._set_profile_name_all_tabs("New profile (unsaved)")

    def open_profile(self):
        path = filedialog.askopenfilename(title="Open Profile", initialdir=str(self.profiles_path),
                                          filetypes=[("JSON", "*.json"), ("All", "*.*")])
        if not path:
            return
        # Parse JSON before discarding anything — if this fails, current state is untouched
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            Messagebox.show_error(f"Failed to read profile:\n{e}", title="Error")
            return
        # Only ask about discarding after we know the file is valid
        if self.modified:
            if Messagebox.yesno("Discard unsaved changes?", title="Unsaved Changes") == "No":
                return
        self._apply_profile(path, data)

    def load_profile(self, path):
        """Load profile from path (used by auto-load on startup)."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            Messagebox.show_error(f"Failed to load profile:\n{e}", title="Error")
            return
        self._apply_profile(path, data)

    def _apply_profile(self, path, data):
        """Apply pre-parsed profile data to all tabs."""
        try:
            self.grids_tab.load_profile_data(data.get('grids', []))
            castbar_config = data.get('castbars', {})
            if castbar_config:
                self.castbar_tab.load_profile_data(castbar_config)
            damageinfo_config = data.get('damageinfo', {})
            if damageinfo_config:
                self.damageinfo_tab.load_profile_data(damageinfo_config)

            timers_config = data.get('timers', {})
            if timers_config:
                self.timers_tab.load_profile_data(timers_config)

            stopwatch_config = data.get('stopwatch', {})
            if stopwatch_config:
                self.stopwatch_tab.load_profile_data(stopwatch_config)

            # Live Tracker (lazy pattern — window may or may not be open)
            live_tracker_config = data.get('live_tracker', {})
            self._live_tracker_settings = live_tracker_config.get('overlay', {})
            if self.live_tracker_tab:
                self.live_tracker_tab.load_profile_data(live_tracker_config)

            # Build flags
            build_config = data.get('build', {})
            if build_config:
                self.build_grids_var.set(build_config.get('grids', True))
                self.build_castbars_var.set(build_config.get('castbars', True))
                self.build_timers_var.set(build_config.get('timers', True))
                self.build_damageinfo_var.set(build_config.get('damageinfo', True))
                self.build_stopwatch_var.set(build_config.get('stopwatch', True))
            self._update_restore_options()

            self._set_profile_name_all_tabs(f"Profile: {Path(path).stem}")
            self.settings.set('last_profile', path)
            self.settings.save()
            self.status_var.set(f"Loaded: {path}")
            self.current_profile = path
            self.modified = False
        except Exception as e:
            Messagebox.show_error(f"Failed to apply profile:\n{e}", title="Error")

    def save_profile(self):
        if self.current_profile:
            self.do_save_profile(self.current_profile)
        else:
            self.save_profile_as()

    def save_profile_as(self):
        path = filedialog.asksaveasfilename(title="Save Profile", initialdir=str(self.profiles_path),
                                            defaultextension=".json", filetypes=[("JSON", "*.json"), ("All", "*.*")])
        if path:
            self.do_save_profile(path)

    def do_save_profile(self, path):
        self.save_all_panels()
        try:
            data = {
                'version': APP_VERSION,
                'grids': self.grids_tab.get_profile_data(),
                'castbars': self.castbar_tab.get_profile_data(),
                'damageinfo': self.damageinfo_tab.get_profile_data(),
                'timers': self.timers_tab.get_profile_data(),
                'stopwatch': self.stopwatch_tab.get_profile_data(),
            }
            # Live Tracker (lazy — use tab if open, else cached settings)
            if self.live_tracker_tab:
                data['live_tracker'] = self.live_tracker_tab.get_profile_data()
            else:
                data['live_tracker'] = {'overlay': self._live_tracker_settings}
            data['build'] = {
                'grids': self.build_grids_var.get(),
                'castbars': self.build_castbars_var.get(),
                'timers': self.build_timers_var.get(),
                'damageinfo': self.build_damageinfo_var.get(),
                'stopwatch': self.build_stopwatch_var.get(),
            }
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            self.current_profile = path
            self.modified = False
            self._set_profile_name_all_tabs(f"Profile: {Path(path).stem}")
            self.settings.set('last_profile', path)
            self.settings.save()
            self.status_var.set(f"Saved: {path}")
        except Exception as e:
            Messagebox.show_error(f"Failed to save profile:\n{e}", title="Error")

    def browse_game(self):
        path = filedialog.askdirectory(title="Select Age of Conan Folder")
        if path:
            self.game_path.set(path)
            self.settings.set('game_path', path)
            self.settings.save()

    def build(self):
        """Orchestrate the full build pipeline."""
        game_path = self._validate_build_prerequisites()
        if not game_path:
            return

        config = self._get_build_configuration(game_path)
        if not config:
            return

        try:
            result = self._execute_builds(game_path, config)
            if result is not None:
                results, cleaned = result
                self._display_build_summary(game_path, config, results, cleaned)
        except Exception as e:
            Messagebox.show_error(
                f"Something went wrong during the build.\n\n"
                f"Your game files may not have been updated.\n\n"
                f"({type(e).__name__}: {e})",
                title="Build Error")
            self.status_var.set("Build failed")

    def _validate_build_prerequisites(self):
        """Validate game path and directory structure. Returns normalized path or None."""
        self.save_all_panels()
        game_path = self.game_path.get()
        if not game_path or not Path(game_path).is_dir():
            Messagebox.show_error("Please select your Age of Conan installation folder", title="Error")
            return None

        game_path = str(Path(game_path).resolve())
        gui_default = Path(game_path) / "Data" / "Gui" / "Default"

        if not gui_default.exists():
            Messagebox.show_error("This doesn't look like an Age of Conan installation.\n"
                                "Expected to find Data\\Gui\\Default folder.", title="Error")
            return None

        # Validate compiler is available before starting any builds
        compiler = find_compiler(self.assets_path, self.app_path)
        if compiler is None:
            Messagebox.show_error(
                "The MTASC compiler was not found.\n\n"
                "It should be in the assets/compiler/ folder.\n"
                "Re-download Kaz Flash Modz if this file is missing.",
                title="Compiler Not Found")
            return None

        self._compiler_path = compiler
        return game_path

    def _get_build_configuration(self, game_path):
        """Determine which modules to build and validate. Returns config dict or None."""
        grids = self.grids_tab.get_profile_data()
        has_grids = len(grids) > 0 and self.build_grids_var.get()
        build_damageinfo = self.build_damageinfo_var.get()
        build_castbars = self.build_castbars_var.get()
        build_timers = self.build_timers_var.get()
        build_stopwatch = self.build_stopwatch_var.get()

        if has_grids:
            total_slots = self.grids_tab.get_total_slots()
            if total_slots > MAX_TOTAL_SLOTS:
                Messagebox.show_error(f"Total slots ({total_slots}) exceeds maximum ({MAX_TOTAL_SLOTS})", title="Error")
                return None

        flash_path = Path(game_path) / "Data" / "Gui" / "Default" / "Flash"
        scripts_path = Path(game_path) / "Scripts"
        total_steps = sum([has_grids, build_damageinfo, build_castbars, build_timers, build_stopwatch]) + 1  # +1 for install

        return {
            'grids': grids, 'has_grids': has_grids,
            'build_damageinfo': build_damageinfo, 'build_castbars': build_castbars,
            'build_timers': build_timers, 'build_stopwatch': build_stopwatch,
            'restore_castbar_xml': self.restore_castbar_var.get(),
            'restore_textcolors_xml': self.restore_textcolors_var.get(),
            'flash_path': flash_path, 'scripts_path': scripts_path,
            'total_steps': total_steps,
        }

    def _execute_builds(self, game_path, config):
        """Run all enabled module builds. Returns (results, cleaned) or None on fatal failure.

        Two-phase approach: compile everything to a staging directory first,
        then install to game directory only if all compilations succeed.
        This prevents partial installs that leave the game in a broken state.
        """
        flash_path = config['flash_path']
        scripts_path = config['scripts_path']
        has_grids = config['has_grids']
        total_steps = config['total_steps']
        current_step = 0

        staging_dir = Path(tempfile.mkdtemp(prefix="kzbuilder_"))
        try:
            # Phase 1: Compile all enabled modules to staging directory
            results = {}

            if has_grids:
                current_step += 1
                self.status_var.set(f"Step {current_step}/{total_steps}: Building KzGrids...")
                self.update()

                compiler = self._compiler_path
                base_swf = self.assets_path / "kzgrids" / "base.swf"
                if not base_swf.exists():
                    base_swf = self.assets_path / "base.swf"
                stubs = self.assets_path / "kzgrids" / "stubs"
                if not stubs.exists():
                    stubs = self.assets_path / "stubs"
                output_swf = staging_dir / "KzGrids.swf"

                kg_success, kg_message = build_grids(
                    config['grids'], self.database, str(base_swf), str(stubs),
                    str(output_swf), str(compiler), APP_VERSION
                )
                results["KzGrids"] = (kg_success, kg_message)

            modules = [
                ("DamageInfo", config['build_damageinfo'], self._compile_damageinfo),
                ("KzCastbars", config['build_castbars'], self._compile_castbars),
                ("KzTimers", config['build_timers'], self._compile_timers),
                ("KzStopwatch", config['build_stopwatch'], self._compile_stopwatch),
            ]

            for name, enabled, compile_fn in modules:
                if not enabled:
                    continue
                current_step += 1
                self.status_var.set(f"Step {current_step}/{total_steps}: Building {name}...")
                self.update()
                success, message = compile_fn(staging_dir)
                results[name] = (success, message)

            # Check for any compilation failures — abort without touching game directory
            failures = {n: msg for n, (s, msg) in results.items() if not s}
            if failures:
                friendly = {
                    "KzGrids": "your buff tracking grids",
                    "KzCastbars": "your in-game castbars",
                    "DamageInfo": "your damage numbers",
                    "KzTimers": "your loop timers",
                    "KzStopwatch": "your stopwatch timer",
                }
                lines = ["Build failed — your game was not modified.\n"]
                for name, msg in failures.items():
                    what = friendly.get(name, name)
                    lines.append(f"{name} could not be built — {what} were not updated.\n({msg})")
                Messagebox.show_error("\n\n".join(lines), title="Build Failed")
                self.status_var.set("Build failed")
                return None

            # Phase 2: All compilations succeeded — install to game directory
            current_step += 1
            self.status_var.set(f"Step {current_step}/{total_steps}: Installing to game directory...")
            self.update()

            flash_path.mkdir(parents=True, exist_ok=True)
            scripts_path.mkdir(parents=True, exist_ok=True)

            # Clean up disabled modules
            cleaned = self._cleanup_disabled_modules(game_path, config)

            # Copy compiled SWFs from staging to game directory
            for swf_file in staging_dir.glob("*.swf"):
                shutil.copy2(swf_file, flash_path / swf_file.name)

            # Module-specific side effects (XML overrides, scripts)
            if config['build_damageinfo']:
                di_ok, di_msg = self._install_damageinfo(game_path)
                if not di_ok:
                    results["DamageInfo"] = (False,
                        f"The mod was installed, but custom text colors could not be applied.\n({di_msg})")

            if config['build_castbars']:
                cb_ok, cb_msg = self._install_castbars(game_path)
                if not cb_ok:
                    results["KzCastbars"] = (False,
                        f"The mod was installed, but some in-game settings could not be applied.\n({cb_msg})")

            # Create/update game scripts
            self._create_scripts(scripts_path, has_grids=has_grids,
                                 build_castbars=config['build_castbars'],
                                 build_timers=config['build_timers'],
                                 build_stopwatch=config['build_stopwatch'])

            return results, cleaned
        finally:
            shutil.rmtree(staging_dir, ignore_errors=True)

    def _display_build_summary(self, game_path, config, results, cleaned):
        """Show build completion summary."""
        has_results = len(results) > 0
        all_ok = all(s for s, _ in results.values()) if has_results else True
        has_warnings = any(not s for s, _ in results.values())

        # Status bar
        if has_results and all_ok:
            self.status_var.set("Build complete! Use /reloadui then /reloadgrids in-game.")
        elif has_warnings:
            self.status_var.set("Build completed with warnings.")
        else:
            self.status_var.set("Cleanup complete.")

        # Build summary text
        if has_results and all_ok:
            summary = "All mods built and installed!\n\n"
        elif has_warnings:
            summary = "Build completed with warnings.\n\n"
        else:
            summary = ""

        # Per-module status
        for name, (success, message) in results.items():
            if success:
                summary += f"  {name} — Updated\n"
            else:
                summary += f"  {name} — Warning: {message}\n"

        # Disabled module cleanup
        if cleaned:
            summary += "\nDisabled mods cleaned up:\n"
            for msg in cleaned:
                summary += f"  - {msg}\n"

        # Reload instructions (only if modules were actually installed)
        if has_results:
            summary += "\nTo apply changes in-game:\n"
            summary += "  1. Type /reloadui in chat\n"
            summary += "  2. Type /reloadgrids in chat\n"
            if config['has_grids']:
                summary += "\nTip: Press Ctrl+Shift+Alt for Preview Mode."

        # Show appropriate dialog
        title = "Build Complete" if all_ok else "Build Complete (with warnings)"
        if all_ok:
            Messagebox.show_info(summary, title=title)
        else:
            Messagebox.show_warning(summary, title=title)

    def _create_scripts(self, scripts_path, has_grids=True, build_castbars=False, build_timers=False, build_stopwatch=False):
        """Create game scripts with loadclip commands for enabled modules."""
        # Build reload content
        parts = []
        if has_grids:
            parts.append("/unloadclip KzGrids.swf\n/delay 100\n/loadclip KzGrids.swf")
        if build_castbars:
            parts.append("/unloadclip KzCastbars.swf\n/delay 100\n/loadclip KzCastbars.swf")
        if build_timers:
            parts.append("/unloadclip KzTimers.swf\n/delay 100\n/loadclip KzTimers.swf")
        if build_stopwatch:
            parts.append("/unloadclip KzStopwatch.swf\n/delay 100\n/loadclip KzStopwatch.swf")

        reload_script = scripts_path / "reloadgrids"
        auto_login_script = scripts_path / "auto_login"

        if not parts:
            # No modules enabled — clean up scripts
            if reload_script.exists():
                reload_script.unlink()
            if auto_login_script.exists():
                content = auto_login_script.read_text(encoding='utf-8')
                content = strip_marker_block(content, "# KzBuilder auto-load")
                if content.strip():
                    auto_login_script.write_text(content, encoding='utf-8')
                else:
                    auto_login_script.unlink()
            return

        reload_content = "\n".join(parts)

        # Write reloadgrids script
        reload_script.write_text(reload_content, encoding='utf-8')

        # Update auto_login script (strip-and-rewrite)
        update_script_with_marker(auto_login_script, "# KzBuilder auto-load",
                                  reload_content)

    def _cleanup_disabled_modules(self, game_path, config):
        """Remove artifacts from previously-built modules that are now disabled."""
        flash_path = config['flash_path']
        cleaned = []

        # KzGrids
        if not config['has_grids']:
            swf = flash_path / "KzGrids.swf"
            if swf.exists():
                swf.unlink()
                cleaned.append("KzGrids: removed KzGrids.swf")

        # KzCastbars
        if not config['build_castbars']:
            swf = flash_path / "KzCastbars.swf"
            if swf.exists():
                swf.unlink()
                cleaned.append("KzCastbars: removed KzCastbars.swf")
            # Restore or remove CommandTimerBar.xml override
            if config.get('restore_castbar_xml'):
                backup_xml = self.settings_path / "backups" / "CommandTimerBar.xml"
                dest = (Path(game_path) / "Data" / "Gui" / "Customized"
                        / "Views" / "CommandTimerBar.xml")
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(backup_xml, dest)
                cleaned.append("KzCastbars: restored CommandTimerBar.xml from backup")
            else:
                remove_hide_xml(game_path)
            # Strip GUI-level auto_login marker
            gui_auto_login = (Path(game_path) / "Data" / "Gui" / "Default"
                              / "Scripts" / "auto_login")
            if gui_auto_login.exists():
                content = gui_auto_login.read_text(encoding='utf-8')
                content = strip_marker_block(content, "# KzCastbars auto-load")
                content = strip_marker_block(content, "# KzGrids auto-load")
                if content.strip():
                    gui_auto_login.write_text(content, encoding='utf-8')
                else:
                    gui_auto_login.unlink()

        # KzTimers
        if not config['build_timers']:
            swf = flash_path / "KzTimers.swf"
            if swf.exists():
                swf.unlink()
                cleaned.append("KzTimers: removed KzTimers.swf")

        # KzStopwatch
        if not config['build_stopwatch']:
            swf = flash_path / "KzStopwatch.swf"
            if swf.exists():
                swf.unlink()
                cleaned.append("KzStopwatch: removed KzStopwatch.swf")

        # DamageInfo — restore original SWF from backup
        if not config['build_damageinfo']:
            swf = flash_path / "DamageInfo.swf"
            backup = self.assets_path / "damageinfo" / "DamageInfo_backup.swf"
            if swf.exists() and backup.exists():
                shutil.copy2(backup, swf)
                cleaned.append("DamageInfo: restored original DamageInfo.swf")
            # Restore or remove TextColors.xml override
            tc_xml = (Path(game_path) / "Data" / "Gui" / "Customized"
                      / "TextColors.xml")
            if config.get('restore_textcolors_xml'):
                backup_xml = self.settings_path / "backups" / "TextColors.xml"
                tc_xml.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(backup_xml, tc_xml)
                cleaned.append("DamageInfo: restored TextColors.xml from backup")
            elif tc_xml.exists():
                tc_xml.unlink()
                cleaned.append("DamageInfo: removed custom TextColors.xml")

        return cleaned

    def _compile_damageinfo(self, staging_dir):
        """Compile DamageInfo.swf to staging directory."""
        self.damageinfo_tab.save_settings()
        global_settings = self.damageinfo_tab.get_global_settings()

        damageinfo_path = self.assets_path / "damageinfo"
        source_path = damageinfo_path / "src" / "__Packages"
        if not source_path.exists():
            source_path = damageinfo_path / "scripts phase 5" / "__Packages"
        backup_swf = damageinfo_path / "DamageInfo_backup.swf"

        compiler = self._compiler_path

        if not source_path.exists():
            return False, f"DamageInfo sources not found:\n{source_path}"
        if not backup_swf.exists():
            return False, f"DamageInfo_backup.swf not found:\n{backup_swf}"
        if not compiler or not compiler.exists():
            return False, "MTASC compiler not found"

        output_swf = staging_dir / "DamageInfo.swf"
        return build_damageinfo(
            str(source_path), str(backup_swf), str(output_swf),
            global_settings, str(compiler)
        )

    def _install_damageinfo(self, game_path):
        """Install DamageInfo side effects (TextColors.xml)."""
        damage_types = self.damageinfo_tab.get_damage_types()

        default_xml = Path(game_path) / "Data" / "Gui" / "Default" / "TextColors.xml"
        customized_path = Path(game_path) / "Data" / "Gui" / "Customized"
        customized_path.mkdir(parents=True, exist_ok=True)
        output_xml = customized_path / "TextColors.xml"

        if not default_xml.exists():
            return False, f"Game's Default TextColors.xml not found:\n{default_xml}"

        xml_success = generate_textcolors_xml(damage_types, str(output_xml), str(default_xml),
                                               assets_path=str(self.assets_path))
        if not xml_success:
            return False, "Failed to generate TextColors.xml"
        return True, str(output_xml)

    def _compile_castbars(self, staging_dir):
        """Compile KzCastbars.swf to staging directory."""
        self.castbar_tab.save_settings()
        settings = self.castbar_tab.get_profile_data()

        castbars_path = self.assets_path / "castbars"
        compiler = self._compiler_path

        if not castbars_path.exists():
            return False, f"Castbars assets not found:\n{castbars_path}"
        if not (castbars_path / "base.swf").exists():
            return False, f"Castbar base.swf not found:\n{castbars_path / 'base.swf'}"
        if not compiler or not compiler.exists():
            return False, "MTASC compiler not found"

        output_swf = staging_dir / "KzCastbars.swf"
        return build_castbars(str(castbars_path), str(output_swf), settings, str(compiler))

    def _install_castbars(self, game_path):
        """Install castbar side effects (XML hiding, auto_login script)."""
        settings = self.castbar_tab.get_profile_data()

        # Handle CommandTimerBar.xml
        if settings.get('hide_default', False):
            xml_success, xml_msg = write_hide_xml(game_path)
            if not xml_success:
                return False, f"Failed to hide default castbar:\n{xml_msg}"
        else:
            remove_hide_xml(game_path)

        # Add to auto_login script (GUI-level)
        gui_auto_login = (Path(game_path) / "Data" / "Gui" / "Default"
                          / "Scripts" / "auto_login")
        update_script_with_marker(gui_auto_login, "# KzCastbars auto-load",
                                  "/unloadclip KzCastbars.swf\n/delay 100\n/loadclip KzCastbars.swf",
                                  old_markers=["# KzGrids auto-load"])
        return True, ""

    def _compile_timers(self, staging_dir):
        """Compile KzTimers.swf to staging directory."""
        settings = self.timers_tab.timer_editor.get_settings()
        appearance = self.timers_tab.appearance_settings

        flash_timer_path = self.assets_path / "flash_timer"
        compiler = self._compiler_path

        base_swf = flash_timer_path / "base.swf"
        if not base_swf.exists():
            return False, f"KzTimers base.swf not found:\n{base_swf}\nSee assets/flash_timer/README.md"
        if not compiler or not compiler.exists():
            return False, "MTASC compiler not found"

        output_swf = staging_dir / "KzTimers.swf"
        from Modules.timers_generator import build_flash_timer
        return build_flash_timer(str(flash_timer_path), str(output_swf), settings, str(compiler),
                                 appearance=appearance)

    def _compile_stopwatch(self, staging_dir):
        """Compile KzStopwatch.swf to staging directory."""
        self.stopwatch_tab.save_settings()
        settings = self.stopwatch_tab.stopwatch_settings
        preset_settings = self.stopwatch_tab.get_preset_settings()

        flash_stopwatch_path = self.assets_path / "flash_stopwatch"
        compiler = self._compiler_path

        if not compiler or not compiler.exists():
            return False, "MTASC compiler not found"

        output_swf = staging_dir / "KzStopwatch.swf"
        return build_stopwatch(str(flash_stopwatch_path), str(output_swf), settings, str(compiler),
                               preset_settings=preset_settings)

    def on_close(self):
        if self.modified:
            result = Messagebox.yesnocancel("Save profile changes before closing?", title="Unsaved Profile")
            if result == "Cancel":
                return
            if result == "Yes":
                self.save_profile()
        if self.db_editor is not None and self.db_editor.is_modified():
            result = Messagebox.yesnocancel("Save database changes before closing?", title="Unsaved Database")
            if result == "Cancel":
                return
            if result == "Yes":
                self.db_editor.save()
        # Clean up tabs
        if self.timers_tab:
            self.timers_tab.cleanup()
        if self.stopwatch_tab:
            self.stopwatch_tab.cleanup()
        # Clean up live tracker window
        if self.live_tracker_tab:
            self.live_tracker_tab.cleanup()
        if self._live_tracker_window:
            try:
                self._live_tracker_window.destroy()
            except tk.TclError:
                pass
        self.destroy()

# ============================================================================
# ENTRY POINT
# ============================================================================
if __name__ == "__main__":
    app = KzBuilder()
    app.mainloop()
