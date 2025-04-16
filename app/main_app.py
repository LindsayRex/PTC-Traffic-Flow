
import streamlit as st
import logging
from pathlib import Path
from log_config import setup_logging
from stremlit_colour_pallet import MAGENTA, BLACK, WHITE, LIGHT_GRAY, DARK_GRAY, STYLES

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Page Configuration
st.set_page_config(
    page_title="Traffic Data Analysis",
    page_icon="app/gfx/ptc-logo-white.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import feature functions
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

# Custom CSS
st.markdown(f"""
    <style>
    .stApp {{
        background-color: {BLACK};
        color: {WHITE};
    }}
    .sidebar .sidebar-content {{
        background-color: {DARK_GRAY};
    }}
    .stSelectbox, .stDateInput {{
        background-color: {DARK_GRAY};
        border-radius: 5px;
        padding: 10px;
        margin: 5px 0;
    }}
    .stButton > button {{
        background-color: {MAGENTA};
        color: {WHITE};
        border: none;
        border-radius: 5px;
        padding: 10px 20px;
        transition: all 0.3s;
    }}
    .stButton > button:hover {{
        opacity: 0.8;
        transform: translateY(-2px);
    }}
    </style>
""", unsafe_allow_html=True)

# Banner with Logo
logo_path = Path("app/gfx/ptc-logo-white.png")
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
st.sidebar.markdown(f"""
    <div style='padding: 10px; background-color: {DARK_GRAY}; border-radius: 5px; margin-bottom: 20px;'>
        <h3 style='color: {MAGENTA}; margin-bottom: 15px;'>Global Filters</h3>
    </div>
""", unsafe_allow_html=True)

# Date Range Filter
st.sidebar.markdown(f"<p style='color: {WHITE}; margin-bottom: 5px;'>Analysis Period</p>", unsafe_allow_html=True)
date_range = st.sidebar.date_input("Select Date Range", [], help="Choose the date range for analysis")

# Region Filter
st.sidebar.markdown(f"<p style='color: {WHITE}; margin-bottom: 5px;'>Geographic Area</p>", unsafe_allow_html=True)
region = st.sidebar.selectbox("Select Region", 
    ["All Regions", "Sydney", "Regional NSW", "Western Sydney", "Northern Beaches", "Eastern Suburbs"],
    help="Filter data by geographic region")

# Additional Filters
st.sidebar.markdown(f"<p style='color: {WHITE}; margin-bottom: 5px;'>Road Type</p>", unsafe_allow_html=True)
road_type = st.sidebar.multiselect("Select Road Types",
    ["All", "Highway", "Arterial", "Local", "Collector"],
    default=["All"],
    help="Filter by road classification")

# Apply Filters Button
st.sidebar.button("Apply Filters", help="Click to apply selected filters", use_container_width=True)

# Main Content Area
if selection == "Home":
    # Home page layout with columns
    st.markdown(f"<div style='{STYLES['content']}'><h2>Welcome to Traffic Data Analysis</h2></div>", unsafe_allow_html=True)
    
    # Create three columns for feature highlights
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
            <div style='background-color: {DARK_GRAY}; padding: 20px; border-radius: 10px; height: 200px;'>
                <h3 style='color: {MAGENTA}'>Traffic Analysis</h3>
                <p>Comprehensive tools for analyzing traffic patterns and trends across NSW roads.</p>
                <ul>
                    <li>Real-time monitoring</li>
                    <li>Historical data analysis</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
            <div style='background-color: {DARK_GRAY}; padding: 20px; border-radius: 10px; height: 200px;'>
                <h3 style='color: {MAGENTA}'>Vehicle Classification</h3>
                <p>Detailed insights into vehicle types and their distribution.</p>
                <ul>
                    <li>Heavy vehicle patterns</li>
                    <li>Vehicle type distribution</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown(f"""
            <div style='background-color: {DARK_GRAY}; padding: 20px; border-radius: 10px; height: 200px;'>
                <h3 style='color: {MAGENTA}'>Time Analysis</h3>
                <p>Compare traffic patterns across different time periods.</p>
                <ul>
                    <li>Peak hour analysis</li>
                    <li>Weekday vs Weekend</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)
    
    # Quick start guide
    st.markdown(f"""
        <div style='{STYLES["content"]}'>
            <h3>Getting Started</h3>
            <ol>
                <li>Select a feature from the sidebar menu</li>
                <li>Choose your analysis parameters</li>
                <li>Explore interactive visualizations</li>
                <li>Export or share your findings</li>
            </ol>
        </div>
    """, unsafe_allow_html=True)
else:
    # Render selected feature
    feature_function = PAGES[selection]
    if feature_function:
        feature_function()

# Footer
st.markdown("---")
st.caption("Developed for PTC | Data Source: NSW Roads & Maritime Services")
