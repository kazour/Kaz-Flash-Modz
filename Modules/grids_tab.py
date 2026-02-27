"""
KzBuilder — Grids Tab Module
Grid configuration UI: add/edit/delete grids, whitelist editing, slot assignment.
"""

import math
import tkinter as tk
from tkinter import ttk, filedialog
import json
from pathlib import Path

from Modules.database_editor import BuffDatabase, format_ids_display
from Modules.grids_generator import build_grids
from Modules.build_utils import update_script_with_marker
from Modules.ui_helpers import (
    restore_window_position, bind_window_position_save,
    get_setting, set_setting,
    FONT_SECTION, FONT_SMALL, FONT_SMALL_BOLD, FONT_BODY, FONT_FORM_LABEL,
    THEME_COLORS, TK_COLORS, style_tk_listbox, style_tk_canvas, apply_dark_titlebar,
    PAD_TAB, PAD_ROW, BTN_SMALL, BTN_MEDIUM, MODULE_COLORS, GRID_TYPE_COLORS,
    create_tip_bar, create_profile_info_bar,
    CollapsibleSection, add_tooltip, create_section_header, fill_canvas_solid, bind_card_events,
    create_scrollable_frame,
)
from ttkbootstrap.dialogs import Messagebox

# ============================================================================
# CONSTANTS
# ============================================================================
MAX_TOTAL_SLOTS = 64
MAX_ROWS = 64
MAX_COLS = 64
SCREEN_MAX_X = 2560
SCREEN_MAX_Y = 1440


# Dialog default sizes (width, height)
ADD_GRID_WIZARD_SIZE = (460, 600)
BUFF_SELECTOR_SIZE = (800, 550)
SLOT_ASSIGNMENT_SIZE = (850, 600)

# ============================================================================
# DEFAULT GRID CONFIGURATION
# ============================================================================
def create_default_grid(grid_type="player", rows=1, cols=10, mode="dynamic", grid_id=None):
    if rows == 1 and cols == 1:
        mode = "static"

    if rows == 1:
        fill_dir = "LR"
    elif cols == 1:
        fill_dir = "BT"
    else:
        fill_dir = "BL-TR"

    return {
        'id': grid_id or f"{grid_type.title()}Grid1",
        'enabled': True,
        'type': grid_type,
        'rows': rows,
        'cols': cols,
        'iconSize': 56,
        'gap': -1,
        'x': 100 if grid_type == "player" else 300,
        'y': 400,
        'slotMode': mode,
        'showTimers': True,
        'timerFontSize': 18,
        'timerFlashThreshold': 6,
        'timerYOffset': 0,
        'enableFlashing': True,
        'fillDirection': fill_dir,
        'sortOrder': 'longest',
        'layout': 'buffFirst' if grid_type == "player" else 'debuffFirst',
        'whitelist': [],
        'slotAssignments': {}
    }

