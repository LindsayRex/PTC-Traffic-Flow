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

# Import utility functions - using relative import
from ..db_utils import (
    get_station_details,
    get_distinct_values,
    get_hourly_data_for_stations,
    get_all_station_metadata,
    get_latest_data_date  # <-- Add this import
)

# Get logger for this module
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
            station_df = get_all_station_metadata()
            if station_df is None:
                logger.error("get_all_station_metadata returned None, likely DB session issue.")
                st.error("Error loading station data. Database connection might be unavailable.")
                return
            logger.info(f"Retrieved {len(station_df)} station records")
        except Exception as e:
            logger.error(f"Failed to fetch station metadata: {e}", exc_info=True)
            st.error("Error loading station data. Check logs for details.")
            return
    
    # Handle empty dataframe case
    if station_df.empty:
        logger.warning("No station data available in the database")
        st.warning("No station data found matching criteria.")
    
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
                station_details = get_station_details(selected_station_key)
                if station_details is None:
                    logger.error(f"get_station_details returned None for key {selected_station_key}")
                    st.error("Could not load details for the selected station.")
                else:
                    logger.debug(f"Retrieved details for station key: {selected_station_key}")
            except Exception as e:
                logger.error(f"Failed to fetch station details: {e}", exc_info=True)
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
            
            # --- DYNAMIC DATE RANGE CALCULATION ---
            latest_date = None
            start_date_90_days = None
            start_date_full_year = None
            start_date = None
            end_date = None  # Use 'end_date' instead of 'fixed_end_date'

            try:
                logger.debug(f"Fetching latest data date for station {selected_station_key}, direction {selected_direction}")
                latest_date = get_latest_data_date(selected_station_key, selected_direction)

                if latest_date:
                    end_date = latest_date  # Use the actual latest date as the end date
                    start_date_90_days = end_date - datetime.timedelta(days=90)
                    start_date_full_year = end_date - datetime.timedelta(days=365)
                    # The earliest start date we need for fetching
                    start_date = min(start_date_90_days, start_date_full_year)
                    logger.info(f"Using dynamic date range based on latest data: {start_date} to {end_date}")
                else:
                    logger.warning(f"No latest data date found for station {selected_station_key}, direction {selected_direction}. Cannot calculate dynamic range.")
                    st.warning("No data found for this station and direction to determine date range.")

            except Exception as e:
                logger.error(f"Error fetching latest data date: {e}", exc_info=True)
                st.error("Error determining data date range.")
            # --- END DYNAMIC DATE RANGE CALCULATION ---

            # Fetch hourly data only if a valid date range was determined
            hourly_data = pd.DataFrame()  # Initialize empty
            if start_date and end_date and station_details:  # Check if dates are valid and details exist
                with st.spinner("Loading traffic data..."):
                    logger.debug(f"Fetching hourly data for station key: {selected_station_key} from {start_date} to {end_date}")
                    try:
                        hourly_data = get_hourly_data_for_stations(
                            [selected_station_key],
                            start_date,  # Use dynamic start date
                            end_date,    # Use dynamic end date
                            directions=[selected_direction],
                            classifications=[1],
                            required_cols=None
                        )
                        if hourly_data is None:
                            logger.error(f"get_hourly_data_for_stations returned None for key {selected_station_key}")
                            st.error("Could not load traffic data for the selected station.")
                            hourly_data = pd.DataFrame()
                        elif not hourly_data.empty:
                            logger.info(f"Retrieved {len(hourly_data)} hourly records for station {selected_station_id}")
                        else:
                            logger.warning(f"No hourly data found for station {selected_station_id} and selected criteria.")
                    except Exception as e:
                        logger.error(f"Failed to fetch hourly data: {e}", exc_info=True)
                        st.error("Error loading traffic data. Check logs for details.")
                        hourly_data = pd.DataFrame()
            elif not station_details:
                logger.warning("Station details not available, skipping hourly data fetch.")
            else:
                logger.warning("Date range not determined, skipping hourly data fetch.")
    
    # 4. Create visualizations in the second column
    with col2:
        # Check if station_dict exists AND if the date range was successfully calculated
        if 'station_details' in locals() and station_details and start_date_full_year and start_date_90_days and end_date:
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
                
                # --- FIX: Convert values to string before creating DataFrame ---
                metadata_items = [(k, str(v)) for k, v in metadata_cols.items()]
                metadata_df = pd.DataFrame(metadata_items, columns=["Attribute", "Value"])
                # --- END FIX ---
                
                # Display as a table
                # --- FIX: Remove unsupported label arguments ---
                st.table(metadata_df)
                # --- END FIX ---
                
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
                    # --- FIX: Remove unsupported label arguments AGAIN ---
                    st_folium(m, width=700, height=500)
                    # --- END FIX ---
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
                    # Filter for the last full year using DYNAMIC dates
                    year_data = hourly_data[
                        (hourly_data['count_date'] >= start_date_full_year) &
                        (hourly_data['count_date'] <= end_date)  # Ensure upper bound is also dynamic
                    ].copy()
                    
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
                                # --- FIX: Add hidden label ---
                                st.bokeh_chart(hvplot_html, use_container_width=True, label="Hourly Profile Chart", label_visibility="collapsed")
                                # --- END FIX ---
                            except Exception as e:
                                logger.error(f"Failed to create hourly profile chart: {e}")
                                st.error("Error creating hourly profile chart. Check logs for details.")
                        else:
                            logger.warning("Insufficient data to create hourly profiles")
                            st.warning("Not enough data to create hourly profiles")
                    else:
                        logger.warning(f"No data available within the calculated last year ({start_date_full_year} to {end_date}) for station {selected_station_id}")
                        st.warning(f"No data available within the calculated last year ({start_date_full_year.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')})")
                else:
                    logger.warning(f"No hourly data fetched for station {selected_station_id}")
                    st.warning("No hourly data available for this station and direction.")
            
            # Tab 3: Recent Daily Volume Trend Chart
            with tab3:
                logger.debug("Rendering daily trends tab")
                st.subheader(f"Recent Daily Traffic Volume ({selected_direction_desc}) - Last 90 Days")
                
                if 'hourly_data' in locals() and not hourly_data.empty:
                    # Filter for the last 90 days using DYNAMIC dates
                    logger.debug("Processing recent daily data for trends")
                    recent_data = hourly_data[
                        (hourly_data['count_date'] >= start_date_90_days) &
                        (hourly_data['count_date'] <= end_date)  # Ensure upper bound is also dynamic
                    ].copy()
                    
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
                            # --- FIX: Add hidden label ---
                            st.bokeh_chart(hvplot_html, use_container_width=True, label="Daily Trend Chart", label_visibility="collapsed")
                            # --- END FIX ---
                        except Exception as e:
                            logger.error(f"Failed to create daily trends chart: {e}")
                            st.error("Error creating daily trends chart. Check logs for details.")
                    else:
                        logger.warning(f"No data available within the calculated last 90 days ({start_date_90_days} to {end_date}) for station {selected_station_id}")
                        st.warning(f"No data available within the calculated last 90 days ({start_date_90_days.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')})")
                else:
                    logger.warning(f"No hourly data fetched for station {selected_station_id}")
                    st.warning("No hourly data available for this station and direction.")
        elif 'station_details' in locals() and station_details:
            # This case handles when station details are loaded but date range failed
            st.warning("Could not determine the date range for analysis based on available data for this station and direction.")
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