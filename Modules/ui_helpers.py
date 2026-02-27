"""
KzBuilder — UI Helper Functions
Window position persistence and related utilities.
Extracted to avoid circular imports between kzbuilder.py and grids_tab.py.
"""

import tkinter as tk
from tkinter import ttk

# ============================================================================
# SHARED FONT CONSTANTS
# ============================================================================
FONT_TITLE = ('Segoe UI', 20, 'bold')
FONT_HEADING = ('Segoe UI', 14, 'bold')
FONT_SUBTITLE = ('Segoe UI', 12, 'bold')
FONT_SECTION = ('Segoe UI', 9, 'bold')
FONT_BODY = ('Segoe UI', 9)
FONT_FORM_LABEL = ('Segoe UI', 9)        # Form field labels (upgrade from 8pt FONT_SMALL)
FONT_SMALL_BOLD = ('Segoe UI', 8, 'bold')
FONT_SMALL = ('Segoe UI', 8)

# ============================================================================
# THEME COLOR CONSTANTS (darkly theme)
# ============================================================================
# Semantic colors for ttk widget foreground text
THEME_COLORS = {
    'heading':    '#FFFFFF',   # Section headings (was #333333)
    'body':       '#ADB5BD',   # Body/descriptions (was #555555, #666666)
    'muted':      '#888888',   # Hints, placeholders (was gray, #AAAAAA)
    'accent':     '#3498db',   # Links, emphasis (was #0066CC)
    'warning':    '#f39c12',   # Warnings (was #CC6600, orange)
    'danger':     '#e74c3c',   # Errors (was red)
    'success':    '#00bc8c',   # Success (was green)
    'info_value': '#3498db',   # Info display values (was blue)
}

# Colors for raw tk widgets (Canvas, Listbox, Text) that ttkbootstrap can't theme
TK_COLORS = {
    'bg':        '#222222',   # darkly background
    'input_bg':  '#2f2f2f',   # darkly input background
    'input_fg':  '#ffffff',   # darkly input text
    'select_bg': '#555555',   # darkly selection background
    'select_fg': '#ffffff',   # darkly selection text
    'border':    '#444444',   # subtle border
}


# ============================================================================
# LAYOUT CONSTANTS
# ============================================================================
PAD_TAB = 10              # Padding inside tab frames
PAD_SECTION = (0, 10)     # Vertical gap between sections
PAD_INNER = 12            # Padding inside LabelFrames
PAD_ROW = 4               # Vertical gap between setting rows
PAD_BUTTON_GAP = 2        # Horizontal gap between buttons
PAD_TIP_BAR = (0, 4)      # Vertical padding for tip bar

# Button width standards
BTN_SMALL = 7             # Add, Edit, Delete, Clear, Copy
BTN_MEDIUM = 12           # Export, Import, Reset, Browse
BTN_LARGE = 20            # Build & Install, Generate & Install

# Module accent colors (for Welcome cards & section accents)
MODULE_COLORS = {
    'grids':      '#3498db',   # Blue
    'castbars':   '#00bc8c',   # Green
    'timers':     '#f39c12',   # Orange
    'damageinfo': '#e74c3c',   # Red
    'stopwatch':  '#9b59b6',   # Purple
}

# Grid type accent colors (player vs target differentiation)
GRID_TYPE_COLORS = {
    'player': '#3498db',   # Blue
    'target': '#e67e22',   # Orange
}

# Hardcoded AS2 colors used by KzTimers in-game rendering.
# KzStopwatch button/shadow colors are now user-configurable (see stopwatch_settings.py).
# These values serve as defaults/fallbacks for KzTimers and preview rendering.
AS2_COLORS = {
    'border':        '#3A3A30',
    'bg':            '#0D0D0D',
    'text':          '#CCCCCC',
    'button_bg':     '#1A1A18',
    'button_border': '#4A4A40',
    'shadow':        '#111111',
    'disabled':      '#555555',
    'start':         '#99DD66',
    'pause':         '#FFE066',
    'stop':          '#FF7744',
    'dot_active':    '#99DD66',
    'dot_armed':     '#FFE066',
    'dot_idle':      '#555555',
}


