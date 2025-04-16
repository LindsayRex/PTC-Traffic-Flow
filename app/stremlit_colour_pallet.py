# app/streamlit_color_pallet.py
"""
Defines color constants based on the app's theme and provides
standard categorical color palettes for consistent use in visualizations.
"""

# --- Theme Colors ---
MAGENTA = "#E600E6" # RGB: 230, 0, 230 (Primary Accent)
BLACK = "#000000"   # RGB: 0, 0, 0 (Primary Background)
WHITE = "#FFFFFF"   # RGB: 255, 255, 255 (Primary Text)
LIGHT_GRAY = "#969696" # RGB: 150, 150, 150 (Secondary Background/Elements)
DARK_GRAY = "#323232"  # RGB: 50, 50, 50 (Sidebar/Widget Background/Borders)

# --- Categorical Color Palettes ---

# Bokeh/D3 Category10 palette: Good for up to 10 distinct categories.
# Source: https://docs.bokeh.org/en/latest/docs/reference/palettes.html#bokeh-palettes-category10
CATEGORY10_PALETTE = [
    "#1f77b4",  # Blue
    "#ff7f0e",  # Orange
    "#2ca02c",  # Green
    "#d62728",  # Red
    "#9467bd",  # Purple
    "#8c564b",  # Brown
    "#e377c2",  # Pink
    "#7f7f7f",  # Gray
    "#bcbd22",  # Olive
    "#17becf"   # Cyan
]

# Bokeh/D3 Category20 palette: Good for up to 20 distinct categories, pairs related colors.
# Source: https://docs.bokeh.org/en/latest/docs/reference/palettes.html#bokeh-palettes-category20
CATEGORY20_PALETTE = [
    "#1f77b4", "#aec7e8", # Blue pair
    "#ff7f0e", "#ffbb78", # Orange pair
    "#2ca02c", "#98df8a", # Green pair
    "#d62728", "#ff9896", # Red pair
    "#9467bd", "#c5b0d5", # Purple pair
    "#8c564b", "#c49c94", # Brown pair
    "#e377c2", "#f7b6d2", # Pink pair
    "#7f7f7f", "#c7c7c7", # Gray pair
    "#bcbd22", "#dbdb8d", # Olive pair
    "#17becf", "#9edae5"  # Cyan pair
]

# Select default palette to use in the app
# For most cases with limited categories (like road hierarchy, direction pairs), Category10 is often sufficient.
DEFAULT_PLOT_PALETTE = CATEGORY10_PALETTE

# --- Helper Function (Optional) ---
def get_color_cycler(palette=DEFAULT_PLOT_PALETTE):
    """Returns an iterator that cycles through the chosen palette."""
    from itertools import cycle
    return cycle(palette)


# Theme Colors
MAGENTA = "#E600E6"  # RGB: 230, 0, 230 (Primary Accent)
BLACK = "#000000"    # RGB: 0, 0, 0 (Primary Background)
WHITE = "#FFFFFF"    # RGB: 255, 255, 255 (Primary Text)
LIGHT_GRAY = "#969696"  # RGB: 150, 150, 150 (Secondary Background)
DARK_GRAY = "#323232"   # RGB: 50, 50, 50 (Sidebar/Widget Background)

# Style Configuration
STYLES = {
    "title": f"color: {MAGENTA}; font-size: 42px; font-weight: bold;",
    "banner": f"background-color: {MAGENTA}; padding: 1rem; margin-bottom: 2rem;",
    "content": f"background-color: {LIGHT_GRAY}; padding: 2rem; border-radius: 5px;",
    "sidebar": f"background-color: {DARK_GRAY}; color: {WHITE};"
}