import unittest
from itertools import islice

# test_stremlit_colour_pallet.py
from app.stremlit_colour_pallet import (
    MAGENTA, BLACK, WHITE, LIGHT_GRAY, DARK_GRAY,
    CATEGORY10_PALETTE, CATEGORY20_PALETTE,
    DEFAULT_PLOT_PALETTE, get_color_cycler
)

class TestStreamlitColorPallet(unittest.TestCase):

    def test_theme_colors(self):
        self.assertEqual(MAGENTA, "#E600E6")
        self.assertEqual(BLACK, "#000000")
        self.assertEqual(WHITE, "#FFFFFF")
        self.assertEqual(LIGHT_GRAY, "#969696")
        self.assertEqual(DARK_GRAY, "#323232")

    def test_category10_palette(self):
        expected_palette = [
            "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
            "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"
        ]
        self.assertEqual(CATEGORY10_PALETTE, expected_palette)

    def test_category20_palette(self):
        expected_palette = [
            "#1f77b4", "#aec7e8", "#ff7f0e", "#ffbb78", "#2ca02c", "#98df8a",
            "#d62728", "#ff9896", "#9467bd", "#c5b0d5", "#8c564b", "#c49c94",
            "#e377c2", "#f7b6d2", "#7f7f7f", "#c7c7c7", "#bcbd22", "#dbdb8d",
            "#17becf", "#9edae5"
        ]
        self.assertEqual(CATEGORY20_PALETTE, expected_palette)

    def test_default_plot_palette(self):
        self.assertEqual(DEFAULT_PLOT_PALETTE, CATEGORY10_PALETTE)

    def test_get_color_cycler(self):
        cycler = get_color_cycler(CATEGORY10_PALETTE)
        first_ten_colors = list(islice(cycler, 10))
        self.assertEqual(first_ten_colors, CATEGORY10_PALETTE)

        # Test cycling behavior
        next_color = next(cycler)
        self.assertEqual(next_color, CATEGORY10_PALETTE[0])  # Should cycle back to the first color

if __name__ == "__main__":
    unittest.main()