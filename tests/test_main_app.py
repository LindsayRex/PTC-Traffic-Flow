import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Mock streamlit and other heavy dependencies BEFORE importing the module under test
mock_st = MagicMock()
mock_st.stop.side_effect = SystemExit

mock_db_utils = MagicMock()
mock_log_config = MagicMock()
mock_render_station_profile = MagicMock(name="render_station_profile")
mock_render_peak_analysis = MagicMock(name="render_peak_analysis")

mock_colour_pallet = MagicMock()
expected_title_style = "color: #E600E6; font-size: 42px; font-weight: bold;"
expected_content_style = "padding: 1rem;"
mock_styles_dict = {
    "title": expected_title_style,
    "content": expected_content_style
}
mock_colour_pallet.STYLES = mock_styles_dict

modules = {
    'streamlit': mock_st,
    'app.db_utils': mock_db_utils,
    'app.log_config': mock_log_config,
    'app.stremlit_colour_pallet': mock_colour_pallet,
}

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
        LOGO_PATH
    )

@pytest.fixture
def reset_mocks():
    mock_st.reset_mock()
    mock_db_utils.reset_mock()
    mock_log_config.reset_mock()
    mock_render_station_profile.reset_mock()
    mock_render_peak_analysis.reset_mock()
    mock_st.stop.side_effect = SystemExit
    mock_db_utils.init_db_resources.return_value = (MagicMock(name="engine"), MagicMock(name="session_factory"))


def test_configure_page(reset_mocks):
    configure_page()
    _, kwargs = mock_st.set_page_config.call_args
    assert kwargs["page_title"] == "Traffic Data Analysis"
    assert kwargs["layout"] == "wide"
    assert kwargs["initial_sidebar_state"] == "expanded"
    expected_suffix = os.path.join("app", "gfx", "ptc-logo-white.png")
    # Check that the page_icon ends with the OS-specific expected suffix
    assert kwargs["page_icon"].endswith(expected_suffix)

@patch('logging.getLogger')
def test_initialize_logging(mock_getLogger, reset_mocks):
    mock_logger = MagicMock()
    mock_getLogger.return_value = mock_logger

    logger = initialize_logging()

    mock_log_config.setup_logging.assert_called_once()
    mock_getLogger.assert_called_once_with('app.main_app')
    assert logger == mock_logger
    mock_logger.info.assert_called_once_with("--- Streamlit App Logging Initialized ---")

@patch('app.main_app.logging.getLogger')
def test_initialize_database_success(mock_getLogger, reset_mocks):
    mock_logger = MagicMock()
    mock_getLogger.return_value = mock_logger
    mock_engine = MagicMock(name="engine")
    mock_session_factory = MagicMock(name="session_factory")
    mock_db_utils.init_db_resources.return_value = (mock_engine, mock_session_factory)

    engine, SessionFactory = initialize_database(mock_logger)

    mock_db_utils.init_db_resources.assert_called_once()
    assert engine == mock_engine
    assert SessionFactory == mock_session_factory
    mock_logger.info.assert_any_call("Attempting to initialize database resources...")
    mock_logger.info.assert_any_call("Database Engine and Session Factory initialized successfully (or retrieved from cache).")
    mock_st.error.assert_not_called()
    mock_st.stop.assert_not_called()

@patch('app.main_app.logging.getLogger')
def test_initialize_database_failure(mock_getLogger, reset_mocks):
    mock_logger = MagicMock()
    mock_getLogger.return_value = mock_logger
    mock_db_utils.init_db_resources.return_value = (None, None)

    with pytest.raises(SystemExit):
        initialize_database(mock_logger)

    mock_db_utils.init_db_resources.assert_called_once()
    mock_logger.error.assert_called_once()
    mock_st.error.assert_called_once_with("Fatal Error: Could not establish database connection. App cannot continue.")
    mock_st.stop.assert_called_once()
