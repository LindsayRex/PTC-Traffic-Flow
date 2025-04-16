# app/streamlit_color_pallet.py
"""
Defines color constants based on the app's theme and provides
standard categorical color palettes for consistent use in visualizations.
"""

import streamlit as st
from streamlit.config import get_option

# --- Theme Colors ---
MAGENTA = "#E600E6" # RGB: 230, 0, 230 (Primary Accent)
BLACK = "#000000"   # RGB: 0, 0, 0 (Primary Background)
WHITE = "#FFFFFF"   # RGB: 255, 255, 255 (Primary Text)
LIGHT_GRAY = "#969696" # RGB: 150, 150, 150 (Secondary Background/Elements)
DARK_GRAY = "#323232"  # RGB: 50, 50, 50 (Sidebar/Widget Background/Borders)

def rgba(hex_color, opacity):
    """Converts a hex color to rgba with the given opacity."""
    hex_color = hex_color.lstrip('#')
    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, {opacity})"

# --- Opacity Variations ---
MAGENTA_80 = rgba(MAGENTA, 0.8)
MAGENTA_60 = rgba(MAGENTA, 0.6)
MAGENTA_40 = rgba(MAGENTA, 0.4)
MAGENTA_20 = rgba(MAGENTA, 0.2)
MAGENTA_05 = rgba(MAGENTA, 0.05)

BLACK_80 = rgba(BLACK, 0.8)
BLACK_60 = rgba(BLACK, 0.6)
BLACK_40 = rgba(BLACK, 0.4)
BLACK_20 = rgba(BLACK, 0.2)
BLACK_05 = rgba(BLACK, 0.05)

WHITE_80 = rgba(WHITE, 0.8)
WHITE_60 = rgba(WHITE, 0.6)
WHITE_40 = rgba(WHITE, 0.4)
WHITE_20 = rgba(WHITE, 0.2)
WHITE_05 = rgba(WHITE, 0.05)

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

CATEGORY10_PALETTE_80 = [rgba(color, 0.8) for color in CATEGORY10_PALETTE]
CATEGORY10_PALETTE_60 = [rgba(color, 0.6) for color in CATEGORY10_PALETTE]
CATEGORY10_PALETTE_40 = [rgba(color, 0.4) for color in CATEGORY10_PALETTE]
CATEGORY10_PALETTE_20 = [rgba(color, 0.2) for color in CATEGORY10_PALETTE]

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

CATEGORY20_PALETTE_80 = [rgba(color, 0.8) for color in CATEGORY20_PALETTE]
CATEGORY20_PALETTE_60 = [rgba(color, 0.6) for color in CATEGORY20_PALETTE]
CATEGORY20_PALETTE_40 = [rgba(color, 0.4) for color in CATEGORY20_PALETTE]
CATEGORY20_PALETTE_20 = [rgba(color, 0.2) for color in CATEGORY20_PALETTE]

# Select default palette to use in the app
# For most cases with limited categories (like road hierarchy, direction pairs), Category10 is often sufficient.
DEFAULT_PLOT_PALETTE = CATEGORY10_PALETTE

# --- Helper Function (Optional) ---
def get_color_cycler(palette=DEFAULT_PLOT_PALETTE):
    """Returns an iterator that cycles through the chosen palette."""
    from itertools import cycle
    return cycle(palette)