# ============================================================================
# ADD GRID WIZARD
# ============================================================================
class AddGridWizard(tk.Toplevel):
    def __init__(self, parent, existing_ids, current_total_slots):
        super().__init__(parent)
        self.withdraw()
        apply_dark_titlebar(self)
        self.title("Add New Grid")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.existing_ids = existing_ids
        self.current_total_slots = current_total_slots
        self.available_slots = MAX_TOTAL_SLOTS - current_total_slots
        self.result = None
        self.parent = parent

        self.create_widgets()
        restore_window_position(self, 'add_grid_wizard', *ADD_GRID_WIZARD_SIZE, parent, resizable=False)
        bind_window_position_save(self, 'add_grid_wizard', save_size=False)
        self.deiconify()

    def generate_unique_name(self, base="Grid"):
        counter = 1
        while True:
            name = f"{base}{counter}"
            if name not in self.existing_ids:
                return name
            counter += 1

    def create_widgets(self):
        frame = ttk.Frame(self, padding=12)
        frame.pack(fill='both', expand=True)

        # Header
        ttk.Label(frame, text="Create New Grid", font=('Arial', 12, 'bold')).pack(pady=(0, 5))
        self.avail_label = ttk.Label(frame, text=f"Available slots: {self.available_slots} of {MAX_TOTAL_SLOTS}",
                                     foreground=THEME_COLORS['info_value'])
        self.avail_label.pack(pady=(0, 8))

        # Grid Name
        name_frame = ttk.Frame(frame)
        name_frame.pack(fill='x', pady=3)
        ttk.Label(name_frame, text="Grid Name:").pack(side='left')
        self.id_var = tk.StringVar(value=self.generate_unique_name())
        ttk.Entry(name_frame, textvariable=self.id_var, width=20).pack(side='left', padx=5)

        # Source
        source_frame = ttk.LabelFrame(frame, text="Source")
        source_frame.configure(padding=5)
        source_frame.pack(fill='x', pady=5)

        self.type_var = tk.StringVar(value="player")
        ttk.Radiobutton(source_frame, text="Player", variable=self.type_var, value="player").pack(anchor='w')
        ttk.Label(source_frame, text="Track buffs/debuffs on yourself",
                 foreground=THEME_COLORS['muted'], font=FONT_SMALL).pack(anchor='w', padx=18)
        ttk.Radiobutton(source_frame, text="Target", variable=self.type_var, value="target").pack(anchor='w', pady=(3,0))
        ttk.Label(source_frame, text="Track buffs/debuffs on your current target",
                 foreground=THEME_COLORS['muted'], font=FONT_SMALL).pack(anchor='w', padx=18)

        # Mode
        mode_lf = ttk.LabelFrame(frame, text="Mode")
        mode_lf.configure(padding=5)
        mode_lf.pack(fill='x', pady=5)

        self.mode_var = tk.StringVar(value="dynamic")
        self.mode_dynamic = ttk.Radiobutton(mode_lf, text="Dynamic", variable=self.mode_var, value="dynamic")
        self.mode_dynamic.pack(anchor='w')
        ttk.Label(mode_lf, text="Shows all matching buffs from whitelist, auto-sorted",
                 foreground=THEME_COLORS['muted'], font=FONT_SMALL).pack(anchor='w', padx=18)

        self.mode_static = ttk.Radiobutton(mode_lf, text="Static", variable=self.mode_var, value="static")
        self.mode_static.pack(anchor='w', pady=(3,0))
        ttk.Label(mode_lf, text="Fixed slots for specific buffs. Empty when buff not active",
                 foreground=THEME_COLORS['muted'], font=FONT_SMALL).pack(anchor='w', padx=18)

        # Dimensions
        dim_frame = ttk.LabelFrame(frame, text="Dimensions")
        dim_frame.configure(padding=5)
        dim_frame.pack(fill='x', pady=5)

        dim_row = ttk.Frame(dim_frame)
        dim_row.pack(fill='x')

        ttk.Label(dim_row, text="Rows:").pack(side='left')
        self.rows_var = tk.StringVar(value="1")
        self.rows_spin = ttk.Spinbox(dim_row, from_=1, to=self.available_slots,
                                      textvariable=self.rows_var, width=5,
                                      command=self.on_rows_changed)
        self.rows_spin.pack(side='left', padx=(2, 15))
        self.rows_spin.bind('<KeyRelease>', lambda e: self.on_rows_changed())

        ttk.Label(dim_row, text="Columns:").pack(side='left')
        self.cols_var = tk.StringVar(value="10")
        self.cols_spin = ttk.Spinbox(dim_row, from_=1, to=self.available_slots,
                                      textvariable=self.cols_var, width=5,
                                      command=self.on_cols_changed)
        self.cols_spin.pack(side='left', padx=(2, 0))
        self.cols_spin.bind('<KeyRelease>', lambda e: self.on_cols_changed())

        self.shape_var = tk.StringVar(value="")
        ttk.Label(dim_frame, textvariable=self.shape_var, font=FONT_SECTION).pack(pady=(5, 2))

        self.preview_var = tk.StringVar(value="")
        ttk.Label(dim_frame, textvariable=self.preview_var, foreground=THEME_COLORS['muted']).pack()

        # Tips
        ttk.Label(dim_frame, text="H-bar: Rows=1 | V-bar: Columns=1",
                 foreground=THEME_COLORS['muted'], font=FONT_SMALL).pack(anchor='w', pady=(3, 0))

        # Quick Templates (integrated into Dimensions section)
        ttk.Label(dim_frame, text="Quick Templates:", foreground=THEME_COLORS['muted'], font=('Arial', 9)).pack(pady=(8, 2))
        template_frame = ttk.Frame(dim_frame)
        template_frame.pack()

        ttk.Button(template_frame, text="H-bar 1x10", width=11,
                   command=lambda: self.apply_template(1, 10)).pack(side='left', padx=1)
        ttk.Button(template_frame, text="V-bar 10x1", width=11,
                   command=lambda: self.apply_template(10, 1)).pack(side='left', padx=1)
        ttk.Button(template_frame, text="Grid 3x3", width=11,
                   command=lambda: self.apply_template(3, 3)).pack(side='left', padx=1)
        ttk.Button(template_frame, text="Single 1x1", width=11,
                   command=lambda: self.apply_template(1, 1)).pack(side='left', padx=1)

        self.warning_var = tk.StringVar(value="")
        ttk.Label(frame, textvariable=self.warning_var, foreground=THEME_COLORS['danger']).pack(pady=2)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Create", command=self.on_create, width=10).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.on_cancel, width=10).pack(side='left', padx=5)

        self.update_display()

    def apply_template(self, rows, cols):
        total = rows * cols
        if total > self.available_slots:
            if rows == 1:
                cols = self.available_slots
            elif cols == 1:
                rows = self.available_slots
            else:
                scale = math.sqrt(self.available_slots / total)
                rows = max(1, int(rows * scale))
                cols = max(1, int(cols * scale))
        self.rows_var.set(str(rows))
        self.cols_var.set(str(cols))
        # Only force static mode for 1x1
        if rows == 1 and cols == 1:
            self.mode_var.set("static")
        self.update_display()

    def safe_get_int(self, var, default=1):
        try:
            val = var.get().strip()
            if not val:
                return default
            return max(1, int(val))
        except (ValueError, tk.TclError):
            return default

    def _on_dimension_changed(self, changed='rows'):
        """Handle rows or cols spinbox change, clamping the other dimension."""
        rows = self.safe_get_int(self.rows_var, 1)
        cols = self.safe_get_int(self.cols_var, 1)
        if changed == 'rows':
            rows = min(rows, self.available_slots)
            max_other = self.available_slots if rows == 1 else self.available_slots // rows
            if cols > max_other:
                self.cols_var.set(str(max_other))
            self.cols_spin.config(to=max_other)
        else:
            cols = min(cols, self.available_slots)
            max_other = self.available_slots if cols == 1 else self.available_slots // cols
            if rows > max_other:
                self.rows_var.set(str(max_other))
            self.rows_spin.config(to=max_other)
        self.update_display()

    def on_rows_changed(self):
        self._on_dimension_changed('rows')

    def on_cols_changed(self):
        self._on_dimension_changed('cols')

    def update_display(self):
        rows = self.safe_get_int(self.rows_var, 1)
        cols = self.safe_get_int(self.cols_var, 1)
        total = rows * cols

        if rows == 1 and cols == 1:
            shape = "Single Slot"
            self.mode_var.set("static")
            self.mode_dynamic.config(state='disabled')
        elif rows == 1:
            shape = f"Horizontal Bar ({cols} slots)"
            self.mode_dynamic.config(state='normal')
        elif cols == 1:
            shape = f"Vertical Bar ({rows} slots)"
            self.mode_dynamic.config(state='normal')
        else:
            shape = f"Grid ({rows}x{cols} = {total} slots)"
            self.mode_dynamic.config(state='normal')

        self.shape_var.set(shape)
        remaining = self.available_slots - total
        if remaining >= 0:
            self.preview_var.set(f"{remaining} slots would remain after creation")
            self.warning_var.set("")
        else:
            self.preview_var.set("")
            self.warning_var.set(f"Exceeds available slots by {-remaining}!")

    def on_create(self):
        grid_id = self.id_var.get().strip()
        if not grid_id:
            Messagebox.show_error("Grid name is required", title="Error")
            return

        has_special = any(not (c.isalnum() or c == '_' or c == ' ') for c in grid_id)
        if has_special:
            if Messagebox.yesno(
                f"Grid name '{grid_id}' contains special characters.\n"
                "These will be converted to underscores.\nContinue?",
                title="Warning") == "No":
                return

        if grid_id in self.existing_ids:
            Messagebox.show_error(f"Grid name '{grid_id}' already exists", title="Error")
            return

        rows = self.safe_get_int(self.rows_var, 1)
        cols = self.safe_get_int(self.cols_var, 1)
        total = rows * cols

        if total > self.available_slots:
            Messagebox.show_error(f"Only {self.available_slots} slots available.", title="Error")
            return

        self.result = create_default_grid(
            grid_type=self.type_var.get(),
            rows=rows,
            cols=cols,
            mode=self.mode_var.get(),
            grid_id=grid_id
        )
        self.destroy()

    def on_cancel(self):
        self.result = None
        self.destroy()

