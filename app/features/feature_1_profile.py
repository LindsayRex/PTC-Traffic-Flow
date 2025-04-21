import streamlit as st
import pandas as pd
import numpy as np
import datetime
import panel as pn
import holoviews as hv
from holoviews import opts
import hvplot.pandas
import folium
from folium import Marker, Popup
from streamlit_folium import st_folium
import datetime as dt
import logging
from typing import List, Dict, Optional, Tuple, Any

# Import logging configuration - using relative import
from ..log_config import setup_logging

# Import utility functions - using relative import
from ..db_utils import (
    get_station_details,
    get_distinct_values,
    get_hourly_data_for_stations,
    get_all_station_metadata
)

# Set up logging
setup_logging(script_name="feature_1_profile")
logger = logging.getLogger(__name__)

def render_station_profile():
    """Renders the Traffic Station Profile Dashboard feature."""
    logger.info("Rendering Traffic Station Profile Dashboard")
    st.title("Traffic Station Profile Dashboard")
    
    # 1. Set up the layout with columns
    col1, col2 = st.columns([1, 3])
    
    # 2. Load station data for selector
    with st.spinner("Loading station data..."):
        logger.debug("Fetching station metadata")
        try:
            station_df = get_all_station_metadata(None)  # None for _conn parameter as it's cached
            logger.info(f"Retrieved {len(station_df)} station records")
        except Exception as e:
            logger.error(f"Failed to fetch station metadata: {e}")
            st.error("Error loading station data. Check logs for details.")
            return
    
    # Handle empty dataframe case
    if station_df.empty:
        logger.warning("No station data available in the database")
        st.error("No station data available. Please check your database connection.")
        return
    
    # Create station selection options
    station_options = [f"{row['station_id']} - {row['road_name']}" for _, row in station_df.iterrows()]
    station_keys = station_df['station_key'].tolist()
    station_map = dict(zip(station_options, station_keys))
    
    # 3. Create selectors in the first column
    with col1:
        st.subheader("Selection Controls")
        
        # Station selector
        selected_station_option = st.selectbox(
            "Select Station",
            options=station_options,
            index=0 if station_options else None
        )
        
        # Get selected station key from the map
        if selected_station_option:
            selected_station_key = station_map[selected_station_option]
            selected_station_id = selected_station_option.split(" - ")[0]
            logger.info(f"User selected station: {selected_station_id} (key: {selected_station_key})")
            
            # Get station details for display and mapping
            try:
                station_details = get_station_details(None, selected_station_key)
                logger.debug(f"Retrieved details for station key: {selected_station_key}")
            except Exception as e:
                logger.error(f"Failed to fetch station details: {e}")
                st.error("Error loading station details. Check logs for details.")
                return
            
            # Direction selector - create mapping for display
            directions = {
                1: "Prescribed Direction",
                2: "Opposite Direction",
                3: "Both Directions"
            }
            selected_direction = st.selectbox(
                "Select Direction",
                options=list(directions.keys()),
                format_func=lambda x: directions[x],
                index=0
            )
            selected_direction_desc = directions[selected_direction]
            logger.info(f"User selected direction: {selected_direction} ({selected_direction_desc})")
            
            # Date range calculation for data fetching
            today = datetime.date.today()
            start_date_90_days = today - datetime.timedelta(days=90)
            start_date_full_year = today - datetime.timedelta(days=365)
            
            # The earliest start date we need
            start_date = min(start_date_90_days, start_date_full_year)
            logger.debug(f"Data query date range: {start_date} to {today}")
            
            # Fetch hourly data
            with st.spinner("Loading traffic data..."):
                logger.debug(f"Fetching hourly data for station key: {selected_station_key}")
                try:
                    hourly_data = get_hourly_data_for_stations(
                        None,  # _conn parameter
                        [selected_station_key],
                        start_date,
                        today,
                        directions=[selected_direction],
                        classifications=[1],  # All vehicles
                        required_cols=None  # Get all columns
                    )
                    if not hourly_data.empty:
                        logger.info(f"Retrieved {len(hourly_data)} hourly records for station {selected_station_id}")
                    else:
                        logger.warning(f"No hourly data found for station {selected_station_id}")
                except Exception as e:
                    logger.error(f"Failed to fetch hourly data: {e}")
                    st.error("Error loading traffic data. Check logs for details.")
                    hourly_data = pd.DataFrame()  # Empty dataframe to prevent errors
    
    # 4. Create visualizations in the second column
    with col2:
        if 'station_details' in locals() and station_details:
            # Convert ORM object to dict for easier access if needed
            if not isinstance(station_details, dict):
                try:
                    station_dict = {c.name: getattr(station_details, c.name) 
                                for c in station_details.__table__.columns}
                except Exception as e:
                    logger.error(f"Failed to convert station details object to dict: {e}")
                    station_dict = {}
            else:
                station_dict = station_details
            
            # Create tabs for different visualizations
            tab1, tab2, tab3 = st.tabs(["Station Info", "Traffic Profiles", "Daily Trends"])
            
            # Tab 1: Station Metadata and Map
            with tab1:
                logger.debug("Rendering station info tab")
                # Display station metadata
                st.subheader(f"Station Metadata: {selected_station_id}")
                
                # Create a clean metadata display
                metadata_cols = {
                    "Road Name": station_dict.get("road_name", "N/A"),
                    "LGA": station_dict.get("lga", "N/A"),
                    "Suburb": station_dict.get("suburb", "N/A"),
                    "Road Functional Hierarchy": station_dict.get("road_functional_hierarchy", "N/A"),
                    "Device Type": station_dict.get("device_type", "N/A"),
                    "Vehicle Classifier": "Yes" if station_dict.get("vehicle_classifier", False) else "No",
                    "Permanent Station": "Yes" if station_dict.get("permanent_station", False) else "No",
                    "Quality Rating": station_dict.get("quality_rating", "N/A")
                }
                
                # Display as a table
                st.table(pd.DataFrame(list(metadata_cols.items()), columns=["Attribute", "Value"]))
                
                # Display station location map
                st.subheader(f"Location: {selected_station_id}")
                
                lat = station_dict.get("wgs84_latitude")
                lon = station_dict.get("wgs84_longitude")
                
                if lat and lon:
                    logger.debug(f"Rendering map for coordinates: {lat}, {lon}")
                    m = folium.Map(location=[lat, lon], zoom_start=15)
                    tooltip = f"Station ID: {selected_station_id}"
                    popup_text = f"""
                    <b>Station ID:</b> {selected_station_id}<br>
                    <b>Road:</b> {station_dict.get('road_name', 'N/A')}<br>
                    <b>Full Name:</b> {station_dict.get('full_name', 'N/A')}
                    """
                    
                    folium.Marker(
                        [lat, lon], 
                        popup=folium.Popup(popup_text, max_width=300),
                        tooltip=tooltip,
                        icon=folium.Icon(color="red", icon="info-sign")
                    ).add_to(m)
                    
                    # Display the map in Streamlit
                    st_folium(m, width=700, height=500)
                else:
                    logger.warning(f"No location data available for station {selected_station_id}")
                    st.warning("No location data available for this station")
            
            # Tab 2: Typical Hourly Profile Chart
            with tab2:
                logger.debug("Rendering traffic profiles tab")
                st.subheader(f"Typical Hourly Traffic Profile ({selected_direction_desc})")
                
                if 'hourly_data' in locals() and not hourly_data.empty:
                    # Process data for hourly profile chart
                    logger.debug("Processing yearly hourly data for profiles")
                    # Filter for the last full year
                    year_data = hourly_data[hourly_data['count_date'] >= start_date_full_year].copy()
                    
                    if not year_data.empty:
                        # Exclude public holidays
                        year_data = year_data[~year_data['is_public_holiday']]
                        
                        # Create weekday/weekend flag
                        year_data['is_weekend'] = year_data['day_of_week'].isin([6, 7])  # 6=Sat, 7=Sun
                        
                        # Prepare data for plotting
                        hourly_profiles = []
                        
                        # Process for weekdays
                        weekday_data = year_data[~year_data['is_weekend']].copy()
                        if not weekday_data.empty:
                            logger.debug(f"Processing {len(weekday_data)} weekday records")
                            weekday_profile = process_hourly_profile(weekday_data, 'Weekday')
                            hourly_profiles.append(weekday_profile)
                        
                        # Process for weekends
                        weekend_data = year_data[year_data['is_weekend']].copy()
                        if not weekend_data.empty:
                            logger.debug(f"Processing {len(weekend_data)} weekend records")
                            weekend_profile = process_hourly_profile(weekend_data, 'Weekend')
                            hourly_profiles.append(weekend_profile)
                        
                        # Combine profiles
                        if hourly_profiles:
                            profile_df = pd.concat(hourly_profiles)
                            
                            logger.debug("Generating hourly profile chart")
                            # Create the plot with hvplot/holoviews
                            try:
                                fig = profile_df.hvplot.line(
                                    x='Hour', 
                                    y='Average Volume', 
                                    by='Period',
                                    title=f"Typical Hourly Traffic Profile ({selected_direction_desc})",
                                    xlabel="Hour of Day (0-23)",
                                    ylabel="Average Traffic Volume",
                                    legend='top_right',
                                    grid=True,
                                    width=700,
                                    height=400,
                                    line_width=3
                                )
                                
                                # Convert to html and display in Streamlit
                                hvplot_html = hv.render(fig, backend='bokeh')
                                st.bokeh_chart(hvplot_html, use_container_width=True)
                            except Exception as e:
                                logger.error(f"Failed to create hourly profile chart: {e}")
                                st.error("Error creating hourly profile chart. Check logs for details.")
                        else:
                            logger.warning("Insufficient data to create hourly profiles")
                            st.warning("Not enough data to create hourly profiles")
                    else:
                        logger.warning(f"No yearly data available for station {selected_station_id}")
                        st.warning("No yearly data available for this station")
                else:
                    logger.warning(f"No data available for station {selected_station_id}")
                    st.warning("No data available for this station")
            
            # Tab 3: Recent Daily Volume Trend Chart
            with tab3:
                logger.debug("Rendering daily trends tab")
                st.subheader(f"Recent Daily Traffic Volume ({selected_direction_desc}) - Last 90 Days")
                
                if 'hourly_data' in locals() and not hourly_data.empty:
                    # Filter for the last 90 days
                    logger.debug("Processing recent daily data for trends")
                    recent_data = hourly_data[hourly_data['count_date'] >= start_date_90_days].copy()
                    
                    if not recent_data.empty:
                        try:
                            # Group by date to get daily totals
                            daily_df = recent_data.groupby('count_date')['daily_total'].mean().reset_index()
                            daily_df.columns = ['Date', 'Total Daily Volume']
                            
                            # Sort by date
                            daily_df = daily_df.sort_values('Date')
                            
                            logger.debug(f"Generated daily trends for {len(daily_df)} days")
                            
                            # Create the plot with hvplot/holoviews
                            fig = daily_df.hvplot.line(
                                x='Date', 
                                y='Total Daily Volume',
                                title=f"Recent Daily Traffic Volume ({selected_direction_desc}) - Last 90 Days",
                                xlabel="Date",
                                ylabel="Total Daily Volume",
                                grid=True,
                                width=700,
                                height=400,
                                line_width=2
                            )
                            
                            # Convert to html and display in Streamlit
                            hvplot_html = hv.render(fig, backend='bokeh')
                            st.bokeh_chart(hvplot_html, use_container_width=True)
                        except Exception as e:
                            logger.error(f"Failed to create daily trends chart: {e}")
                            st.error("Error creating daily trends chart. Check logs for details.")
                    else:
                        logger.warning(f"No recent data available for station {selected_station_id}")
                        st.warning("No recent data available for this station")
                else:
                    logger.warning(f"No data available for station {selected_station_id}")
                    st.warning("No data available for this station")
        else:
            logger.info("No station selected or station details not available")
            st.warning("Please select a station to display data")

def process_hourly_profile(data: pd.DataFrame, period_name: str) -> pd.DataFrame:
    """
    Process hourly count data to create an average hourly profile.
    
    Args:
        data: DataFrame containing hourly counts
        period_name: Name to assign to the period (e.g., 'Weekday', 'Weekend')
    
    Returns:
        DataFrame with columns ['Hour', 'Average Volume', 'Period']
    """
    logger.debug(f"Processing hourly profile for {period_name}")
    # Create a list to hold hourly data
    hourly_data = []
    
    # Process each hour column
    for hour in range(24):
        hour_col = f'hour_{hour:02d}'
        if hour_col in data.columns:
            avg_volume = data[hour_col].mean()
            hourly_data.append({'Hour': hour, 'Average Volume': avg_volume, 'Period': period_name})
    
    # Create a DataFrame from the processed data
    result_df = pd.DataFrame(hourly_data)
    logger.debug(f"Created hourly profile with {len(result_df)} data points")
    return result_df