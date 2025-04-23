import unittest
from unittest.mock import patch, MagicMock
import sys

# Patch sys.modules BEFORE importing app.main_app
mock_streamlit = MagicMock()
mock_streamlit.columns.return_value = (MagicMock(), MagicMock())
mock_logger = MagicMock()

# Create a mock for app.db_utils with a proper init_db_resources
mock_db_utils = MagicMock()
mock_db_utils.init_db_resources.return_value = (MagicMock(), MagicMock())

modules = {
    'streamlit': mock_streamlit,
    'app.log_config': MagicMock(),
    'app.stremlit_colour_pallet': MagicMock(),
    'app.db_utils': mock_db_utils,  # Use the custom mock here
    'app.features.feature_1_profile': MagicMock(),
    'app.features.feature_2_peak': MagicMock(),
    'app.features.feature_3_corridor': MagicMock(),
    'app.features.feature_4_heavy_vehicle': MagicMock(),
    'app.features.feature_5_weekday_weekend': MagicMock(),
    'app.features.feature_6_quality': MagicMock(),
    'app.features.feature_7_snapshot': MagicMock(),
    'app.features.feature_8_directional': MagicMock(),
    'app.features.feature_9_hierarchy': MagicMock(),
    'app.features.feature_10_seasonal': MagicMock(),
}
with patch.dict(sys.modules, modules):
    from app.main_app import init_db_resources, PAGES

class TestMainApp(unittest.TestCase):

    @patch('app.main_app.logger', new=mock_logger)
    @patch('app.main_app.init_db_resources')
    def test_database_initialization_success(self, mock_init_db_resources, mock_logger):
        mock_engine = MagicMock()
        mock_session_factory = MagicMock()
        mock_init_db_resources.return_value = (mock_engine, mock_session_factory)
        engine, session_factory = init_db_resources()
        self.assertIsNotNone(engine)
        self.assertIsNotNone(session_factory)
        mock_logger.info.assert_any_call("Database Engine and Session Factory initialized successfully (or retrieved from cache).")

    @patch('app.main_app.logger', new=mock_logger)
    @patch('app.main_app.init_db_resources')
    @patch('app.main_app.st')
    def test_database_initialization_failure(self, mock_st, mock_init_db_resources, mock_logger):
        mock_init_db_resources.return_value = (None, None)
        engine, session_factory = init_db_resources()
        self.assertIsNone(engine)
        self.assertIsNone(session_factory)
        mock_logger.error.assert_any_call("Database Engine or Session Factory failed to initialize during startup. Stopping app.")
        mock_st.error.assert_called_with("Fatal Error: Could not establish database connection. App cannot continue.")
        mock_st.stop.assert_called_once()

    @patch('app.main_app.st.sidebar.radio')
    def test_sidebar_navigation(self, mock_radio):
        mock_radio.return_value = "Station Profile"
        selected_function = PAGES[mock_radio.return_value]
        self.assertIsNotNone(selected_function)

    @patch('app.main_app.Path.exists')
    @patch('app.main_app.st')
    def test_logo_display(self, mock_st, mock_path_exists):
        mock_path_exists.return_value = True
        logo_path = Path("app/gfx/ptc-logo-white.svg")
        if logo_path.exists():
            mock_st.image.assert_called_once_with(str(logo_path), width=100)
        else:
            mock_logger.warning.assert_called_once_with(f"Logo file not found at: {logo_path.resolve()}")
            mock_st.error.assert_called_once_with("Logo file not found")

    @patch('app.main_app.st.markdown')
    def test_home_page_rendering(self, mock_markdown):
        home_content = """
            <div style='{STYLES["content"]}'>
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
        """
        mock_markdown.assert_called_with(home_content, unsafe_allow_html=True)

if __name__ == '__main__':
    unittest.main()