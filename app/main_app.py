import streamlit as st
import logging
from pathlib import Path
from app.log_config import setup_logging
from app.stremlit_colour_pallet import MAGENTA, BLACK, WHITE, LIGHT_GRAY, DARK_GRAY, STYLES

# --- Page Configuration (MUST BE FIRST STREAMLIT COMMAND) ---
st.set_page_config(
    page_title="Traffic Data Analysis",
    page_icon="app/gfx/ptc-logo-white.png",  # Ensure this path is correct relative to execution dir or use absolute
    layout="wide",
    initial_sidebar_state="expanded"
)
# --- End of Page Configuration ---

# Setup logging (call once at the start)
setup_logging()
logger = logging.getLogger(__name__) # Get logger for this module

# --- Now initialize and check Database Connection ---
# Import db_utils here if it relies heavily on st commands like st.secrets
from app.db_utils import SessionFactory, engine

if engine is None or SessionFactory is None:
    logger.error("Database Engine or Session Factory failed to initialize. Stopping app.")
    # This st.error call is now AFTER set_page_config, which is allowed.
    st.error("Fatal Error: Could not establish database connection. Please check configuration and logs.")
    st.stop()  # Stop script execution if DB connection failed
else:
    logger.info("Database Engine and Session Factory initialized successfully.")

# Import feature functions (can be done after DB check)
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

# Custom CSS
st.markdown(f"""
    <style>
    .stApp {{
        background-color: {BLACK};
        color: {WHITE};
    }}
    .sidebar .sidebar-content {{
        background-color: {DARK_GRAY};
        padding: 1rem 0.5rem;
    }}
    .stButton > button {{
        width: 100%;
        border: 1px solid {MAGENTA};
        background-color: transparent;
        color: {WHITE};
        transition: all 0.3s ease;
    }}
    .stButton > button:hover {{
        background-color: {MAGENTA};
        color: {WHITE};
    }}
    </style>
""", unsafe_allow_html=True)

# Banner with Logo
logo_path = Path("app/gfx/ptc-logo-white.svg")
if logo_path.exists():
    col1, col2 = st.columns([1, 5])
    with col1:
        st.image(str(logo_path), width=100)
    with col2:
        st.markdown(f"<h1 style='{STYLES['title']}'>Traffic Data Analysis</h1>", unsafe_allow_html=True)
else:
    st.error("Logo file not found")

# Sidebar Navigation
st.sidebar.markdown(f"<h2 style='color: {MAGENTA}'>Navigation</h2>", unsafe_allow_html=True)

# Define pages/features
PAGES = {
    "Home": None,
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

# Page selection
selection = st.sidebar.radio("", list(PAGES.keys()))

# Global Filters in Sidebar
st.sidebar.markdown(f"<h3 style='color: {MAGENTA}'>Global Filters</h3>", unsafe_allow_html=True)
date_range = st.sidebar.date_input("Date Range", [])
region = st.sidebar.selectbox("Region", ["All Regions", "Sydney", "Regional NSW"])

# Main Content Area
if selection == "Home":
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
else:
    # Render selected feature
    feature_function = PAGES[selection]
    if feature_function:
        try:
            feature_function()
        except Exception as e:
            logger.error(f"Error rendering feature '{selection}': {e}", exc_info=True)
            st.error(f"An error occurred while loading the '{selection}' feature. Please check the logs.")

# Footer
st.markdown("---")
st.caption("Developed for PTC | Data Source: NSW Roads & Maritime Services")
