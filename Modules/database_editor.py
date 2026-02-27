"""
KzGrids Database Editor Module
Handles buff database loading, editing, and the Database tab UI.

v2 Format:
{
    "name": "Buff Name",
    "ids": [id1, id2, ...],
    "category": "#Category",
    "type": "buff" | "debuff" | "misc",
    "stacking": true,      // optional - IDs represent stack levels
    "stackStart": 1        // optional - first ID = this stack number (default: 1)
}
"""

import logging
import tkinter as tk
from tkinter import ttk, filedialog
from ttkbootstrap.dialogs import Messagebox
from .ui_helpers import THEME_COLORS, FONT_SMALL, style_tk_text, apply_dark_titlebar, BTN_SMALL, BTN_MEDIUM, add_tooltip
import json
import re

logger = logging.getLogger(__name__)


# ============================================================================
# CONSTANTS
# ============================================================================
TYPE_FILTER_MAP = {"Buff": "buff", "Debuff": "debuff", "Misc": "misc"}


# ============================================================================
# BUFF DATABASE
# ============================================================================
class BuffDatabase:
    """Handles loading, searching, and managing the buff database."""

    def __init__(self):
        self.buffs = []
        self.categories = []
        self.by_id = {}
        self.grouped_buffs = []

    def load(self, json_path):
        """Load database from JSON file."""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.buffs = data.get('buffs', [])
            self._rebuild_indexes()
            return True
        except Exception as e:
            logger.error("Error loading buff database: %s", e)
            return False

    def _rebuild_indexes(self):
        """Rebuild internal indexes after data changes."""
        cats = set()
        self.by_id = {}
        for b in self.buffs:
            cats.add(b.get('category', 'Unknown'))
            ids = b.get('ids', [])
            for bid in ids:
                self.by_id[bid] = b
        self.categories = sorted(list(cats))
        self._group_buffs_by_name()

    def _group_buffs_by_name(self):
        """Group buffs by name for display purposes."""
        # In v2 format, each entry is already properly grouped
        # Just copy the buffs list to grouped_buffs
        self.grouped_buffs = list(self.buffs)

    def search(self, query="", category=None, buff_type=None):
        """
        Search buffs by query, category, and type.

        Args:
            query: Search string (matches name or ID)
            category: Category filter (None = all)
            buff_type: Type filter - "buff", "debuff", "misc" (None = all)
        """
        results = []
        query_lower = query.lower() if query else ""

        for buff in self.grouped_buffs:
            # Category filter
            if category and buff.get('category') != category:
                continue

            # Type filter
            if buff_type and buff.get('type', 'buff') != buff_type:
                continue

            # Query filter (name or ID)
            if query_lower:
                name_match = query_lower in buff.get('name', '').lower()
                id_match = any(query_lower in str(bid) for bid in buff.get('ids', []))
                if not name_match and not id_match:
                    continue

            results.append(buff)

        return sorted(results, key=lambda b: (b.get('category', ''), b.get('name', '')))

    def get_by_id(self, buff_id):
        """Get buff entry by ID."""
        return self.by_id.get(buff_id)

    def get_name(self, buff_id):
        """Get buff name by ID."""
        buff = self.by_id.get(buff_id)
        return buff['name'] if buff else f"ID:{buff_id}"

    def get_type(self, buff_id):
        """Get buff type by ID (buff/debuff/misc)."""
        buff = self.by_id.get(buff_id)
        if buff:
            return buff.get('type', 'buff')
        return 'buff'

    def is_debuff(self, buff_id):
        """Check if buff is a debuff."""
        return self.get_type(buff_id) == 'debuff'

    def is_stacking(self, buff_id):
        """Check if buff is a stacking buff."""
        buff = self.by_id.get(buff_id)
        if buff:
            return buff.get('stacking', False)
        return False

    def get_stack_level(self, buff_id):
        """
        Get stack level for a buff ID.
        Returns stackStart + index for stacking buffs.
        Returns None if not a stacking buff or ID not found.
        """
        buff = self.by_id.get(buff_id)
        if buff and buff.get('stacking', False):
            ids = buff.get('ids', [])
            stack_start = buff.get('stackStart', 1)
            try:
                return stack_start + ids.index(buff_id)
            except ValueError:
                return None
        return None

    def add_buff(self, buff_data):
        """Add a new buff entry."""
        self.buffs.append(buff_data)
        self._rebuild_indexes()

    def update_buff(self, old_ids, new_data):
        """Update an existing buff entry."""
        for i, buff in enumerate(self.buffs):
            buff_ids = buff.get('ids', [])
            if set(buff_ids) == set(old_ids):
                self.buffs[i] = new_data
                break
        self._rebuild_indexes()

    def remove_buff(self, ids):
        """Remove a buff entry by its IDs."""
        self.buffs = [b for b in self.buffs if set(b.get('ids', [])) != set(ids)]
        self._rebuild_indexes()

    def save(self, json_path):
        """Save database to JSON file."""
        data = {
            "version": 2,
            "description": "KzGrids buff/debuff database v2",
            "buffs": self.buffs
        }
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