# ============================================================================
# BUFF SELECTOR DIALOG
# ============================================================================
class BuffSelectorDialog(tk.Toplevel):
    def __init__(self, parent, database, title="Select Buffs", initial_ids=None):
        super().__init__(parent)
        self.withdraw()
        apply_dark_titlebar(self)
        self.title(title)
        self.transient(parent)
        self.grab_set()

        self.database = database
        self.selected_ids = set(initial_ids or [])
        self.result = None

        self.create_widgets()

        last_cat = get_setting('buff_selector_category', 'All')
        last_type = get_setting('buff_selector_type', 'All')
        if last_cat in ["All"] + self.database.categories:
            self.category_var.set(last_cat)
        if last_type in ["All", "Buffs", "Debuffs", "Misc"]:
            self.type_var.set(last_type)

        self.refresh_lists()
        restore_window_position(self, 'buff_selector', *BUFF_SELECTOR_SIZE, parent)
        bind_window_position_save(self, 'buff_selector')
        self.deiconify()

    def save_filter_state(self):
        set_setting('buff_selector_category', self.category_var.get())
        set_setting('buff_selector_type', self.type_var.get())

    def create_widgets(self):
        search_frame = ttk.Frame(self, padding=5)
        search_frame.pack(fill='x')

        ttk.Label(search_frame, text="Search:").pack(side='left')
        self.search_var = tk.StringVar()
        self.search_var.trace_add('write', lambda *a: self.refresh_lists())
        ttk.Entry(search_frame, textvariable=self.search_var, width=20).pack(side='left', padx=5)

        ttk.Label(search_frame, text="Category:").pack(side='left', padx=(10, 0))
        self.category_var = tk.StringVar(value="All")
        cat_combo = ttk.Combobox(search_frame, textvariable=self.category_var,
                                  values=["All"] + self.database.categories, width=18, state='readonly')
        cat_combo.pack(side='left', padx=5)
        cat_combo.bind('<<ComboboxSelected>>', lambda e: self.refresh_lists())

        ttk.Label(search_frame, text="Type:").pack(side='left', padx=(10, 0))
        self.type_var = tk.StringVar(value="All")
        type_combo = ttk.Combobox(search_frame, textvariable=self.type_var,
                                   values=["All", "Buffs", "Debuffs", "Misc"], width=10, state='readonly')
        type_combo.pack(side='left', padx=5)
        type_combo.bind('<<ComboboxSelected>>', lambda e: self.refresh_lists())

        lists_frame = ttk.Frame(self, padding=5)
        lists_frame.pack(fill='both', expand=True)

        # Available
        avail_frame = ttk.LabelFrame(lists_frame, text="Available")
        avail_frame.configure(padding=5)
        avail_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        avail_scroll = ttk.Scrollbar(avail_frame)
        avail_scroll.pack(side='right', fill='y')
        self.avail_list = tk.Listbox(avail_frame, yscrollcommand=avail_scroll.set,
                                      selectmode='extended', width=40, height=22)
        style_tk_listbox(self.avail_list)
        self.avail_list.pack(side='left', fill='both', expand=True)
        avail_scroll.config(command=self.avail_list.yview)
        self.avail_list.bind('<Double-1>', lambda e: self.add_selected())

        # Buttons
        btn_frame = ttk.Frame(lists_frame)
        btn_frame.pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Add >>", command=self.add_selected, width=10).pack(pady=5)
        ttk.Button(btn_frame, text="<< Remove", command=self.remove_selected, width=10).pack(pady=5)
        ttk.Button(btn_frame, text="Add All", command=self.add_all, width=10).pack(pady=20)
        ttk.Button(btn_frame, text="Clear", command=self.clear_all, width=10).pack(pady=5)

        # Selected
        sel_frame = ttk.LabelFrame(lists_frame, text="Selected")
        sel_frame.configure(padding=5)
        sel_frame.pack(side='left', fill='both', expand=True, padx=(5, 0))
        sel_scroll = ttk.Scrollbar(sel_frame)
        sel_scroll.pack(side='right', fill='y')
        self.sel_list = tk.Listbox(sel_frame, yscrollcommand=sel_scroll.set,
                                    selectmode='extended', width=40, height=22)
        style_tk_listbox(self.sel_list)
        self.sel_list.pack(side='left', fill='both', expand=True)
        sel_scroll.config(command=self.sel_list.yview)
        self.sel_list.bind('<Double-1>', lambda e: self.remove_selected())

        bottom_frame = ttk.Frame(self, padding=5)
        bottom_frame.pack(fill='x')
        self.status_var = tk.StringVar(value="0 selected")
        ttk.Label(bottom_frame, textvariable=self.status_var).pack(side='left')
        ttk.Button(bottom_frame, text="OK", command=self.on_ok, width=10).pack(side='right', padx=5)
        ttk.Button(bottom_frame, text="Cancel", command=self.on_cancel, width=10).pack(side='right')

    def refresh_lists(self):
        query = self.search_var.get()
        category = self.category_var.get()
        if category == "All":
            category = None

        type_map = {"Buffs": "buff", "Debuffs": "debuff", "Misc": "misc"}
        buff_type = type_map.get(self.type_var.get())

        available = self.database.search(query, category, buff_type=buff_type)

        self.avail_list.delete(0, tk.END)
        self.avail_data = []
        for buff in available:
            buff_ids = buff.get('ids', [])
            if not any(bid in self.selected_ids for bid in buff_ids):
                id_str = format_ids_display(buff_ids)
                self.avail_list.insert(tk.END, f"{buff['name']} ({id_str})")
                self.avail_data.append(buff)

        self.sel_list.delete(0, tk.END)
        self.sel_data = []
        selected_entries = []
        for buff in self.database.grouped_buffs:
            buff_ids = buff.get('ids', [])
            selected_from_buff = [bid for bid in buff_ids if bid in self.selected_ids]
            if selected_from_buff:
                id_str = format_ids_display(selected_from_buff)
                selected_entries.append({
                    'name': buff['name'], 'ids': selected_from_buff,
                    'buff': buff, 'display': f"{buff['name']} ({id_str})"
                })
        selected_entries.sort(key=lambda e: e['name'].lower())
        for entry in selected_entries:
            self.sel_list.insert(tk.END, entry['display'])
            self.sel_data.append({'name': entry['name'], 'ids': entry['ids'], 'buff': entry['buff']})

        self.status_var.set(f"{len(self.selected_ids)} IDs selected")

    def add_selected(self):
        for i in self.avail_list.curselection():
            for bid in self.avail_data[i].get('ids', []):
                self.selected_ids.add(bid)
        self.refresh_lists()

    def remove_selected(self):
        for i in self.sel_list.curselection():
            for bid in self.sel_data[i]['ids']:
                self.selected_ids.discard(bid)
        self.refresh_lists()

    def add_all(self):
        for buff in self.avail_data:
            for bid in buff.get('ids', []):
                self.selected_ids.add(bid)
        self.refresh_lists()

    def clear_all(self):
        self.selected_ids.clear()
        self.refresh_lists()

    def on_ok(self):
        self.save_filter_state()
        self.result = list(self.selected_ids)
        self.destroy()

    def on_cancel(self):
        self.save_filter_state()
        self.result = None
        self.destroy()

