# Example in a feature file (e.g., app/features/feature_1_profile.py)
import streamlit as st
import panel as pn
import pandas as pd
import holoviews as hv
import hvplot.pandas # noqa Register hvplot interfaces
from ..db_utils import get_db_session, get_station_details, get_hourly_data_for_stations # Relative import
# ... other imports ...

def calculate_hourly_profile(df_hourly):
    # ... calculation logic using the DataFrame fetched by get_hourly_data_for_stations ...
    pass

def render_station_profile(conn_info_ignored=None): # conn_info not directly needed if using get_db_session
    st.subheader("Station Profile Dashboard")

    # --- Widgets ---
    station_key_select = pn.widgets.Select(name="Select Station:", options=[...]) # Populate options
    direction_select = pn.widgets.Select(name="Select Direction:", options={...})

    # --- Reactive Function ---
    @pn.depends(station_key=station_key_select.param.value, direction=direction_select.param.value)
    def update_dashboard(station_key, direction):
        if not station_key or not direction:
            return pn.Column("Please select a station and direction.")

        layout = pn.Column()

        # Use the context manager for database access
        with get_db_session() as session:
            if not session:
                 return pn.pane.Alert("Database connection failed.", alert_type='danger')

            # Fetch data using utility functions
            station_data = get_station_details(session, station_key) # Pass session
            if not station_data:
                 return pn.pane.Alert(f"Station {station_key} not found.", alert_type='warning')

            # Example: Define date range for queries
            end_date = pd.Timestamp.now().date()
            start_date_90 = end_date - pd.Timedelta(days=90)
            start_date_year = end_date - pd.Timedelta(days=365)

            hourly_data_df = get_hourly_data_for_stations(
                session, # Pass session
                station_keys=[station_key],
                start_date=start_date_year, # Fetch enough data
                end_date=end_date,
                directions=[direction], # Assuming direction is integer
                classifications=[1] # Total volume
            )

        # --- Process Data and Create Panes ---
        if not hourly_data_df.empty:
            # Metadata Card
            metadata_card = pn.Card(..., title=f"Station Metadata: {station_data.station_id}")
            layout.append(metadata_card)

            # Folium Map Card
            # ... create folium map ...
            map_card = pn.Card(pn.pane.plot.Folium(folium_map), title="Station Location")
            layout.append(map_card)

            # Calculate profiles
            profile_df = calculate_hourly_profile(hourly_data_df) # Filter by date etc. inside this function
            profile_plot = profile_df.hvplot.line(...)
            profile_card = pn.Card(pn.pane.HoloViews(profile_plot), title="Typical Hourly Profile")
            layout.append(profile_card)

            # Recent Trend
            trend_df = hourly_data_df[hourly_data_df['count_date'] >= pd.to_datetime(start_date_90)].copy()
            trend_plot = trend_df.hvplot.line(...)
            trend_card = pn.Card(pn.pane.HoloViews(trend_plot), title="Recent Daily Trend")
            layout.append(trend_card)

        else:
            layout.append(pn.pane.Alert("No hourly data found for the selected station/period.", alert_type='warning'))

        return layout

    # --- Display Panel Components ---
    dashboard_column = pn.Column(
        pn.Row(station_key_select, direction_select),
        update_dashboard # The reactive function output
    )
    st.write(dashboard_column) # Render the Panel object in Streamlit

# Make sure this is called from main_app.py
# render_station_profile()