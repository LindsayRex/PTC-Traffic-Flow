import sys
from pathlib import Path
import logging
import streamlit as st

# --- Project Setup ---
# Add the project root to the PYTHONPATH
# Ensure this runs early if imports depend on it
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

# --- Local Imports (Grouped after path setup) ---
from app.log_config import setup_logging
from app.stremlit_colour_pallet import MAGENTA, BLACK, WHITE, DARK_GRAY, STYLES
from app.db_utils import init_db_resources

# --- Constants ---
LOGO_PATH = Path("app/gfx/ptc-logo-white.svg")

# --- Core Functions ---

def configure_page():
    """Sets the Streamlit page configuration."""
    st.set_page_config(
        page_title="Traffic Data Analysis",
        page_icon="app/gfx/ptc-logo-white.png", # Consider making this relative or absolute
        layout="wide",
        initial_sidebar_state="expanded"
    )

def initialize_logging():
    """Initializes logging for the application."""
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("--- Streamlit App Logging Initialized ---")
    return logger

def initialize_database(logger):
    """
    Initializes and validates database resources.
    Returns engine and SessionFactory, or (None, None) on failure.
    Logs errors and shows Streamlit error message on failure.
    """
    logger.info("Attempting to initialize database resources...")
    try:
        # init_db_resources is cached via @st.cache_resource in db_utils
        engine, SessionFactory = init_db_resources()
        if engine is None or SessionFactory is None:
            raise ConnectionError("Database Engine or Session Factory failed to initialize.")
        logger.info("Database Engine and Session Factory initialized successfully (or retrieved from cache).")
        return engine, SessionFactory
    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        st.error("Fatal Error: Could not establish database connection. App cannot continue.")
        st.stop() # Stop script execution
        return None, None # Return None explicitly, though st.stop() halts

def load_feature_modules(logger):
    """Dynamically imports and returns the feature rendering functions."""
    logger.info("Loading feature modules...")
    try:
        # Import feature functions *after* potential st.stop() in DB init
        from app.features.feature_1_profile import render_station_profile
        from app.features.feature_2_peak import render_peak_analysis
        from app.features.feature_3_corridor import render_corridor_comparison
        from app.features.feature_4_heavy_vehicle import render_heavy_vehicle_explorer
        from app.features.feature_5_weekday_weekend import render_weekday_weekend_comparison
        from app.features.feature_6_quality import render_data_quality_overview
        from app.features.feature_7_snapshot import render_lga_suburb_snapshot
        from app.features.feature_8_directional import render_directional_flow_analysis
        from app.features.feature_9_hierarchy import render_hierarchy_benchmarking
        from app.features.feature_10_seasonal import render_seasonal_trend_analyzer

        pages = {
            "Home": render_home_page, # Reference the local function
            "Station Profile": render_station_profile,
            "Peak Hour Analysis": render_peak_analysis,
            "Corridor Comparison": render_corridor_comparison,
            "Heavy Vehicle Explorer": render_heavy_vehicle_explorer,
            "Weekday vs Weekend": render_weekday_weekend_comparison,
            "Data Quality Overview": render_data_quality_overview,
            "LGA/Suburb Snapshot": render_lga_suburb_snapshot,
            "Directional Flow Analysis": render_directional_flow_analysis,
            "Hierarchy Benchmarking": render_hierarchy_benchmarking,
            "Seasonal Trends": render_seasonal_trend_analyzer,
        }
        logger.info("Feature modules loaded successfully.")
        return pages
    except ImportError as e:
        logger.error(f"Failed to import one or more feature modules: {e}", exc_info=True)
        st.error("Error loading application features. Check logs.")
        return {} # Return empty dict on failure

# --- UI Rendering Functions ---

def apply_custom_css():
    """Applies custom CSS styles using st.markdown."""
    st.markdown(f"""
        <style>
        .stApp {{ background-color: {BLACK}; color: {WHITE}; }}
        .sidebar .sidebar-content {{ background-color: {DARK_GRAY}; padding: 1rem 0.5rem; }}
        .stButton > button {{ width: 100%; border: 1px solid {MAGENTA}; background-color: transparent; color: {WHITE}; transition: all 0.3s ease; }}
        .stButton > button:hover {{ background-color: {MAGENTA}; color: {WHITE}; }}
        /* Add other styles as needed */
        </style>
    """, unsafe_allow_html=True)

def display_banner(logger, logo_path=LOGO_PATH):
    """Displays the top banner with logo and title."""
    if logo_path.exists():
        col1, col2 = st.columns([1, 5])
        with col1:
            st.image(str(logo_path), width=100)
        with col2:
            st.markdown(f"<h1 style='{STYLES['title']}'>Traffic Data Analysis</h1>", unsafe_allow_html=True)
    else:
        logger.warning(f"Logo file not found at: {logo_path.resolve()}")
        st.error("Logo file not found, banner title only.")
        st.markdown(f"<h1 style='{STYLES['title']}'>Traffic Data Analysis</h1>", unsafe_allow_html=True)


def display_sidebar_navigation(pages):
    """Displays the sidebar navigation radio buttons."""
    st.sidebar.markdown(f"<h2 style='color: {MAGENTA}'>Navigation</h2>", unsafe_allow_html=True)
    if not pages:
        st.sidebar.warning("No features available.")
        return None
    # Use "Home" as the default selection if available
    default_index = 0
    page_options = list(pages.keys())
    if "Home" in page_options:
        default_index = page_options.index("Home")

    selection = st.sidebar.radio("Select Feature:", page_options, index=default_index, label_visibility="collapsed")
    return selection

def display_global_filters():
    """Displays global filters in the sidebar."""
    st.sidebar.markdown(f"<h3 style='color: {MAGENTA}'>Global Filters</h3>", unsafe_allow_html=True)
    # Keep filters simple for now, return values if needed later
    st.sidebar.date_input("Date Range", [])
    st.sidebar.selectbox("Region", ["All Regions", "Sydney", "Regional NSW"])
    # Add return values if these filters need to be passed to features

def render_home_page():
    """Renders the content for the Home page."""
    st.markdown(f"""
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
    """, unsafe_allow_html=True)

def render_feature_page(page_name, pages_dict, logger):
    """Renders the selected feature page."""
    feature_function = pages_dict.get(page_name)
    if feature_function:
        logger.info(f"Rendering feature: {page_name}")
        try:
            # Pass necessary arguments if features require them (e.g., engine, session, filters)
            feature_function()
        except Exception as e:
            logger.error(f"Error rendering feature '{page_name}': {e}", exc_info=True)
            st.error(f"An error occurred while loading the '{page_name}' feature. Please check the logs.")
    elif page_name is not None: # Avoid error if pages_dict was empty
         logger.warning(f"No function found for selected page: {page_name}")
         st.warning(f"Feature '{page_name}' is not available or failed to load.")

def display_footer():
    """Displays the application footer."""
    st.markdown("---")
    st.caption("Developed for PTC | Data Source: NSW Roads & Maritime Services")

# --- Main Application Execution ---

def main():
    """Main function to run the Streamlit application."""
    configure_page()
    logger = initialize_logging()
    logger.info("--- Streamlit App Starting ---")

    engine, SessionFactory = initialize_database(logger)
    # Proceed only if DB is initialized (initialize_database handles st.stop())

    pages = load_feature_modules(logger)

    apply_custom_css()
    display_banner(logger)
    selected_page = display_sidebar_navigation(pages)
    display_global_filters()

    # Render main content based on selection
    render_feature_page(selected_page, pages, logger)

    display_footer()
    logger.info("--- Streamlit App Rendering Complete ---")


if __name__ == "__main__":
    main()