# ============================================================================
# SLOT ASSIGNMENT DIALOG
# ============================================================================
class SlotAssignmentDialog(tk.Toplevel):
    def __init__(self, parent, database, grid_config):
        super().__init__(parent)
        self.withdraw()
        apply_dark_titlebar(self)
        self.title(f"Slot Assignments - {grid_config['id']}")
        self.transient(parent)
        self.grab_set()

        self.database = database
        self.grid_config = grid_config
        self.total_slots = grid_config['rows'] * grid_config['cols']

        self.assignments = {}
        for i in range(self.total_slots):
            key = str(i)
            if key in grid_config.get('slotAssignments', {}):
                self.assignments[i] = list(grid_config['slotAssignments'][key])
            elif i in grid_config.get('slotAssignments', {}):
                self.assignments[i] = list(grid_config['slotAssignments'][i])
            else:
                self.assignments[i] = []

        self.result = None
        self.create_widgets()
        restore_window_position(self, 'slot_assignment', *SLOT_ASSIGNMENT_SIZE, parent)
        bind_window_position_save(self, 'slot_assignment')
        self.deiconify()

    def create_widgets(self):
        info = f"Grid: {self.grid_config['rows']}x{self.grid_config['cols']} = {self.total_slots} slots"
        ttk.Label(self, text=info, padding=5, font=('Arial', 9)).pack(fill='x')

        container = ttk.Frame(self)
        container.pack(fill='both', expand=True, padx=5, pady=2)

        outer, self.slots_frame, _ = create_scrollable_frame(container)
        outer.pack(fill='both', expand=True)

        self.slot_lists = []
        for i in range(self.total_slots):
            row = i // self.grid_config['cols']
            col = i % self.grid_config['cols']

            frame = ttk.LabelFrame(self.slots_frame, text=f"Slot {i} (r{row},c{col})")
            frame.configure(padding=3)
            frame.pack(fill='x', pady=1, padx=3)

            list_frame = ttk.Frame(frame)
            list_frame.pack(side='left', fill='x', expand=True)

            listbox = tk.Listbox(list_frame, height=1, width=45, font=FONT_SMALL)
            style_tk_listbox(listbox)
            listbox.pack(side='left', fill='x', expand=True)
            self.slot_lists.append(listbox)

            btn_frame = ttk.Frame(frame)
            btn_frame.pack(side='right', padx=3)
            ttk.Button(btn_frame, text="Edit", width=6,
                       command=lambda idx=i: self.edit_slot(idx)).pack(side='left', padx=1)
            ttk.Button(btn_frame, text="Clear", width=6,
                       command=lambda idx=i: self.clear_slot(idx)).pack(side='left', padx=1)

        self.refresh_slot_displays()

        bottom = ttk.Frame(self, padding=5)
        bottom.pack(fill='x')
        ttk.Button(bottom, text="OK", command=self.on_ok, width=10).pack(side='right', padx=5)
        ttk.Button(bottom, text="Cancel", command=self.on_cancel, width=10).pack(side='right')

    def refresh_slot_displays(self):
        for i, listbox in enumerate(self.slot_lists):
            listbox.delete(0, tk.END)
            for buff_id in self.assignments.get(i, []):
                name = self.database.get_name(buff_id)
                btype = self.database.get_type(buff_id)
                tag = {"debuff": "(D)", "misc": "(M)"}.get(btype, "(B)")
                listbox.insert(tk.END, f"{name} {tag} ({buff_id})")

    def edit_slot(self, slot_index):
        dialog = BuffSelectorDialog(
            self, self.database, f"Slot {slot_index} Buffs",
            initial_ids=self.assignments.get(slot_index, [])
        )
        self.wait_window(dialog)
        if dialog.result is not None:
            self.assignments[slot_index] = dialog.result
            self.refresh_slot_displays()

    def clear_slot(self, slot_index):
        self.assignments[slot_index] = []
        self.refresh_slot_displays()

    def on_ok(self):
        self.result = {str(k): v for k, v in self.assignments.items() if v}
        self.destroy()

    def on_cancel(self):
        self.result = None
        self.destroy()