# ============================================================================
# BUFF EDIT DIALOG
# ============================================================================
class BuffEditDialog(tk.Toplevel):
    """Dialog for adding/editing buff entries."""

    DIALOG_WIDTH = 450
    DIALOG_HEIGHT = 480

    def __init__(self, parent, title, categories, buff=None):
        super().__init__(parent)
        self.withdraw()
        apply_dark_titlebar(self)
        self.title(title)
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)

        self.categories = categories
        self.result = None
        self.create_widgets(buff)

        # Center on parent
        w, h = self.DIALOG_WIDTH, self.DIALOG_HEIGHT
        if parent:
            x = parent.winfo_x() + (parent.winfo_width() - w) // 2
            y = parent.winfo_y() + (parent.winfo_height() - h) // 2
        else:
            x = (self.winfo_screenwidth() - w) // 2
            y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.deiconify()

    def create_widgets(self, buff):
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill='both', expand=True)

        # Name
        ttk.Label(frame, text="Name:").grid(row=0, column=0, sticky='w', pady=5)
        self.name_var = tk.StringVar(value=buff['name'] if buff else "")
        ttk.Entry(frame, textvariable=self.name_var, width=35).grid(row=0, column=1, sticky='w', pady=5)

        # IDs
        ttk.Label(frame, text="ID(s):").grid(row=1, column=0, sticky='nw', pady=5)
        id_frame = ttk.Frame(frame)
        id_frame.grid(row=1, column=1, sticky='w', pady=5)

        self.ids_text = tk.Text(id_frame, width=25, height=10)
        style_tk_text(self.ids_text)
        self.ids_text.pack(side='left')

        if buff:
            ids = buff.get('ids', [])
            self.ids_text.insert('1.0', '\n'.join(str(i) for i in ids))

        ttk.Label(id_frame, text="One per line or\ncomma-separated",
                 foreground=THEME_COLORS['muted'], font=FONT_SMALL).pack(side='left', padx=10)

        # Category
        ttk.Label(frame, text="Category:").grid(row=2, column=0, sticky='w', pady=5)
        self.category_var = tk.StringVar(value=buff.get('category', '') if buff else "")
        ttk.Combobox(frame, textvariable=self.category_var, values=self.categories, width=32).grid(row=2, column=1, sticky='w', pady=5)

        # Type (buff/debuff/misc)
        ttk.Label(frame, text="Type:").grid(row=3, column=0, sticky='w', pady=5)
        initial_type = buff.get('type', 'buff') if buff else 'buff'
        self.type_var = tk.StringVar(value=initial_type)

        type_frame = ttk.Frame(frame)
        type_frame.grid(row=3, column=1, sticky='w', pady=5)
        ttk.Radiobutton(type_frame, text="Buff", variable=self.type_var, value='buff').pack(side='left')
        ttk.Radiobutton(type_frame, text="Debuff", variable=self.type_var, value='debuff').pack(side='left', padx=10)
        ttk.Radiobutton(type_frame, text="Misc", variable=self.type_var, value='misc').pack(side='left', padx=10)

        # Stacking checkbox
        ttk.Label(frame, text="Stacking:").grid(row=4, column=0, sticky='w', pady=5)
        self.stacking_var = tk.BooleanVar(value=buff.get('stacking', False) if buff else False)
        stack_frame = ttk.Frame(frame)
        stack_frame.grid(row=4, column=1, sticky='w', pady=5)
        ttk.Checkbutton(stack_frame, text="This buff has stack levels",
                       variable=self.stacking_var,
                       command=self._on_stacking_changed,
                       bootstyle="success-round-toggle").pack(side='left')
        ttk.Label(stack_frame, text="(IDs ordered by stack)",
                 foreground=THEME_COLORS['muted'], font=FONT_SMALL).pack(side='left', padx=10)

        # Stack Start field (only shown when stacking is checked)
        ttk.Label(frame, text="Start at:").grid(row=5, column=0, sticky='w', pady=5)
        self.stack_start_frame = ttk.Frame(frame)
        self.stack_start_frame.grid(row=5, column=1, sticky='w', pady=5)

        self.stack_start_var = tk.IntVar(value=buff.get('stackStart', 1) if buff else 1)
        self.stack_start_spin = ttk.Spinbox(
            self.stack_start_frame, textvariable=self.stack_start_var,
            from_=1, to=99, width=5
        )
        self.stack_start_spin.pack(side='left')
        ttk.Label(self.stack_start_frame, text="First ID = this stack number",
                 foreground=THEME_COLORS['muted'], font=FONT_SMALL).pack(side='left', padx=10)

        # Stack End field
        ttk.Label(frame, text="End at:").grid(row=6, column=0, sticky='w', pady=5)
        self.stack_end_frame = ttk.Frame(frame)
        self.stack_end_frame.grid(row=6, column=1, sticky='w', pady=5)

        # Default end = start + num_ids - 1, or 0 to mean "all"
        default_end = buff.get('stackEnd', 0) if buff else 0
        self.stack_end_var = tk.IntVar(value=default_end)
        self.stack_end_spin = ttk.Spinbox(
            self.stack_end_frame, textvariable=self.stack_end_var,
            from_=0, to=99, width=5
        )
        self.stack_end_spin.pack(side='left')
        ttk.Label(self.stack_end_frame, text="Last stack to show (0 = all)",
                 foreground=THEME_COLORS['muted'], font=FONT_SMALL).pack(side='left', padx=10)

        # Initial state based on stacking checkbox
        self._on_stacking_changed()

        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=7, column=0, columnspan=2, pady=20)
        ttk.Button(btn_frame, text="OK", command=self.on_ok, width=10).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.on_cancel, width=10).pack(side='left', padx=5)

        # Bind Enter key (but not when in the IDs text field)
        self.bind('<Return>', self._on_return)
        self.bind('<Escape>', lambda e: self.on_cancel())

    def _on_return(self, event):
        """Handle Enter key - allow newlines in IDs text, otherwise OK."""
        if event.widget == self.ids_text:
            return  # Let Text widget handle Enter normally (insert newline)
        self.on_ok()

    def parse_ids(self):
        """Parse IDs from text input."""
        text = self.ids_text.get('1.0', 'end').strip()
        parts = re.split(r'[\n,]+', text)
        ids = []
        for part in parts:
            part = part.strip()
            if part:
                try:
                    ids.append(int(part))
                except ValueError:
                    pass
        return ids

    def _on_stacking_changed(self):
        """Toggle stack start/end fields based on stacking checkbox."""
        if self.stacking_var.get():
            self.stack_start_spin.configure(state='normal')
            self.stack_end_spin.configure(state='normal')
        else:
            self.stack_start_spin.configure(state='disabled')
            self.stack_end_spin.configure(state='disabled')

    def on_ok(self):
        ids = self.parse_ids()
        if not ids:
            Messagebox.show_error("At least one valid ID is required", title="Error")
            return

        name = self.name_var.get().strip()
        if not name:
            Messagebox.show_error("Name is required", title="Error")
            return

        category = self.category_var.get().strip()
        if not category:
            Messagebox.show_error("Category is required", title="Error")
            return

        buff_type = self.type_var.get()
        is_stacking = self.stacking_var.get()

        # Build result - v2 format (no isDebuff)
        self.result = {
            'name': name,
            'ids': ids,
            'category': category,
            'type': buff_type
        }

        # Only add stacking fields if stacking is enabled
        if is_stacking:
            self.result['stacking'] = True
            stack_start = self.stack_start_var.get()
            stack_end = self.stack_end_var.get()
            # Only add stackStart if not default (1)
            if stack_start != 1:
                self.result['stackStart'] = stack_start
            # Only add stackEnd if set (0 = all, so we don't save it)
            if stack_end > 0:
                self.result['stackEnd'] = stack_end

        self.destroy()

    def on_cancel(self):
        self.result = None
        self.destroy()


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================
def format_ids_display(ids, max_show=3):
    """Format a list of IDs for display, truncating if needed."""
    if len(ids) <= max_show:
        return ','.join(str(i) for i in ids)
    return ','.join(str(i) for i in ids[:max_show]) + f"...+{len(ids)-max_show}"


