import unittest
from unittest.mock import patch, MagicMock, call
import sys
from pathlib import Path
import logging

# Mock streamlit and other heavy dependencies BEFORE importing the module under test
# This prevents top-level Streamlit calls during import
mock_st = MagicMock()
# Configure st.stop mock to raise SystemExit for relevant tests
mock_st.stop.side_effect = SystemExit

mock_db_utils = MagicMock()
mock_log_config = MagicMock()

# Mock the feature functions directly for load_feature_modules test
mock_render_station_profile = MagicMock(name="render_station_profile")
mock_render_peak_analysis = MagicMock(name="render_peak_analysis")
# ... create mocks for ALL feature functions imported in load_feature_modules

# --- FIX: Configure mock for stremlit_colour_pallet ---
mock_colour_pallet = MagicMock()
# Define the expected style strings
expected_title_style = "color: #E600E6; font-size: 42px; font-weight: bold;"
expected_content_style = "padding: 1rem;" # Or just "" if the value doesn't matter for tests
# Make STYLES behave like a dictionary for the required keys
mock_styles_dict = {
    "title": expected_title_style,
    "content": expected_content_style # Add the 'content' key
}
mock_colour_pallet.STYLES = mock_styles_dict
# --- End Fix ---

# Use patch.dict to insert mocks into sys.modules for general imports
modules = {
    'streamlit': mock_st,
    'app.db_utils': mock_db_utils,
    'app.log_config': mock_log_config,
    'app.stremlit_colour_pallet': mock_colour_pallet, # Use configured mock
}

# Apply mocks using patch.dict before importing the app
# This ensures the app imports the mocks, not the real modules
with patch.dict(sys.modules, modules):
    from app.main_app import (
        configure_page,
        initialize_logging,
        initialize_database,
        load_feature_modules,
        apply_custom_css,
        display_banner,
        display_sidebar_navigation,
        display_global_filters,
        render_home_page,
        render_feature_page,
        display_footer,
        main,
        LOGO_PATH # Import the constant to patch it
    )