# ============================================================================
# GRID EDITOR PANEL
# ============================================================================
class GridEditorPanel(ttk.Frame):
    """A collapsible grid editor using CollapsibleSection.

    Collapsed: shows summary (source, size, mode) + Enabled + Delete
    Expanded: Name row, Position & Size, Timer Display, Mode Options
    """

    def __init__(self, parent, database, grid_config, on_delete=None, initially_open=False):
        super().__init__(parent)
        self.database = database
        self.grid_config = grid_config
        self.on_delete = on_delete

        # Accent color by grid type (player=blue, target=orange)
        grid_type = grid_config.get('type', 'player')
        self._accent_color = GRID_TYPE_COLORS.get(grid_type, GRID_TYPE_COLORS['player'])

        # Card border — thin colored frame on all 4 sides
        card = tk.Frame(self,
                        highlightbackground=self._accent_color,
                        highlightcolor=self._accent_color,
                        highlightthickness=1)
        card.pack(fill='x')

        self.section = CollapsibleSection(
            card, title=grid_config.get('id', 'Grid'),
            badge_text=grid_type,
            badge_color=self._accent_color,
            initially_open=initially_open,
        )
        self.section.pack(fill='x', padx=4, pady=(2, 4))

        # --- Header right side: Enabled + Delete (always visible) ---
        self.enabled_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(self.section.header_frame, text="Enabled",
                        variable=self.enabled_var,
                        bootstyle="success-round-toggle").pack(side='right', padx=(0, 4))
        ttk.Button(self.section.header_frame, text="Delete",
                   command=self.delete_grid, width=BTN_SMALL).pack(side='right', padx=(0, 4))

        # --- Content area ---
        content = self.section.content

        # Row 1: Name
        row1 = ttk.Frame(content)
        row1.pack(fill='x', pady=(0, PAD_ROW))
        ttk.Label(row1, text="Name:", font=FONT_SMALL_BOLD,
                  foreground=THEME_COLORS['body']).pack(side='left')
        self.id_var = tk.StringVar()
        name_entry = ttk.Entry(row1, textvariable=self.id_var, width=18)
        name_entry.pack(side='left', padx=(4, 0))
        add_tooltip(name_entry, "Display name for this grid (shown in preview mode)")

        # Hidden vars for summary display (set from config, not editable)
        self.type_var = tk.StringVar()
        self.size_var = tk.StringVar()
        self.mode_var = tk.StringVar()

        # --- Position & Size ---
        pos_header = create_section_header(content, "Position & Size", color=self._accent_color)
        pos_header.pack(fill='x', pady=(PAD_ROW, 2))

        pos_row = ttk.Frame(content)
        pos_row.pack(fill='x', pady=(0, PAD_ROW))

        ttk.Label(pos_row, text="X:", font=FONT_FORM_LABEL).pack(side='left')
        self.x_var = tk.IntVar()
        x_spin = ttk.Spinbox(pos_row, from_=0, to=SCREEN_MAX_X, textvariable=self.x_var, width=5)
        x_spin.pack(side='left', padx=(2, 10))
        add_tooltip(x_spin, "Horizontal position on screen (pixels from left edge)")

        ttk.Label(pos_row, text="Y:", font=FONT_FORM_LABEL).pack(side='left')
        self.y_var = tk.IntVar()
        y_spin = ttk.Spinbox(pos_row, from_=0, to=SCREEN_MAX_Y, textvariable=self.y_var, width=5)
        y_spin.pack(side='left', padx=(2, 10))
        add_tooltip(y_spin, "Vertical position on screen (pixels from top edge)")

        ttk.Label(pos_row, text="Icon Size:", font=FONT_FORM_LABEL).pack(side='left')
        self.icon_var = tk.IntVar()
        icon_spin = ttk.Spinbox(pos_row, from_=24, to=64, textvariable=self.icon_var, width=2)
        icon_spin.pack(side='left', padx=(2, 10))
        add_tooltip(icon_spin, "Size of each buff icon in pixels (24-64)")

        ttk.Label(pos_row, text="Gap:", font=FONT_FORM_LABEL).pack(side='left')
        self.gap_var = tk.IntVar()
        gap_spin = ttk.Spinbox(pos_row, from_=-5, to=10, textvariable=self.gap_var, width=2)
        gap_spin.pack(side='left', padx=(2, 0))
        add_tooltip(gap_spin, "Space between icons (-5 = overlapping, 0 = touching, 10 = spaced out)")

        # --- Timer Display ---
        timer_header = create_section_header(content, "Timer Display", color=self._accent_color)
        timer_header.pack(fill='x', pady=(PAD_ROW, 2))

        timer_row = ttk.Frame(content)
        timer_row.pack(fill='x', pady=(0, PAD_ROW))

        self.timers_var = tk.BooleanVar()
        timers_cb = ttk.Checkbutton(timer_row, text="Show Timers", variable=self.timers_var,
                                     bootstyle="success-round-toggle")
        timers_cb.pack(side='left', padx=(0, 10))
        add_tooltip(timers_cb, "Display remaining duration below each buff icon")

        ttk.Label(timer_row, text="Font Size:", font=FONT_FORM_LABEL).pack(side='left')
        self.timer_font_var = tk.IntVar()
        font_spin = ttk.Spinbox(timer_row, from_=8, to=24, textvariable=self.timer_font_var, width=2)
        font_spin.pack(side='left', padx=(2, 10))
        add_tooltip(font_spin, "Font size for timer text below icons (8-24)")

        ttk.Label(timer_row, text="Y Offset:", font=FONT_FORM_LABEL).pack(side='left')
        self.timer_y_offset_var = tk.IntVar()
        yoff_spin = ttk.Spinbox(timer_row, from_=-10, to=10, textvariable=self.timer_y_offset_var, width=2)
        yoff_spin.pack(side='left', padx=(2, 10))
        add_tooltip(yoff_spin, "Shift timer text up/down relative to the icon (-10 to 10)")

        self.flashing_var = tk.BooleanVar()
        flash_cb = ttk.Checkbutton(timer_row, text="Flash Warning", variable=self.flashing_var,
                                    bootstyle="success-round-toggle")
        flash_cb.pack(side='left', padx=(0, 6))
        add_tooltip(flash_cb, "Icons flash when buff timer is about to expire")

        ttk.Label(timer_row, text="Threshold:", font=FONT_FORM_LABEL).pack(side='left')
        self.flash_threshold_var = tk.IntVar()
        thres_spin = ttk.Spinbox(timer_row, from_=0, to=11, textvariable=self.flash_threshold_var, width=2)
        thres_spin.pack(side='left', padx=(2, 0))
        add_tooltip(thres_spin, "Icons flash when buff timer drops below this many seconds (0-11)")
        ttk.Label(timer_row, text="s", foreground=THEME_COLORS['muted'],
                  font=FONT_SMALL).pack(side='left', padx=(0, 0))

        # --- Mode Options ---
        self.options_frame = ttk.Frame(content)
        self.options_frame.pack(fill='x', pady=(PAD_ROW, 0))

        # Dynamic mode options
        self.dynamic_frame = ttk.Frame(self.options_frame)

        dyn_header = create_section_header(self.dynamic_frame, "Dynamic Mode \u2014 Auto-fill", color=self._accent_color)
        dyn_header.pack(fill='x', pady=(0, 2))

        dyn_row = ttk.Frame(self.dynamic_frame)
        dyn_row.pack(fill='x', pady=(0, PAD_ROW))

        ttk.Label(dyn_row, text="Fill Direction:", font=FONT_FORM_LABEL).pack(side='left')
        self.fill_var = tk.StringVar()
        self.fill_combo = ttk.Combobox(dyn_row, textvariable=self.fill_var, width=8, state='readonly')
        self.fill_combo.pack(side='left', padx=(2, 10))
        add_tooltip(self.fill_combo, "Direction buffs fill into the grid (Left-to-Right, Bottom-to-Top, etc.)")

        ttk.Label(dyn_row, text="Sorting:", font=FONT_FORM_LABEL).pack(side='left')
        self.sort_var = tk.StringVar()
        sort_combo = ttk.Combobox(dyn_row, textvariable=self.sort_var,
                                  values=['shortest', 'longest', 'application'], width=10, state='readonly')
        sort_combo.pack(side='left', padx=(2, 10))
        add_tooltip(sort_combo, "How buffs are ordered (by shortest/longest remaining time, or order applied)")

        ttk.Label(dyn_row, text="Grouping:", font=FONT_FORM_LABEL).pack(side='left')
        self.layout_var = tk.StringVar()
        group_combo = ttk.Combobox(dyn_row, textvariable=self.layout_var,
                                   values=['buffFirst', 'debuffFirst', 'mixed'], width=10, state='readonly')
        group_combo.pack(side='left', padx=(2, 0))
        add_tooltip(group_combo, "Whether buffs appear before debuffs, or mixed together")

        # Whitelist row
        wl_row = ttk.Frame(self.dynamic_frame)
        wl_row.pack(fill='x', pady=(0, PAD_ROW))

        ttk.Button(wl_row, text="Edit Whitelist...", command=self.edit_whitelist,
                   width=BTN_MEDIUM).pack(side='left', padx=(0, 8))
        self.whitelist_label = tk.StringVar(value="Whitelist: empty \u2014 tracking all buffs")
        ttk.Label(wl_row, textvariable=self.whitelist_label,
                  foreground=THEME_COLORS['muted'], font=FONT_SMALL).pack(side='left')

        # Whitelist preview (shows first few buff names)
        self.whitelist_preview_var = tk.StringVar(value="")
        self.whitelist_preview_label = ttk.Label(
            self.dynamic_frame, textvariable=self.whitelist_preview_var,
            foreground=THEME_COLORS['muted'], font=FONT_SMALL, wraplength=500)

        # Static mode options
        self.static_frame = ttk.Frame(self.options_frame)

        stat_header = create_section_header(self.static_frame, "Static Mode \u2014 Fixed Slots", color=self._accent_color)
        stat_header.pack(fill='x', pady=(0, 2))

        stat_row = ttk.Frame(self.static_frame)
        stat_row.pack(fill='x')

        ttk.Button(stat_row, text="Edit Slot Assignments...", command=self.edit_slots,
                   width=BTN_MEDIUM + 4).pack(side='left', padx=(0, 8))
        self.slots_label = tk.StringVar(value="0 of 0 slots assigned")
        ttk.Label(stat_row, textvariable=self.slots_label,
                  foreground=THEME_COLORS['muted'], font=FONT_SMALL).pack(side='left')

        self.load_from_config()

        # Hover highlight on card border
        bind_card_events(card, self._accent_color)

    def load_from_config(self):
        cfg = self.grid_config
        self.id_var.set(cfg.get('id', 'Grid'))
        self.enabled_var.set(cfg.get('enabled', True))
        self.type_var.set(cfg.get('type', 'player').title())
        rows = cfg.get('rows', 1)
        cols = cfg.get('cols', 5)
        self.size_var.set(f"{rows}x{cols}")
        self.mode_var.set(cfg.get('slotMode', 'dynamic').title())
        self.x_var.set(min(cfg.get('x', 100), SCREEN_MAX_X))
        self.y_var.set(min(cfg.get('y', 400), SCREEN_MAX_Y))
        self.icon_var.set(min(cfg.get('iconSize', 56), 64))
        self.gap_var.set(max(-5, min(cfg.get('gap', -1), 10)))
        self.timers_var.set(cfg.get('showTimers', True))
        self.timer_font_var.set(cfg.get('timerFontSize', 18))
        self.flash_threshold_var.set(cfg.get('timerFlashThreshold', 6))
        self.timer_y_offset_var.set(cfg.get('timerYOffset', 0))
        self.flashing_var.set(cfg.get('enableFlashing', True))
        self.fill_var.set(cfg.get('fillDirection', 'LR'))
        self.sort_var.set(cfg.get('sortOrder', 'longest'))
        self.layout_var.set(cfg.get('layout', 'buffFirst'))

        if rows == 1:
            self.fill_combo['values'] = ['LR', 'RL']
            if cfg.get('fillDirection') not in ['LR', 'RL']:
                self.fill_var.set('LR')
        elif cols == 1:
            self.fill_combo['values'] = ['TB', 'BT']
            if cfg.get('fillDirection') not in ['TB', 'BT']:
                self.fill_var.set('BT')
        else:
            self.fill_combo['values'] = ['TL-BR', 'TR-BL', 'BL-TR', 'BR-TL']
            if cfg.get('fillDirection') not in ['TL-BR', 'TR-BL', 'BL-TR', 'BR-TL']:
                self.fill_var.set('BL-TR')

        if cfg.get('slotMode') == 'static':
            self.dynamic_frame.pack_forget()
            self.static_frame.pack(fill='x')
        else:
            self.static_frame.pack_forget()
            self.dynamic_frame.pack(fill='x')

        self.update_labels()

    def save_to_config(self):
        self.grid_config['id'] = self.id_var.get()
        self.grid_config['enabled'] = self.enabled_var.get()
        self.grid_config['x'] = max(0, min(self.x_var.get(), SCREEN_MAX_X))
        self.grid_config['y'] = max(0, min(self.y_var.get(), SCREEN_MAX_Y))
        self.grid_config['iconSize'] = max(24, min(self.icon_var.get(), 64))
        self.grid_config['gap'] = max(-5, min(self.gap_var.get(), 10))
        self.grid_config['showTimers'] = self.timers_var.get()
        self.grid_config['timerFontSize'] = self.timer_font_var.get()
        self.grid_config['timerFlashThreshold'] = max(0, min(self.flash_threshold_var.get(), 11))
        self.grid_config['timerYOffset'] = max(-10, min(self.timer_y_offset_var.get(), 10))
        self.grid_config['enableFlashing'] = self.flashing_var.get()
        self.grid_config['fillDirection'] = self.fill_var.get()
        self.grid_config['sortOrder'] = self.sort_var.get()
        self.grid_config['layout'] = self.layout_var.get()

    def update_labels(self):
        cfg = self.grid_config
        wl = cfg.get('whitelist', [])
        rows = cfg.get('rows', 1)
        cols = cfg.get('cols', 5)
        total_slots = rows * cols

        # Whitelist label
        if wl:
            self.whitelist_label.set(f"Whitelist: {len(wl)} buffs filtered")
        else:
            self.whitelist_label.set("Whitelist: empty \u2014 tracking all buffs")

        # Whitelist preview (show first few buff names)
        if wl and self.database:
            names = []
            for bid in wl:
                buff = self.database.by_id.get(bid)
                if buff and buff['name'] not in names:
                    names.append(buff['name'])
            if names:
                preview_names = names[:4]
                preview = ", ".join(preview_names)
                if len(names) > 4:
                    preview += f" + {len(names) - 4} more"
                self.whitelist_preview_var.set(preview)
                self.whitelist_preview_label.pack(fill='x', pady=(0, 2))
            else:
                self.whitelist_preview_var.set("")
                self.whitelist_preview_label.pack_forget()
        else:
            self.whitelist_preview_var.set("")
            self.whitelist_preview_label.pack_forget()

        # Slot assignments label
        sa = cfg.get('slotAssignments', {})
        configured = sum(1 for v in sa.values() if v)
        self.slots_label.set(f"{configured} of {total_slots} slots assigned")

        # Update collapsible header
        self.section.set_title(cfg.get('id', 'Grid'))

        # Build summary for collapsed state
        source = cfg.get('type', 'player')
        size = f"{rows}x{cols}"
        mode = cfg.get('slotMode', 'dynamic')
        self.section.set_summary(f"  {size} \u00B7 {mode}")

    def edit_whitelist(self):
        self.save_to_config()
        dialog = BuffSelectorDialog(
            self.winfo_toplevel(), self.database, "Edit Whitelist",
            initial_ids=self.grid_config.get('whitelist', [])
        )
        self.wait_window(dialog)
        if dialog.result is not None:
            self.grid_config['whitelist'] = dialog.result
            self.update_labels()

    def edit_slots(self):
        self.save_to_config()
        dialog = SlotAssignmentDialog(self.winfo_toplevel(), self.database, self.grid_config)
        self.wait_window(dialog)
        if dialog.result is not None:
            self.grid_config['slotAssignments'] = dialog.result
            self.update_labels()

    def delete_grid(self):
        if Messagebox.yesno(f"Delete grid '{self.id_var.get()}'?", title="Confirm") == "Yes":
            if self.on_delete:
                self.on_delete(self)