# ============================================================================
# DATABASE EDITOR TAB
# ============================================================================
class DatabaseEditorTab(ttk.Frame):
    """Database editor tab for the main application."""

    def __init__(self, parent, database, assets_path, on_modified=None):
        super().__init__(parent)

        self.database = database
        self.assets_path = assets_path
        self.on_modified = on_modified
        self.modified = False

        self.sort_column = 'name'
        self.sort_reverse = False

        self.create_widgets()
        self.update_categories()
        self.refresh_list()

    def create_widgets(self):
        # Filter frame
        filter_frame = ttk.Frame(self, padding=5)
        filter_frame.pack(fill='x')

        ttk.Label(filter_frame, text="Search:").pack(side='left')
        self.search_var = tk.StringVar()
        self.search_var.trace_add('write', lambda *a: self.refresh_list())
        ttk.Entry(filter_frame, textvariable=self.search_var, width=20).pack(side='left', padx=5)

        ttk.Label(filter_frame, text="Category:").pack(side='left', padx=(10, 0))
        self.category_var = tk.StringVar(value="All")
        self.category_combo = ttk.Combobox(filter_frame, textvariable=self.category_var,
                                           values=["All"], width=18, state='readonly')
        self.category_combo.pack(side='left', padx=5)
        self.category_combo.bind('<<ComboboxSelected>>', lambda e: self.refresh_list())

        ttk.Label(filter_frame, text="Type:").pack(side='left', padx=(10, 0))
        self.type_var = tk.StringVar(value="All")
        type_combo = ttk.Combobox(filter_frame, textvariable=self.type_var,
                                  values=["All", "Buff", "Debuff", "Misc"], width=10, state='readonly')
        type_combo.pack(side='left', padx=5)
        self.type_var.trace_add('write', lambda *a: self.refresh_list())

        self.count_var = tk.StringVar(value="0 entries")
        ttk.Label(filter_frame, textvariable=self.count_var).pack(side='right', padx=10)

        # Tree view
        list_frame = ttk.Frame(self, padding=5)
        list_frame.pack(fill='both', expand=True)

        columns = ('name', 'ids', 'category', 'type', 'stacking')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', selectmode='browse')

        self.tree.heading('name', text='Name', command=lambda: self.sort_by('name'))
        self.tree.heading('ids', text='ID(s)', command=lambda: self.sort_by('ids'))
        self.tree.heading('category', text='Category', command=lambda: self.sort_by('category'))
        self.tree.heading('type', text='Type', command=lambda: self.sort_by('type'))
        self.tree.heading('stacking', text='Stack', command=lambda: self.sort_by('stacking'))

        self.tree.column('name', width=220, minwidth=100, stretch=True, anchor='w')
        self.tree.column('ids', width=180, minwidth=80, stretch=True, anchor='w')
        self.tree.column('category', width=120, minwidth=80, stretch=True, anchor='w')
        self.tree.column('type', width=60, minwidth=50, stretch=False, anchor='center')
        self.tree.column('stacking', width=50, minwidth=40, stretch=False, anchor='center')

        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        self.tree.bind('<Double-1>', lambda e: self.edit_buff())

        # Button frame
        btn_frame = ttk.Frame(self, padding=5)
        btn_frame.pack(fill='x')

        save_btn = ttk.Button(btn_frame, text="Save Database", command=self.save, width=BTN_MEDIUM)
        save_btn.pack(side='left', padx=2)
        add_tooltip(save_btn, "Save all buff entries to database file")
        ttk.Separator(btn_frame, orient='vertical').pack(side='left', fill='y', padx=10)

        add_btn = ttk.Button(btn_frame, text="Add", command=self.add_buff, width=BTN_SMALL)
        add_btn.pack(side='left', padx=2)
        add_tooltip(add_btn, "Create a new buff entry")
        edit_btn = ttk.Button(btn_frame, text="Edit", command=self.edit_buff, width=BTN_SMALL)
        edit_btn.pack(side='left', padx=2)
        add_tooltip(edit_btn, "Edit the selected buff entry")
        del_btn = ttk.Button(btn_frame, text="Delete", command=self.delete_buff, width=BTN_SMALL)
        del_btn.pack(side='left', padx=2)
        add_tooltip(del_btn, "Delete the selected buff entry")
        dup_btn = ttk.Button(btn_frame, text="Duplicate", command=self.duplicate_buff, width=BTN_MEDIUM)
        dup_btn.pack(side='left', padx=2)
        add_tooltip(dup_btn, "Copy the selected buff as a new entry")
        ttk.Separator(btn_frame, orient='vertical').pack(side='left', fill='y', padx=10)
        imp_btn = ttk.Button(btn_frame, text="Import...", command=self.import_buffs, width=BTN_MEDIUM)
        imp_btn.pack(side='left', padx=2)
        add_tooltip(imp_btn, "Import buff entries from a JSON file")
        exp_btn = ttk.Button(btn_frame, text="Export...", command=self.export_buffs, width=BTN_MEDIUM)
        exp_btn.pack(side='left', padx=2)
        add_tooltip(exp_btn, "Export selected buffs to a JSON file")

        # Status bar
        self.status_var = tk.StringVar(value="")
        ttk.Label(self, textvariable=self.status_var, style='StatusBar.TLabel').pack(fill='x', side='bottom')

    def update_categories(self):
        """Update category dropdown with current categories."""
        self.category_combo['values'] = ["All"] + self.database.categories

    def refresh_list(self):
        """Refresh the buff list based on current filters."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        search = self.search_var.get().lower()
        category = self.category_var.get()
        type_filter = self.type_var.get()

        buff_type = TYPE_FILTER_MAP.get(type_filter)

        filtered = self.database.search(
            search,
            category if category != "All" else None,
            buff_type=buff_type
        )
        filtered.sort(key=lambda b: self._get_sort_key(b), reverse=self.sort_reverse)

        for buff in filtered:
            ids = buff.get('ids', [])
            ids_str = format_ids_display(ids)

            type_str = buff.get('type', 'buff').capitalize()
            # Show stacking info with start value if not default
            if buff.get('stacking', False):
                stack_start = buff.get('stackStart', 1)
                stack_str = f"x{stack_start}+" if stack_start != 1 else "Yes"
            else:
                stack_str = ""

            self.tree.insert('', 'end', values=(
                buff.get('name', ''),
                ids_str,
                buff.get('category', ''),
                type_str,
                stack_str
            ))

        self.count_var.set(f"{len(filtered)} / {len(self.database.grouped_buffs)} entries")

    def sort_by(self, column):
        """Sort list by column."""
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False
        self.refresh_list()

    def _get_sort_key(self, buff):
        """Get sort key for a buff entry."""
        if self.sort_column == 'ids':
            ids = buff.get('ids', [])
            return ids[0] if ids else 0
        elif self.sort_column == 'name':
            return buff.get('name', '').lower()
        elif self.sort_column == 'category':
            return buff.get('category', '').lower()
        elif self.sort_column == 'type':
            return {'buff': 0, 'debuff': 1, 'misc': 2}.get(buff.get('type', 'buff'), 0)
        elif self.sort_column == 'stacking':
            return 0 if buff.get('stacking', False) else 1
        return ''

    def _get_selected_buff(self):
        """Get currently selected buff and its IDs."""
        selection = self.tree.selection()
        if not selection:
            return None, None
        item = self.tree.item(selection[0])
        # values = (name, ids, category, type, stacking)
        buff_name = item['values'][0]
        buff_type = item['values'][3].lower()  # "Buff" -> "buff", "Debuff" -> "debuff"

        # Match by name AND type to handle same-name entries (e.g., Lotus Miasma buff vs debuff)
        for buff in self.database.grouped_buffs:
            if buff['name'] == buff_name and buff.get('type', 'buff') == buff_type:
                return buff, buff.get('ids', [])
        return None, None

    def _check_id_collision(self, new_ids, exclude_ids=None):
        """Check if any IDs already exist in database. Returns overlapping set or None."""
        exclude = set(exclude_ids or [])
        for buff in self.database.buffs:
            existing = set(buff.get('ids', [])) - exclude
            overlap = new_ids & existing
            if overlap:
                return overlap
        return None

    def add_buff(self):
        """Add a new buff entry."""
        dialog = BuffEditDialog(self.winfo_toplevel(), "Add Buff", self.database.categories)
        self.winfo_toplevel().wait_window(dialog)

        if dialog.result:
            new_ids = set(dialog.result['ids'])
            overlap = self._check_id_collision(new_ids)
            if overlap:
                Messagebox.show_error(f"ID(s) {overlap} already exist!", title="Error")
                return

            self.database.add_buff(dialog.result)
            self._set_modified()
            self.update_categories()
            self.refresh_list()
            self.status_var.set(f"Added: {dialog.result['name']}")

    def edit_buff(self):
        """Edit selected buff entry."""
        buff, old_ids = self._get_selected_buff()
        if buff is None:
            Messagebox.show_warning("Select a buff to edit", title="Warning")
            return

        dialog = BuffEditDialog(self.winfo_toplevel(), "Edit Buff", self.database.categories, buff)
        self.winfo_toplevel().wait_window(dialog)

        if dialog.result:
            new_ids = set(dialog.result['ids'])
            overlap = self._check_id_collision(new_ids, exclude_ids=old_ids)
            if overlap:
                Messagebox.show_error(f"ID(s) {overlap} already exist!", title="Error")
                return

            self.database.update_buff(old_ids, dialog.result)
            self._set_modified()
            self.update_categories()
            self.refresh_list()
            self.status_var.set(f"Updated: {dialog.result['name']}")

    def delete_buff(self):
        """Delete selected buff entry."""
        buff, ids = self._get_selected_buff()
        if buff is None:
            Messagebox.show_warning("Select a buff to delete", title="Warning")
            return

        ids_str = format_ids_display(ids)

        if Messagebox.yesno(f"Delete '{buff['name']}' (IDs: {ids_str})?", title="Confirm Delete") == "Yes":
            self.database.remove_buff(ids)
            self._set_modified()
            self.update_categories()
            self.refresh_list()
            self.status_var.set(f"Deleted: {buff['name']}")

    def duplicate_buff(self):
        """Duplicate selected buff entry."""
        buff, _ = self._get_selected_buff()
        if buff is None:
            Messagebox.show_warning("Select a buff to duplicate", title="Warning")
            return

        new_buff = dict(buff)
        new_buff['ids'] = []
        new_buff['name'] = buff['name'] + " (copy)"

        dialog = BuffEditDialog(self.winfo_toplevel(), "Duplicate Buff", self.database.categories, new_buff)
        self.winfo_toplevel().wait_window(dialog)

        if dialog.result:
            new_ids = set(dialog.result['ids'])
            overlap = self._check_id_collision(new_ids)
            if overlap:
                Messagebox.show_error(f"ID(s) {overlap} already exist!", title="Error")
                return

            self.database.add_buff(dialog.result)
            self._set_modified()
            self.update_categories()
            self.refresh_list()
            self.status_var.set(f"Created: {dialog.result['name']}")

    def import_buffs(self):
        """Import buffs from JSON file."""
        path = filedialog.askopenfilename(
            title="Import Buff List",
            filetypes=[("JSON", "*.json"), ("All", "*.*")]
        )
        if not path:
            return

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            import_buffs = data if isinstance(data, list) else data.get('buffs', [])
            if not import_buffs:
                Messagebox.show_warning("No buffs found in file", title="Warning")
                return

            existing_ids = set()
            for buff in self.database.buffs:
                for bid in buff.get('ids', []):
                    existing_ids.add(bid)

            added = 0
            skipped = 0

            for buff in import_buffs:
                buff_ids = buff.get('ids', [buff.get('id')] if 'id' in buff else [])
                if any(bid in existing_ids for bid in buff_ids):
                    skipped += 1
                else:
                    # Ensure v2 format
                    if 'id' in buff and 'ids' not in buff:
                        buff['ids'] = [buff['id']]
                        del buff['id']
                    # Remove isDebuff if present, ensure type exists
                    if 'isDebuff' in buff:
                        if 'type' not in buff:
                            buff['type'] = 'debuff' if buff['isDebuff'] else 'buff'
                        del buff['isDebuff']
                    if 'type' not in buff:
                        buff['type'] = 'buff'

                    self.database.add_buff(buff)
                    for bid in buff_ids:
                        existing_ids.add(bid)
                    added += 1

            self._set_modified()
            self.update_categories()
            self.refresh_list()

            msg = f"Imported {added} buffs"
            if skipped > 0:
                msg += f" ({skipped} duplicates skipped)"
            self.status_var.set(msg)
            Messagebox.show_info(msg, title="Import Complete")

        except Exception as e:
            Messagebox.show_error(f"Failed to import:\n{e}", title="Error")

    def export_buffs(self):
        """Export filtered buffs to JSON file."""
        search = self.search_var.get().lower()
        category = self.category_var.get()
        type_filter = self.type_var.get()

        buff_type = TYPE_FILTER_MAP.get(type_filter)

        export_buffs = self.database.search(
            search,
            category if category != "All" else None,
            buff_type=buff_type
        )

        if not export_buffs:
            Messagebox.show_warning("No buffs to export (check filters)", title="Warning")
            return

        default_name = "Db_export"
        if category != "All":
            default_name = f"Db_{category.replace(' ', '_').replace('#', '')}"

        path = filedialog.asksaveasfilename(
            title="Export Buff List",
            initialfile=default_name,
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("All", "*.*")]
        )
        if not path:
            return

        try:
            data = {
                "version": 2,
                "description": "KzGrids buff list export",
                "buffs": export_buffs
            }
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self.status_var.set(f"Exported {len(export_buffs)} buffs")
            Messagebox.show_info(f"Exported {len(export_buffs)} buffs to:\n{path}", title="Export Complete")
        except Exception as e:
            Messagebox.show_error(f"Failed to export:\n{e}", title="Error")

    def save(self):
        """Save database to file."""
        self.assets_path.mkdir(exist_ok=True)
        db_path = self.assets_path / "Database.json"

        try:
            self.database.save(db_path)
            self.modified = False
            self.status_var.set(f"Database saved: {db_path}")
        except Exception as e:
            Messagebox.show_error(f"Failed to save database:\n{e}", title="Error")

    def _set_modified(self):
        """Mark database as modified."""
        self.modified = True
        if self.on_modified:
            self.on_modified()

    def is_modified(self):
        """Check if database has unsaved changes."""
        return self.modified