class TestMainAppRefactored(unittest.TestCase):

    def setUp(self):
        """Reset mocks before each test."""
        mock_st.reset_mock()
        mock_db_utils.reset_mock()
        mock_log_config.reset_mock()
        mock_render_station_profile.reset_mock()
        mock_render_peak_analysis.reset_mock()
        # Reset the configured mock's specific attributes if necessary,
        # though reset_mock() on the parent might suffice.
        # mock_colour_pallet.reset_mock() # Optional, depends if STYLES needs reset

        mock_st.stop.side_effect = SystemExit
        mock_db_utils.init_db_resources.return_value = (MagicMock(name="engine"), MagicMock(name="session_factory"))

    def test_configure_page(self):
        """Test that st.set_page_config is called correctly."""
        configure_page()
        mock_st.set_page_config.assert_called_once_with(
            page_title="Traffic Data Analysis",
            page_icon="app/gfx/ptc-logo-white.png",
            layout="wide",
            initial_sidebar_state="expanded"
        )

    # FIX: Patch logging.getLogger directly
    @patch('logging.getLogger')
    def test_initialize_logging(self, mock_getLogger):
        """Test logging setup and logger retrieval."""
        mock_logger = MagicMock()
        mock_getLogger.return_value = mock_logger

        logger = initialize_logging()

        mock_log_config.setup_logging.assert_called_once()
        # The name passed to getLogger is __name__ from main_app.py
        mock_getLogger.assert_called_once_with('app.main_app')
        self.assertEqual(logger, mock_logger)
        mock_logger.info.assert_called_once_with("--- Streamlit App Logging Initialized ---")

    @patch('app.main_app.logging.getLogger')
    def test_initialize_database_success(self, mock_getLogger):
        """Test successful database initialization."""
        mock_logger = MagicMock()
        mock_getLogger.return_value = mock_logger
        mock_engine = MagicMock(name="engine")
        mock_session_factory = MagicMock(name="session_factory")
        mock_db_utils.init_db_resources.return_value = (mock_engine, mock_session_factory)

        engine, SessionFactory = initialize_database(mock_logger)

        mock_db_utils.init_db_resources.assert_called_once()
        self.assertEqual(engine, mock_engine)
        self.assertEqual(SessionFactory, mock_session_factory)
        mock_logger.info.assert_any_call("Attempting to initialize database resources...")
        mock_logger.info.assert_any_call("Database Engine and Session Factory initialized successfully (or retrieved from cache).")
        mock_st.error.assert_not_called()
        mock_st.stop.assert_not_called()

    @patch('app.main_app.logging.getLogger')
    def test_initialize_database_failure(self, mock_getLogger):
        """Test database initialization failure."""
        mock_logger = MagicMock()
        mock_getLogger.return_value = mock_logger
        mock_db_utils.init_db_resources.return_value = (None, None) # Simulate failure

        with self.assertRaises(SystemExit):
             initialize_database(mock_logger)

        mock_db_utils.init_db_resources.assert_called_once()
        mock_logger.error.assert_called_once()
        mock_st.error.assert_called_once_with("Fatal Error: Could not establish database connection. App cannot continue.")
        mock_st.stop.assert_called_once()

    # FIX: Patch the feature functions in their original modules
    @patch('app.features.feature_10_seasonal.render_seasonal_trend_analyzer', new=MagicMock(name="render_seasonal"))
    @patch('app.features.feature_9_hierarchy.render_hierarchy_benchmarking', new=MagicMock(name="render_hierarchy"))
    @patch('app.features.feature_8_directional.render_directional_flow_analysis', new=MagicMock(name="render_directional"))
    @patch('app.features.feature_7_snapshot.render_lga_suburb_snapshot', new=MagicMock(name="render_snapshot"))
    @patch('app.features.feature_6_quality.render_data_quality_overview', new=MagicMock(name="render_quality"))
    @patch('app.features.feature_5_weekday_weekend.render_weekday_weekend_comparison', new=MagicMock(name="render_weekday"))
    @patch('app.features.feature_4_heavy_vehicle.render_heavy_vehicle_explorer', new=MagicMock(name="render_heavy"))
    @patch('app.features.feature_3_corridor.render_corridor_comparison', new=MagicMock(name="render_corridor"))
    @patch('app.features.feature_2_peak.render_peak_analysis', new=mock_render_peak_analysis) # Use pre-defined mock
    @patch('app.features.feature_1_profile.render_station_profile', new=mock_render_station_profile) # Use pre-defined mock
    @patch('app.main_app.render_home_page', new=MagicMock(name="render_home_page")) # Patch local home page func
    @patch('app.main_app.logging.getLogger')
    def test_load_feature_modules_success(self, mock_getLogger, *mock_feature_funcs): # Order matters less now
        """Test loading feature modules successfully."""
        mock_logger = MagicMock()
        mock_getLogger.return_value = mock_logger

        pages = load_feature_modules(mock_logger)

        self.assertIn("Home", pages)
        self.assertIn("Station Profile", pages)
        # Check against the directly patched mock function
        self.assertEqual(pages["Station Profile"], mock_render_station_profile)
        self.assertEqual(pages["Peak Hour Analysis"], mock_render_peak_analysis)
        # ... add asserts for other features if needed
        mock_logger.info.assert_any_call("Loading feature modules...")
        mock_logger.info.assert_any_call("Feature modules loaded successfully.")


    @patch('app.main_app.LOGO_PATH')
    @patch('app.main_app.logging.getLogger')
    def test_display_banner_logo_exists(self, mock_getLogger, mock_logo_path):
        """Test banner display when logo exists."""
        mock_logger = MagicMock()
        mock_getLogger.return_value = mock_logger
        mock_logo_path.exists.return_value = True
        mock_logo_path.__str__.return_value = "mock/path/logo.svg"

        mock_col1, mock_col2 = MagicMock(), MagicMock()
        mock_st.columns.return_value = (mock_col1, mock_col2)

        display_banner(mock_logger, logo_path=mock_logo_path)

        mock_logo_path.exists.assert_called_once()
        mock_st.columns.assert_called_once_with([1, 5])
        mock_st.image.assert_called_once_with("mock/path/logo.svg", width=100)
        mock_st.markdown.assert_any_call(
            f"<h1 style='{expected_title_style}'>Traffic Data Analysis</h1>",
            unsafe_allow_html=True
        )
        mock_logger.warning.assert_not_called()

    @patch('app.main_app.LOGO_PATH')
    @patch('app.main_app.logging.getLogger')
    def test_display_banner_logo_missing(self, mock_getLogger, mock_logo_path):
        """Test banner display when logo is missing."""
        mock_logger = MagicMock()
        mock_getLogger.return_value = mock_logger
        mock_logo_path.exists.return_value = False
        mock_logo_path.resolve.return_value = "resolved/mock/path/logo.svg"

        display_banner(mock_logger, logo_path=mock_logo_path)

        mock_logo_path.exists.assert_called_once()
        mock_st.columns.assert_not_called()
        mock_st.error.assert_called_once_with("Logo file not found, banner title only.")
        mock_st.markdown.assert_called_once()
        mock_logger.warning.assert_called_once_with("Logo file not found at: resolved/mock/path/logo.svg")

    def test_display_sidebar_navigation(self):
        """Test sidebar navigation rendering."""
        mock_pages = {"Home": MagicMock(), "Feature1": MagicMock()}
        mock_st.sidebar.radio.return_value = "Home" # Simulate user selection

        selection = display_sidebar_navigation(mock_pages)

        self.assertEqual(selection, "Home")
        mock_st.sidebar.markdown.assert_called_once()
        mock_st.sidebar.radio.assert_called_once_with(
            "Select Feature:",
            list(mock_pages.keys()),
            index=0, # Home is first
            label_visibility="collapsed"
        )

    def test_render_home_page(self):
        """Test home page rendering."""
        render_home_page()

        # FIX: Define expected_markdown exactly as in render_home_page
        expected_markdown = f"""
        <div style='{expected_content_style}'>
            <h2>Welcome to Traffic Data Analysis</h2>
            <p>This application provides comprehensive traffic data analysis tools for NSW roads.</p>
            <h3>Key Features:</h3>
            <ul>
                <li>Real-time traffic monitoring</li>
                <li>Historical data analysis</li>
                <li>Peak hour patterns</li>
                <li>Vehicle classification insights</li>
            </ul>
            <h3>Getting Started:</h3>
            <p>Select a feature from the sidebar menu to begin exploring traffic data.</p>
        </div>
    """ # Note the indentation level of this closing triple quote

        # Check the call with the precisely matching string
        mock_st.markdown.assert_called_once_with(expected_markdown, unsafe_allow_html=True)

    @patch('app.main_app.logging.getLogger')
    def test_render_feature_page_success(self, mock_getLogger):
        """Test rendering a specific feature page."""
        mock_logger = MagicMock()
        mock_getLogger.return_value = mock_logger
        mock_feature_func = MagicMock(name="render_feature_1")
        mock_pages = {"Home": MagicMock(), "Feature1": mock_feature_func}

        render_feature_page("Feature1", mock_pages, mock_logger)

        mock_feature_func.assert_called_once()
        mock_logger.info.assert_called_once_with("Rendering feature: Feature1")
        mock_st.error.assert_not_called()

    @patch('app.main_app.logging.getLogger')
    def test_render_feature_page_error(self, mock_getLogger):
        """Test error handling when rendering a feature page."""
        mock_logger = MagicMock()
        mock_getLogger.return_value = mock_logger
        mock_feature_func = MagicMock(name="render_feature_1")
        mock_feature_func.side_effect = ValueError("Something went wrong") # Simulate error
        mock_pages = {"Home": MagicMock(), "Feature1": mock_feature_func}

        render_feature_page("Feature1", mock_pages, mock_logger)

        mock_feature_func.assert_called_once()
        mock_logger.error.assert_called_once() # Check error logged
        mock_st.error.assert_called_once_with("An error occurred while loading the 'Feature1' feature. Please check the logs.")


if __name__ == '__main__':
    unittest.main()
