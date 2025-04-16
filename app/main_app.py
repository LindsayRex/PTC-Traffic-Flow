# This is the main application file for the PTC Traffic Data Explorer.
# It uses Streamlit for the web interface and Panel for interactive components.

import streamlit as st
import logging
from .log_config import setup_logging
import panel as pn
import pandas as pd
from pathlib import Path

# --- Import color palette ---
from .stremlit_colour_pallet import MAGENTA, LIGHT_GRAY, DARK_GRAY, WHITE

# --- Import feature functions ---
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

# --- Import database utilities ---
from db_utils import get_db_connection, fetch_data

# Initialize environment from secrets
if not st.secrets.get("environment"):
    st.error("Environment configuration not found in secrets")
    st.stop()

# --- Get logging configuration from secrets ---
log_config = st.secrets.get("logging", {})
log_level_str = log_config.get("level", "WARNING")
log_level = getattr(logging, log_level_str)
file_path = log_config.get("file_path", "logs/app.log")

# --- Setup logging ---
setup_logging(level=log_level, file_path=file_path)
logger = logging.getLogger(__name__)

logger.info(f"Starting PTC Traffic Data Explorer application in {st.secrets.environment.get('type', 'development')} mode")

# Configure debug mode
st.set_page_config(
    page_title="Traffic Data Analysis",
    page_icon="app/gfx/ptc-logo-white.png",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    } if not st.secrets.environment.get("debug", False) else None
)

# --- Panel Setup ---
pn.extension('tabulator', 'folium', sizing_mode='stretch_width')

# --- Database Connection ---
@st.cache_resource
def init_connection():
    # Uses Streamlit secrets ideally
    return get_db_connection()

conn = init_connection()

# --- Sidebar Styling ---
st.markdown(
    f"""
    <style>
    [data-testid="stSidebar"] {{
        background-color: {DARK_GRAY};
    }}
    .sidebar-title {{
        color: {MAGENTA};
        font-size: 1.3rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }}
    .sidebar-btn > button {{
        background-color: {DARK_GRAY} !important;
        color: {MAGENTA} !important;
        border-radius: 8px;
        border: 1.5px solid {MAGENTA};
        margin-bottom: 0.5rem;
        font-weight: 600;
    }}
    .sidebar-btn > button:hover {{
        background-color: {MAGENTA} !important;
        color: {WHITE} !important;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# --- Sidebar Logo ---
logo_path = Path(__file__).parent / "gfx" / "ptc-logo-white.png"
if logo_path.exists():
    st.sidebar.image(str(logo_path), use_column_width=True)
else:
    st.sidebar.warning("Logo file not found.")

# --- Sidebar Title ---
st.sidebar.markdown('<div class="sidebar-title">Menu</div>', unsafe_allow_html=True)

# --- Menu Items ---
MENU_ITEMS = [
    ("Traffic Station Profile Dashboard", render_station_profile),
    ("Peak Hour Analysis View", render_peak_analysis),
    ("Corridor Traffic Flow Comparison", render_corridor_comparison),
    ("Heavy Vehicle Pattern Explorer", render_heavy_vehicle_explorer),
    ("Weekday vs. Weekend Traffic Comparison", render_weekday_weekend_comparison),
    ("Data Quality & Coverage Overview", render_data_quality_overview),
    ("LGA/Suburb Traffic Snapshot", render_lga_suburb_snapshot),
    ("Directional Flow Analysis Dashboard", render_directional_flow_analysis),
    ("Road Hierarchy Traffic Benchmarking", render_hierarchy_benchmarking),
    ("Monthly/Seasonal Trend Analyzer", render_seasonal_trend_analyzer),
]

# --- Sidebar Menu Buttons ---
selected_page = "Home"
for label, _ in MENU_ITEMS:
    if st.sidebar.container().markdown(f'<div class="sidebar-btn">{st.sidebar.button(label, key=label)}</div>', unsafe_allow_html=True):
        selected_page = label

# --- Global Filters (Sidebar) ---
st.sidebar.markdown("---")
st.sidebar.markdown('<div class="sidebar-title">Global Filters</div>', unsafe_allow_html=True)

# Example: Fetch LGA list from DB or static list
try:
    lga_list = fetch_data(conn, "SELECT DISTINCT lga FROM traffic_data ORDER BY lga")["lga"].tolist()
except Exception:
    lga_list = ["Sydney", "Parramatta", "Wollongong"]  # fallback

date_range = st.sidebar.date_input("Date Range", [])
selected_lgas = st.sidebar.multiselect("Select LGA(s)", lga_list)

# --- Banner ---
st.markdown(
    f"""
    <div style="background-color: {MAGENTA}; padding: 1.2rem 0 1.2rem 0; width: 100%; display: flex; align-items: center;">
        <img src="app/gfx/ptc-logo-white.png" style="height: 48px; margin-left: 2rem; margin-right: 2rem;" alt="Logo">
        <span style="color: {WHITE}; font-size: 2.2rem; font-weight: bold; letter-spacing: 1px;">
            Traffic Data Analysis
        </span>
    </div>
    """,
    unsafe_allow_html=True
)

# --- Main Content Area Styling ---
st.markdown(
    f"""
    <style>
    .main-content-area {{
        background-color: {LIGHT_GRAY};
        padding: 2rem 2rem 2rem 2rem;
        border-radius: 12px;
        margin-top: 2rem;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# --- Main Page Content ---
if selected_page == "Home":
    st.markdown(
        f"""
        <div class="main-content-area">
            <h2 style="color: {MAGENTA};">Welcome to the Traffic Data Analysis Platform</h2>
            <p>
                This application provides interactive dashboards and analysis tools for NSW traffic count data.<br>
                <b>How to use:</b>
                <ul>
                    <li>Use the <span style="color:{MAGENTA};font-weight:bold;">sidebar menu</span> to navigate between features.</li>
                    <li>Apply <span style="color:{MAGENTA};font-weight:bold;">global filters</span> (date range, LGA) to refine your analysis.</li>
                </ul>
                <b>Features:</b>
                <ul>
                    <li>Traffic station profiles, peak hour analysis, corridor comparisons, heavy vehicle patterns, and more.</li>
                </ul>
                <b>Recent Updates:</b>
                <ul>
                    <li>Data updated: <i>April 2025</i></li>
                    <li>New: Directional Flow Analysis Dashboard</li>
                </ul>
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    # Find the function for the selected page
    for label, func in MENU_ITEMS:
        if selected_page == label:
            func(conn, date_range=date_range, lgas=selected_lgas)
            break

# --- Footer ---
st.markdown("---")
st.caption("Developed for ptc. | Data Source: NSW Roads & Maritime Services")