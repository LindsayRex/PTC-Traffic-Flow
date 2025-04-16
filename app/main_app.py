
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
st.sidebar.markdown(f"""
    <div style='padding: 1rem 0; border-bottom: 1px solid {MAGENTA};'>
        <h2 style='color: {MAGENTA}; font-size: 1.5rem; margin-bottom: 0.5rem;'>Navigation</h2>
        <p style='color: {WHITE}; font-size: 0.9rem;'>Explore traffic data analysis tools</p>
    </div>
""", unsafe_allow_html=True)

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
    # Home page layout with welcome section
    st.markdown(f"""
        <div style='text-align: center; padding: 2rem 0;'>
            <h1 style='color: {MAGENTA}; font-size: 3rem;'>Traffic Data Analysis</h1>
            <p style='font-size: 1.2rem; color: {WHITE}; margin: 1rem 0;'>
                Comprehensive traffic analysis tools for NSW roads and highways
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # KPI Summary Cards
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    
    with kpi1:
        st.markdown(f"""
            <div style='background-color: {DARK_GRAY}; padding: 1rem; border-radius: 10px; text-align: center;'>
                <h3 style='color: {MAGENTA}'>10K+</h3>
                <p>Daily Records</p>
            </div>
        """, unsafe_allow_html=True)
    
    with kpi2:
        st.markdown(f"""
            <div style='background-color: {DARK_GRAY}; padding: 1rem; border-radius: 10px; text-align: center;'>
                <h3 style='color: {MAGENTA}'>150+</h3>
                <p>Monitoring Stations</p>
            </div>
        """, unsafe_allow_html=True)
    
    with kpi3:
        st.markdown(f"""
            <div style='background-color: {DARK_GRAY}; padding: 1rem; border-radius: 10px; text-align: center;'>
                <h3 style='color: {MAGENTA}'>24/7</h3>
                <p>Real-time Updates</p>
            </div>
        """, unsafe_allow_html=True)
    
    with kpi4:
        st.markdown(f"""
            <div style='background-color: {DARK_GRAY}; padding: 1rem; border-radius: 10px; text-align: center;'>
                <h3 style='color: {MAGENTA}'>5+</h3>
                <p>Vehicle Classes</p>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Feature highlights in three columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
            <div style='background-color: {DARK_GRAY}; padding: 20px; border-radius: 10px; height: 250px; transition: transform 0.3s; cursor: pointer; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
                <h3 style='color: {MAGENTA}; font-size: 1.5rem; margin-bottom: 1rem;'>Traffic Analysis</h3>
                <p style='color: {WHITE}; margin-bottom: 1rem;'>Comprehensive tools for analyzing traffic patterns and trends across NSW roads.</p>
                <ul style='color: {WHITE}; margin-left: 1rem;'>
                    <li style='margin-bottom: 0.5rem;'>🔍 Real-time monitoring</li>
                    <li style='margin-bottom: 0.5rem;'>📊 Historical data analysis</li>
                    <li style='margin-bottom: 0.5rem;'>📈 Trend visualization</li>
                </ul>
                <div style='position: absolute; bottom: 20px;'>
                    <span style='color: {MAGENTA}; text-decoration: underline; font-size: 0.9rem;'>Learn More →</span>
                </div>
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