# ============================================================================
# GRIDS TAB
# ============================================================================
class GridsTab(ttk.Frame):
    """Grids configuration tab — manages grid list, panels, and canvas."""

    def __init__(self, parent, database, app_version, profiles_path,
                 on_modified=None, on_open_database=None, status_var=None,
                 game_path_var=None, assets_path=None):
        super().__init__(parent)
        self.database = database
        self.app_version = app_version
        self.profiles_path = profiles_path
        self.on_modified = on_modified
        self.on_open_database = on_open_database
        self.status_var = status_var
        self.game_path_var = game_path_var
        self._assets_path = assets_path

        self.grids = []
        self.grid_panels = []

        # Profile label, grid count, slot count
        self.profile_label = tk.StringVar(value="No profile loaded")
        self.grid_count_label = tk.StringVar(value="0 grids")
        self.slot_count_label = tk.StringVar(value=f"0 / {MAX_TOTAL_SLOTS} slots")

        self._create_widgets()

    def _create_widgets(self):
        """Build the tab UI — buttons, description, scrollable canvas."""
        # === BUTTONS (top bar) ===
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill='x', padx=10, pady=(5, 5))

        ttk.Button(btn_frame, text="+ Add Grid", command=self.add_grid, width=BTN_MEDIUM).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="Clear All", command=self._clear_all_grids, width=BTN_MEDIUM).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="Database", command=self._on_database_click, width=BTN_MEDIUM).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="Build", command=self._build, width=BTN_MEDIUM).pack(side='right', padx=2)
        ttk.Button(btn_frame, text="Export...", command=self.export_grids, width=BTN_MEDIUM).pack(side='right', padx=2)
        ttk.Button(btn_frame, text="Import...", command=self.import_grids, width=BTN_MEDIUM).pack(side='right', padx=2)

        self.build_status = ttk.Label(
            btn_frame, text="",
            font=FONT_SMALL, foreground=THEME_COLORS['muted']
        )
        self.build_status.pack(side='left', padx=(10, 0))

        # === TIP BAR + PROFILE INFO ===
        create_tip_bar(self, "Configure buff/debuff tracking grids. Ctrl+Shift+Alt in-game for Preview Mode.")

        create_profile_info_bar(self, self.profile_label,
                               extra_labels=[self.grid_count_label, self.slot_count_label])

        grids_container = ttk.Frame(self)
        grids_container.pack(fill='both', expand=True, padx=5, pady=5)

        outer, self.grids_frame, self.grids_canvas = create_scrollable_frame(grids_container)
        outer.pack(fill='both', expand=True)

    def _on_database_click(self):
        if self.on_open_database:
            self.on_open_database()

    def get_profile_data(self):
        """Return current grid configurations."""
        return self.grids

    def load_profile_data(self, grids):
        """Load grid configs and rebuild panels."""
        self.grids = grids
        self.refresh_panels()

    def set_profile_name(self, name):
        """Update the profile indicator label."""
        self.profile_label.set(name)

    def get_total_slots(self):
        """Return total slot count across all grids."""
        return sum(g['rows'] * g['cols'] for g in self.grids)

    def _build(self):
        """Build KzGrids.swf."""
        grids = self.get_profile_data()
        if not grids:
            Messagebox.show_error("No grids configured.", title="Error")
            return

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

        kzgrids_path = base_assets / "kzgrids"
        base_swf = kzgrids_path / "base.swf"
        stubs = kzgrids_path / "stubs"
        compiler_path = base_assets / "compiler" / "mtasc.exe"
        flash_path = Path(game_path) / "Data" / "Gui" / "Default" / "Flash"
        output_path = flash_path / "KzGrids.swf"

        if not base_swf.exists():
            Messagebox.show_error(
                f"KzGrids base.swf not found:\n{base_swf}",
                title="Missing base.swf"
            )
            return
        if not compiler_path.exists():
            Messagebox.show_error(
                f"MTASC compiler not found:\n{compiler_path}",
                title="Compiler Not Found"
            )
            return

        flash_path.mkdir(parents=True, exist_ok=True)

        self.build_status.config(text="Building...", foreground=THEME_COLORS['warning'])
        self.update()

        success, message = build_grids(
            grids, self.database, str(base_swf), str(stubs),
            str(output_path), str(compiler_path), self.app_version
        )

        if success:
            # Update auto_login script
            scripts_path = Path(game_path) / "Data" / "Gui" / "Default" / "Scripts"
            update_script_with_marker(
                scripts_path / "auto_login",
                "# KzGrids auto-load",
                "/unloadclip KzGrids.swf\n/delay 100\n/loadclip KzGrids.swf"
            )
            self.build_status.config(text="Build successful!", foreground=THEME_COLORS['success'])
            Messagebox.show_info(
                f"{message}\n\nIn-game: /reloadui",
                title="Build Complete"
            )
        else:
            self.build_status.config(text="Build failed", foreground=THEME_COLORS['danger'])
            Messagebox.show_error(message, title="Build Failed")

    def save_settings(self):
        """Persist all panel UI values back to grid configs."""
        for panel in self.grid_panels:
            panel.save_to_config()

    def add_grid(self):
        """Open AddGridWizard dialog."""
        existing_ids = {g['id'] for g in self.grids}
        current_slots = self.get_total_slots()
        if current_slots >= MAX_TOTAL_SLOTS:
            Messagebox.show_warning(f"Maximum {MAX_TOTAL_SLOTS} total slots reached", title="Limit")
            return
        wizard = AddGridWizard(self.winfo_toplevel(), existing_ids, current_slots)
        self.winfo_toplevel().wait_window(wizard)
        if wizard.result:
            self.grids.append(wizard.result)
            self._mark_modified()
            self.refresh_panels()

    def delete_grid(self, panel):
        """Delete a single grid."""
        for i, p in enumerate(self.grid_panels):
            if p == panel:
                del self.grids[i]
                self._mark_modified()
                self.refresh_panels()
                break

    def _clear_all_grids(self):
        """Remove all grids with confirmation."""
        if not self.grids:
            return
        if Messagebox.yesno(f"Remove all {len(self.grids)} grids?", title="Clear All Grids") == "No":
            return
        self.grids.clear()
        self._mark_modified()
        self.refresh_panels()

    def refresh_panels(self):
        """Rebuild GridEditorPanel widgets from self.grids."""
        for widget in self.grids_frame.winfo_children():
            widget.destroy()
        self.grid_panels.clear()
        for i, grid_config in enumerate(self.grids):
            if i > 0:
                ttk.Separator(self.grids_frame, orient='horizontal').pack(
                    fill='x', padx=15, pady=4)
            panel = GridEditorPanel(
                self.grids_frame, self.database, grid_config,
                on_delete=self.delete_grid, initially_open=(i == 0),
            )
            panel.pack(fill='x', pady=(0, 4), padx=5)
            self.grid_panels.append(panel)
        self.grid_count_label.set(f"{len(self.grids)} grids")
        self.slot_count_label.set(f"{self.get_total_slots()} / {MAX_TOTAL_SLOTS} slots")

    def import_grids(self):
        """Import grid configs from JSON file."""
        path = filedialog.askopenfilename(title="Import Grids", initialdir=str(self.profiles_path),
                                          filetypes=[("JSON", "*.json"), ("All", "*.*")])
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            grids = data.get('grids', [])
            if not grids:
                Messagebox.show_warning("No grid configurations found in file.", title="Warning")
                return
            self.grids = grids
            self._mark_modified()
            self.refresh_panels()
            if self.status_var:
                self.status_var.set(f"Imported {len(grids)} grids from: {Path(path).name}")
        except Exception as e:
            Messagebox.show_error(f"Failed to import grids:\n{e}", title="Error")

    def export_grids(self):
        """Export grid configs to JSON file."""
        self.save_settings()
        if not self.grids:
            Messagebox.show_warning("No grids to export.", title="Warning")
            return
        path = filedialog.asksaveasfilename(title="Export Grids", initialdir=str(self.profiles_path),
                                            initialfile="Gr_",
                                            defaultextension=".json", filetypes=[("JSON", "*.json"), ("All", "*.*")])
        if not path:
            return
        try:
            data = {'version': self.app_version, 'grids': self.grids}
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            if self.status_var:
                self.status_var.set(f"Exported {len(self.grids)} grids to: {Path(path).name}")
        except Exception as e:
            Messagebox.show_error(f"Failed to export grids:\n{e}", title="Error")

    def _mark_modified(self):
        """Signal that grids have changed."""
        if self.on_modified:
            self.on_modified()
