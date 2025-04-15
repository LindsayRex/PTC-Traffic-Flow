import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from app.main_app import init_connection
from app.main_app import logo_path
from app.main_app import PAGES, page_selection
from app.main_app import conn
from app.main_app import page_selection

# Mock Streamlit and Panel imports
@pytest.fixture(autouse=True)
def mock_dependencies():
    with patch("streamlit.set_page_config"), \
         patch("streamlit.sidebar"), \
         patch("streamlit.header"), \
         patch("streamlit.markdown"), \
         patch("streamlit.subheader"), \
         patch("streamlit.write"), \
         patch("streamlit.caption"), \
         patch("streamlit.radio"), \
         patch("panel.extension"):
        yield

# Mock database connection
@pytest.fixture
def mock_db_connection():
    with patch("app.main_app.get_db_connection") as mock_conn:
        mock_conn.return_value = MagicMock()
        yield mock_conn

# Test init_connection function
def test_init_connection(mock_db_connection):
    conn = init_connection()
    mock_db_connection.assert_called_once()
    assert conn is not None

# Test sidebar logo handling
def test_sidebar_logo_handling():
    with patch("pathlib.Path.exists", return_value=True) as mock_exists, \
         patch("streamlit.sidebar.image") as mock_image, \
         patch("streamlit.sidebar.warning") as mock_warning:
        if logo_path.exists():
            mock_image.assert_called_once()
        else:
            mock_warning.assert_called_once()

# Test page selection and rendering
def test_page_selection_and_rendering(mock_db_connection):
    with patch("streamlit.sidebar.radio", return_value="Station Profile") as mock_radio, \
         patch("app.main_app.render_station_profile") as mock_render:
        page_function = PAGES[page_selection]
        page_function(conn)
        mock_radio.assert_called_once()
        mock_render.assert_called_once_with(conn)

# Test home page rendering
def test_home_page_rendering():
    with patch("streamlit.subheader") as mock_subheader, \
         patch("streamlit.write") as mock_write:
        if page_selection == "Home":
            mock_subheader.assert_called_once_with("Welcome")
            mock_write.assert_called_once_with("Select a feature from the sidebar to explore the NSW traffic count data.")