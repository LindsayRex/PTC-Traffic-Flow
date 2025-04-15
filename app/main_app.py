# This is the main application file for the PTC Traffic Data Explorer.
# It uses Streamlit for the web interface and Panel for interactive components.

import streamlit as st
import logging
from . import log_config

# Setup logging
log_config.setup_logging(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Starting PTC Traffic Data Explorer application")
import panel as pn
import pandas as pd
from pathlib import Path

# Import feature functions (assuming each feature is implemented in its own file)
from features.feature_1_profile import render_station_profile
from features.feature_2_peak import render_peak_analysis
from features.feature_3_corridor import render_corridor_comparison
from features.feature_4_heavy_vehicle import render_heavy_vehicle_explorer
from features.feature_5_weekday_weekend import render_weekday_weekend_comparison
from features.feature_6_quality import render_data_quality_overview
from features.feature_7_snapshot import render_lga_suburb_snapshot
from features.feature_8_directional import render_directional_flow_analysis
from features.feature_9_hierarchy import render_hierarchy_benchmarking
from features.feature_10_seasonal import render_seasonal_trend_analyzer

# Import database utilities
from db_utils import get_db_connection, fetch_data # Example functions

# --- Page Configuration ---
st.set_page_config(
    page_title="PTC Traffic Data Explorer",
    page_icon="app/gfx/ptc-logo-white.png", # Or a favicon version
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Panel Setup ---
pn.extension('tabulator', 'folium', sizing_mode='stretch_width') # Load extensions

# --- Database Connection ---
# Use st.cache_resource for the connection pool if using SQLAlchemy
@st.cache_resource
def init_connection():
    # Uses Streamlit secrets ideally
    return get_db_connection()

conn = init_connection()

# --- Sidebar Navigation and Global Controls ---
logo_path = Path(__file__).parent / "gfx" / "ptc-logo-white.png"
if logo_path.exists():
    st.sidebar.image(str(logo_path), use_column_width=True)
else:
    st.sidebar.warning("Logo file not found.")

st.sidebar.title("Navigation")

# Define pages/features
PAGES = {
    "Home": "Home",
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
page_selection = st.sidebar.radio("Go to", list(PAGES.keys()))

# --- Main Page Content ---
st.header(f"PTC Traffic Data Explorer: {page_selection}")
st.markdown("---") # Visual separator

# Render selected page
if page_selection == "Home":
    st.subheader("Welcome")
    st.write("Select a feature from the sidebar to explore the NSW traffic count data.")
    # Add more info, acknowledgements, or instructions here
else:
    # Call the function associated with the selected page
    page_function = PAGES[page_selection]
    # Pass the database connection/engine to the feature function
    page_function(conn) # Assuming feature functions accept the connection

# --- Footer ---
st.markdown("---")
st.caption("Developed for ptc. | Data Source: NSW Roads & Maritime Services")