def blend_alpha(fg_hex: str, bg_hex: str, alpha: int) -> str:
    """Blend foreground color over background at given alpha (0-100).
    Used to simulate AS2 opacity on tkinter Canvas (which lacks transparency).
    """
    fr, fg, fb = int(fg_hex[1:3], 16), int(fg_hex[3:5], 16), int(fg_hex[5:7], 16)
    br, bg_, bb = int(bg_hex[1:3], 16), int(bg_hex[3:5], 16), int(bg_hex[5:7], 16)
    a = max(0, min(alpha, 100)) / 100.0
    r = int(fr * a + br * (1 - a))
    g = int(fg * a + bg_ * (1 - a))
    b = int(fb * a + bb * (1 - a))
    return f'#{r:02x}{g:02x}{b:02x}'


def create_rounded_rect(canvas, x1, y1, x2, y2, radius, **kwargs):
    """Draw a rounded rectangle on a tkinter Canvas."""
    if radius <= 0:
        return canvas.create_rectangle(x1, y1, x2, y2, **kwargs)
    r = min(radius, (x2 - x1) / 2, (y2 - y1) / 2)
    points = [
        x1 + r, y1,   x2 - r, y1,   x2, y1,   x2, y1 + r,
        x2, y2 - r,   x2, y2,   x2 - r, y2,   x1 + r, y2,
        x1, y2,   x1, y2 - r,   x1, y1 + r,   x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


# ============================================================================
# UI HELPER WIDGETS
# ============================================================================
def create_tip_bar(parent, text):
    """Create a compact single-line tip bar replacing verbose description boxes."""
    tip_frame = ttk.Frame(parent)
    tip_frame.pack(fill='x', padx=PAD_TAB, pady=PAD_TIP_BAR)
    ttk.Label(tip_frame, text="?", font=FONT_SMALL_BOLD,
              foreground=THEME_COLORS['accent'], width=2).pack(side='left')
    ttk.Label(tip_frame, text=text, font=FONT_SMALL,
              foreground=THEME_COLORS['muted']).pack(side='left', fill='x')
    return tip_frame


def create_profile_info_bar(parent, profile_label, extra_labels=None):
    """Create the profile indicator bar used on all tabs.

    Args:
        parent: Parent frame
        profile_label: StringVar for profile name
        extra_labels: Optional list of StringVar to append with separators
    Returns:
        The info_bar Frame
    """
    info_bar = ttk.Frame(parent)
    info_bar.pack(fill='x', padx=PAD_TAB, pady=(0, 4))
    ttk.Label(info_bar, textvariable=profile_label,
              font=FONT_SMALL_BOLD, foreground=THEME_COLORS['accent']).pack(side='left')
    if extra_labels:
        for label_var in extra_labels:
            ttk.Label(info_bar, text="  |  ", font=FONT_SMALL,
                      foreground=THEME_COLORS['muted']).pack(side='left')
            ttk.Label(info_bar, textvariable=label_var,
                      font=FONT_SMALL, foreground=THEME_COLORS['body']).pack(side='left')
    return info_bar


def fill_canvas_solid(canvas, color):
    """Fill a canvas with a solid color rectangle, redrawing on resize.

    Use this instead of bg= when ttkbootstrap theme overrides background colors.
    Drawn shapes (create_rectangle) are immune to theme overrides.
    """
    def _redraw(event):
        canvas.delete('accent_fill')
        if event.width > 1 and event.height > 1:
            canvas.create_rectangle(0, 0, event.width, event.height,
                                    fill=color, outline='', tags='accent_fill')
    canvas.bind('<Configure>', _redraw)


def bind_card_events(card_border, color, var=None):
    """Bind hover highlight and optional click-to-toggle on a card and all descendants.

    Hover uses debounced enter/leave (10ms) so the highlight stays active when
    moving between child widgets inside the card.  If var (BooleanVar) is given,
    clicking anywhere toggles it (skipping ttk.Checkbutton to avoid double-toggle).
    """
    def on_enter(e):
        """Cancel any pending leave timer and apply the hover highlight."""
        if hasattr(card_border, '_hover_after') and card_border._hover_after is not None:
            card_border.after_cancel(card_border._hover_after)
            card_border._hover_after = None
        card_border.config(highlightbackground='#FFFFFF', highlightcolor='#FFFFFF')

    def on_leave(e):
        """Schedule a debounced restore of the default border color."""
        card_border._hover_after = card_border.after(
            10, lambda: card_border.config(highlightbackground=color, highlightcolor=color))

    def on_click(e):
        """Toggle the linked BooleanVar, skipping Checkbuttons to avoid double-toggle."""
        if isinstance(e.widget, ttk.Checkbutton):
            return
        var.set(not var.get())

    def bind_recursive(widget):
        """Bind hover and click events to a widget and all its descendants."""
        widget.bind('<Enter>', on_enter, add='+')
        widget.bind('<Leave>', on_leave, add='+')
        if var is not None:
            widget.bind('<Button-1>', on_click, add='+')
        for child in widget.winfo_children():
            bind_recursive(child)

    card_border._hover_after = None
    bind_recursive(card_border)


def add_tooltip(widget, text):
    """Add a hover tooltip to any widget."""
    from ttkbootstrap.tooltip import ToolTip
    ToolTip(widget, text=text, delay=400)


def create_section_header(parent, text, color=None):
    """Small bold label with optional left-side colored accent dot."""
    frame = ttk.Frame(parent)
    if color:
        dot = tk.Canvas(frame, width=6, height=6, highlightthickness=0,
                        bg=TK_COLORS['bg'])
        dot.pack(side='left', padx=(0, 6), pady=1)
        dot.create_oval(0, 0, 6, 6, fill=color, outline=color)
    ttk.Label(frame, text=text, font=FONT_SMALL_BOLD,
              foreground=THEME_COLORS['body']).pack(side='left')
    return frame


class CollapsibleSection(ttk.Frame):
    """A section with a clickable header that shows/hides its content.

    The header shows an arrow indicator, title text, and optional right-side
    widgets (passed via add_header_widget). The content frame is toggled
    via pack/pack_forget.

    Usage:
        section = CollapsibleSection(parent, "Grid Name", initially_open=True)
        section.pack(fill='x', pady=2)
        # Add widgets to section.header_frame (right side) and section.content
        ttk.Label(section.content, text="Settings go here").pack()
    """

    def __init__(self, parent, title="", accent_color=None, initially_open=False,
                 badge_text=None, badge_color=None):
        """Initialize a collapsible section with a clickable header and togglable content area."""
        super().__init__(parent)
        self._is_open = initially_open

        # --- Header bar (always visible) ---
        self.header_frame = ttk.Frame(self)
        self.header_frame.pack(fill='x')

        # Clickable left side: arrow + accent + title + badge + summary
        left = ttk.Frame(self.header_frame)
        left.pack(side='left', fill='x', expand=True)
        clickable = [left]

        arrow_text = "\u25BC" if initially_open else "\u25B6"
        self._arrow_label = ttk.Label(
            left, text=arrow_text, font=FONT_SMALL,
            foreground=THEME_COLORS['muted'], width=2
        )
        self._arrow_label.pack(side='left')
        clickable.append(self._arrow_label)

        if accent_color:
            accent = tk.Canvas(left, width=3, height=16,
                               highlightthickness=0, bg=accent_color)
            accent.pack(side='left', padx=(0, 6))

        self._title_label = ttk.Label(
            left, text=title, font=FONT_SECTION,
            foreground=THEME_COLORS['heading']
        )
        self._title_label.pack(side='left')
        clickable.append(self._title_label)

        # Optional type badge (always visible, even when expanded)
        if badge_text:
            self._badge_label = ttk.Label(
                left, text=badge_text, font=FONT_SMALL,
                foreground=badge_color or THEME_COLORS['muted']
            )
            self._badge_label.pack(side='left', padx=(8, 0))
            clickable.append(self._badge_label)

        # Optional summary label (shown when collapsed, hidden when expanded)
        self._summary_label = ttk.Label(
            left, text="", font=FONT_SMALL,
            foreground=THEME_COLORS['muted']
        )
        self._summary_label.pack(side='left', padx=(10, 0))
        clickable.append(self._summary_label)

        # Bind click + hover on all header elements
        for widget in clickable:
            widget.bind('<Button-1>', lambda e: self.toggle())
            widget.bind('<Enter>', lambda e: self._arrow_label.config(
                foreground=THEME_COLORS['heading']))
            widget.bind('<Leave>', lambda e: self._arrow_label.config(
                foreground=THEME_COLORS['muted']))

        # --- Content area (toggled) ---
        self.content = ttk.Frame(self)
        if initially_open:
            self.content.pack(fill='x', padx=(14, 0), pady=(4, 0))

    def toggle(self):
        """Toggle content visibility."""
        if self._is_open:
            self.collapse()
        else:
            self.expand()

    def expand(self):
        """Show content, update arrow."""
        if not self._is_open:
            self._is_open = True
            self._arrow_label.config(text="\u25BC")
            self.content.pack(fill='x', padx=(14, 0), pady=(4, 0))
            self._summary_label.pack_forget()

    def collapse(self):
        """Hide content, update arrow."""
        if self._is_open:
            self._is_open = False
            self._arrow_label.config(text="\u25B6")
            self.content.pack_forget()
            # Re-show summary after title
            self._summary_label.pack(side='left', padx=(10, 0),
                                     in_=self._title_label.master)

    def set_title(self, text):
        """Update the header title."""
        self._title_label.config(text=text)

    def set_summary(self, text):
        """Set the summary text shown when collapsed."""
        self._summary_label.config(text=text)

    @property
    def is_open(self):
        """Return whether the section content is currently visible."""
        return self._is_open


# ============================================================================
# RAW TK WIDGET STYLING
# ============================================================================
def style_tk_listbox(listbox):
    """Style a raw tk.Listbox to match the darkly theme."""
    listbox.configure(
        bg=TK_COLORS['input_bg'], fg=TK_COLORS['input_fg'],
        selectbackground=TK_COLORS['select_bg'], selectforeground=TK_COLORS['select_fg'],
        highlightbackground=TK_COLORS['border'], highlightcolor=TK_COLORS['border'])


def style_tk_text(text_widget):
    """Style a raw tk.Text widget to match the darkly theme."""
    text_widget.configure(
        bg=TK_COLORS['input_bg'], fg=TK_COLORS['input_fg'],
        insertbackground=TK_COLORS['input_fg'],
        selectbackground=TK_COLORS['select_bg'], selectforeground=TK_COLORS['select_fg'],
        highlightbackground=TK_COLORS['border'], highlightcolor=TK_COLORS['border'])


def style_tk_canvas(canvas):
    """Style a raw tk.Canvas to match the darkly theme."""
    canvas.configure(bg=TK_COLORS['bg'], highlightthickness=0)


def apply_dark_titlebar(window):
    """Apply dark title bar on Windows 11 via pywinstyles."""
    try:
        import pywinstyles
        pywinstyles.apply_style(window, 'dark')
        pywinstyles.change_header_color(window, '#222222')
    except (ImportError, Exception):
        pass  # Silently skip if pywinstyles unavailable or not on Windows 11


# ============================================================================
# SETTINGS REFERENCE (set once at startup via init_settings)
# ============================================================================
_settings = None


def init_settings(settings):
    """Store the app settings reference. Call once from KzBuilder.__init__."""
    global _settings
    _settings = settings


# ============================================================================
# WINDOW POSITION HELPERS
# ============================================================================
def clamp_to_screen(x, y, width, height):
    """Clamp window coordinates so the window stays within screen bounds."""
    try:
        root = tk._default_root
        if root:
            screen_w = root.winfo_screenwidth()
            screen_h = root.winfo_screenheight()
        else:
            screen_w, screen_h = 1920, 1080
    except (tk.TclError, AttributeError):
        screen_w, screen_h = 1920, 1080
    x = max(0, min(x, screen_w - width))
    y = max(0, min(y, screen_h - height - 50))
    return x, y


def save_window_position(window_name, x, y, width=None, height=None):
    """Persist a window's position and optional size to settings."""
    if _settings:
        pos_data = {'x': x, 'y': y}
        if width is not None:
            pos_data['width'] = width
        if height is not None:
            pos_data['height'] = height
        _settings.set(f'window_pos_{window_name}', pos_data)
        _settings.save()


def restore_window_position(window, window_name, default_width, default_height, parent=None, resizable=True):
    """Restore a window's saved position and size, or center it as a fallback."""
    pos_data = _settings.get(f'window_pos_{window_name}') if _settings else None

    if pos_data:
        x = pos_data.get('x', 0)
        y = pos_data.get('y', 0)
        width = pos_data.get('width', default_width) if resizable else default_width
        height = pos_data.get('height', default_height) if resizable else default_height
    else:
        width, height = default_width, default_height
        if parent:
            x = parent.winfo_rootx() + (parent.winfo_width() - width) // 2
            y = parent.winfo_rooty() + (parent.winfo_height() - height) // 2
        else:
            try:
                screen_w = window.winfo_screenwidth()
                screen_h = window.winfo_screenheight()
            except (tk.TclError, RuntimeError, AttributeError):
                screen_w, screen_h = 1920, 1080
            x = (screen_w - width) // 2
            y = (screen_h - height) // 2

    x, y = clamp_to_screen(x, y, width, height)
    window.geometry(f"{width}x{height}+{x}+{y}")


def bind_window_position_save(window, window_name, save_size=True):
    """Bind a debounced Configure handler that auto-saves window position on move or resize."""
    save_timer = [None]  # Mutable container for closure

    def _do_save():
        save_timer[0] = None
        if save_size:
            save_window_position(window_name, window.winfo_x(), window.winfo_y(),
                                window.winfo_width(), window.winfo_height())
        else:
            save_window_position(window_name, window.winfo_x(), window.winfo_y())

    def on_configure(event):
        """Schedule a debounced position save when the window is moved or resized."""
        if event.widget == window and getattr(window, '_pos_initialized', False):
            # Debounce: only save 300ms after the last configure event
            if save_timer[0] is not None:
                window.after_cancel(save_timer[0])
            save_timer[0] = window.after(300, _do_save)

    window._pos_initialized = False
    window.after(500, lambda: setattr(window, '_pos_initialized', True))
    window.bind('<Configure>', on_configure)


def get_setting(key, default=None):
    """Read a single setting value. For use by dialogs that need to persist UI state."""
    if _settings:
        return _settings.get(key, default)
    return default


def set_setting(key, value):
    """Write a single setting value and save."""
    if _settings:
        _settings.set(key, value)
        _settings.save()


# ============================================================================
# CUSTOM TTK STYLES
# ============================================================================
def setup_custom_styles(root):
    """Configure custom ttk styles for a more polished look. Call once at startup."""
    style = ttk.Style()

    # Notebook tabs: more padding, slightly larger text
    style.configure('TNotebook.Tab', padding=[16, 6], font=('Segoe UI', 9))

    # Status bar: darker bg, integrated feel (replaces relief='sunken')
    style.configure('StatusBar.TLabel',
                    padding=[10, 5],
                    font=('Segoe UI', 8),
                    background='#1a1a1a',
                    foreground='#888888')

    # Card-style LabelFrame
    style.configure('Card.TLabelframe', borderwidth=1)
    style.configure('Card.TLabelframe.Label',
                    font=('Segoe UI', 9, 'bold'),
                    foreground='#ADB5BD')


# ============================================================================
# COLOR SWATCH WIDGET
# ============================================================================
class ColorSwatch(tk.Canvas):
    """Modern color swatch with rounded corners, hover effect, and click-to-pick.

    Replaces bare tk.Canvas/tk.Frame swatches. Handles RRGGBB, #RRGGBB, 0xRRGGBB.

    Args:
        parent: Parent widget
        color_var: Optional StringVar to sync with (reads on trace)
        on_change: Callback(hex_color_str) when user picks a new color
        initial_color: Starting color if no color_var (default '#FFFFFF')
    """
    WIDTH = 28
    HEIGHT = 20
    RADIUS = 3
    BORDER_IDLE = '#444444'
    BORDER_HOVER = '#888888'

    def __init__(self, parent, color_var=None, on_change=None, initial_color='#FFFFFF', **kwargs):
        """Initialize a color swatch canvas with optional variable binding and click-to-pick."""
        kwargs.setdefault('highlightthickness', 0)
        kwargs.setdefault('cursor', 'hand2')
        super().__init__(parent, width=self.WIDTH, height=self.HEIGHT, **kwargs)
        self.configure(bg=TK_COLORS['bg'])
        self._color_var = color_var
        self._on_change = on_change
        self._color = initial_color

        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
        self.bind('<Button-1>', self._on_click)

        if color_var:
            color_var.trace_add('write', lambda *_: self._sync_from_var())
            self._sync_from_var()
        else:
            self._draw(self.BORDER_IDLE)

    def set_color(self, hex_color):
        """Programmatically update the displayed color."""
        self._color = self._normalize(hex_color)
        self._draw(self.BORDER_IDLE)

    def get_color(self):
        """Return the current displayed color as #RRGGBB."""
        return self._color

    def _sync_from_var(self):
        """Read color from the linked StringVar."""
        raw = self._color_var.get().strip()
        if raw:
            self._color = self._normalize(raw)
            self._draw(self.BORDER_IDLE)

    @staticmethod
    def _normalize(raw):
        """Accept RRGGBB, #RRGGBB, 0xRRGGBB → #RRGGBB."""
        raw = raw.strip()
        if raw.startswith('0x') or raw.startswith('0X'):
            return '#' + raw[2:]
        if not raw.startswith('#'):
            return '#' + raw
        return raw

    def _draw(self, border_color):
        self.delete('all')
        create_rounded_rect(self, 1, 1, self.WIDTH - 1, self.HEIGHT - 1,
                            self.RADIUS, fill=self._color, outline=border_color)

    def _on_enter(self, event):
        self._draw(self.BORDER_HOVER)

    def _on_leave(self, event):
        self._draw(self.BORDER_IDLE)

    def _on_click(self, event):
        from ttkbootstrap.dialogs import ColorChooserDialog
        cd = ColorChooserDialog(initialcolor=self._color, title="Choose Color")
        cd.show()
        if cd.result:
            new_color = cd.result.hex
            self._color = new_color
            self._draw(self.BORDER_HOVER)
            if self._on_change:
                self._on_change(new_color)


# ============================================================================
# SCROLLABLE FRAME HELPER
# ============================================================================
def create_scrollable_frame(parent):
    """Create a scrollable frame with canvas + scrollbar + mousewheel binding.

    Returns (outer_frame, inner_frame, canvas).
    Pack outer_frame with fill='both', expand=True.
    Add widgets to inner_frame.
    """
    outer = ttk.Frame(parent)
    canvas = tk.Canvas(outer, highlightthickness=0, borderwidth=0)
    scrollbar = ttk.Scrollbar(outer, orient='vertical', command=canvas.yview)
    inner = ttk.Frame(canvas)

    inner.bind('<Configure>',
               lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
    canvas_window = canvas.create_window((0, 0), window=inner, anchor='nw')
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side='left', fill='both', expand=True)
    scrollbar.pack(side='right', fill='y')
    style_tk_canvas(canvas)

    def _on_canvas_configure(event):
        canvas.itemconfig(canvas_window, width=event.width)
    canvas.bind('<Configure>', _on_canvas_configure)
    bind_canvas_mousewheel(canvas, inner)

    return outer, inner, canvas


# ============================================================================
# CANVAS MOUSEWHEEL SCROLLING
# ============================================================================
def disable_mousewheel_on_inputs(root):
    """Remove class-level mousewheel bindings from Spinbox, Combobox, and Scale.

    ttkbootstrap adds <MouseWheel> bindings to TSpinbox and TCombobox that
    intercept scroll events, changing widget values when the user is just
    trying to scroll the parent panel. Call once at startup.
    """
    root.unbind_class('TSpinbox', '<MouseWheel>')
    root.unbind_class('TCombobox', '<MouseWheel>')
    root.unbind_class('TScale', '<MouseWheel>')
    root.unbind_class('Scale', '<MouseWheel>')


# Set of canvas widgets registered for mousewheel scrolling.
# Used by the global handler to find which canvas to scroll.
_scrollable_canvases = set()


def _global_mousewheel_handler(event):
    """Global mousewheel handler that scrolls the correct canvas.

    Walks up the widget tree from the event target to find a registered
    scrollable canvas. This works even when the mouse is over child widgets
    (labels, frames, buttons, etc.) inside the scrollable area.
    """
    widget = event.widget
    # Walk up the widget tree looking for a registered scrollable canvas
    try:
        while widget is not None:
            if widget in _scrollable_canvases:
                widget.yview_scroll(int(-1 * (event.delta / 120)), "units")
                return "break"
            widget = widget.master
    except (AttributeError, tk.TclError):
        pass


def bind_canvas_mousewheel(canvas, *extra_widgets):
    """Bind mousewheel scrolling to a canvas.

    Registers the canvas so the global mousewheel handler can find it.
    Scrolling works anywhere inside the canvas or its child widgets.
    Extra widgets parameter is accepted but ignored (kept for call-site convenience).
    """
    _scrollable_canvases.add(canvas)

    # Install the global handler once on the root window
    root = canvas.winfo_toplevel()
    if not getattr(root, '_mousewheel_handler_installed', False):
        root.bind_all('<MouseWheel>', _global_mousewheel_handler)
        root._mousewheel_handler_installed = True

    # Clean up when canvas is destroyed
    def _on_destroy(event):
        if event.widget is canvas:
            _scrollable_canvases.discard(canvas)
    canvas.bind('<Destroy>', _on_destroy)
