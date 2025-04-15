**1. Database Data Model (PostgreSQL)**  STATUS =  NOT IMPLEMENTED 
Objective:  



use SQLAlchemy to interact with the database at all times, no 'native postgres
hard coded' SQL commands or quearies. Use SQLAlchemy.  



stations Table: Stores static station metadata.
station_key (INTEGER, Primary Key) - Unique identifier used across tables.
station_id (VARCHAR) - The public-facing station ID.
name (VARCHAR) - Station name description.
road_name (VARCHAR) - Main road name.
full_name (VARCHAR) - Detailed descriptive name.
common_road_name (VARCHAR) - Localised road name.
lga (VARCHAR) - Local Government Area.
suburb (VARCHAR) - Suburb name.
post_code (VARCHAR)
road_functional_hierarchy (VARCHAR) - e.g., 'Arterial Road', 'Local Road'.
lane_count (VARCHAR) - e.g., 'OneLane', 'TwoOrMoreLanes'.
road_classification_type (VARCHAR) - e.g., 'Road', 'Highway', 'Street'.
device_type (VARCHAR) - e.g., 'Tirtl', 'Trafficorder Tube Axlepair Counter'.
permanent_station (BOOLEAN) - True if permanent, False if sample.
vehicle_classifier (BOOLEAN) - True if it classifies vehicles.
heavy_vehicle_checking_station (BOOLEAN)
quality_rating (INTEGER) - Numerical quality score (e.g., 1-5).
wgs84_latitude (FLOAT)
wgs84_longitude (FLOAT)
location_geom (GEOMETRY(Point, 4326)) - Geospatial point using WGS84 SRID.
Other relevant columns from road_traffic_counts_station_reference.csv...
Indexes: Create indexes on station_key, station_id, lga, suburb, road_name, road_functional_hierarchy. Create a GiST index on location_geom for efficient spatial queries.
hourly_counts Table: Stores the time-series traffic data.
count_id (SERIAL, Primary Key) - Auto-incrementing unique ID for the row.
station_key (INTEGER, Foreign Key references stations(station_key))
traffic_direction_seq (INTEGER) - Refers to direction (Refer 5.2 in docs).
cardinal_direction_seq (INTEGER) - Refers to cardinal direction (Refer 5.3 in docs).
classification_seq (INTEGER) - Refers to vehicle class (Refer 5.4 in docs: 0=Unclassified, 1=All, 2=Light, 3=Heavy).
count_date (DATE) - The date of the count.
year (INTEGER) - Extracted year from date.
month (INTEGER) - Extracted month from date.
day_of_week (INTEGER) - 1 (Mon) to 7 (Sun).
is_public_holiday (BOOLEAN)
is_school_holiday (BOOLEAN)
hour_00 (INTEGER) - Traffic volume 00:00-00:59
hour_01 (INTEGER) - Traffic volume 01:00-01:59
... (up to hour_23) ...
hour_23 (INTEGER) - Traffic volume 23:00-23:59
daily_total (INTEGER) - Sum of hourly volumes for the day/class/direction.
Indexes: Create indexes on station_key, count_date, classification_seq, year, month, day_of_week.


PostGIS: Using GEOMETRY(geometry_type='POINT', srid=4326) requires the PostGIS extension to be enabled in your database (CREATE EXTENSION IF NOT EXISTS postgis;). This allows for efficient spatial indexing and queries later if needed. 
We'll need two main tables.

Nullability: Set nullable=False for columns that must have a value (like count_date). Adjust based on your actual data constraints.
Indexes: Added index=True to columns frequently used in WHERE clauses or JOIN conditions.
Relationships: relationship defines how Station and HourlyCount objects are linked. back_populates enables accessing the related objects from both sides (e.g., station.hourly_counts and hourly_count.station).



**2. Data Transformations & Calculated Columns use Python & Panda sqlalchemy**

STATUS =  NOT IMPLEMENTED


Peak Hour Volumes: Dynamically calculate sums for AM (hour_06 to hour_09) and PM (hour_15 to hour_18) peaks based on filters.
Average Hourly Profile: Calculate the average volume for each hour (00-23) over a selected period (e.g., month, year, weekdays, weekends).
AADT (Annual Average Daily Traffic): Calculate average daily_total over a full year, applying data quality rules (e.g., requiring >=19 hours of data per day counted). This is more complex and might be pre-calculated or calculated carefully on demand.
AAWT (Average Annual Weekday Traffic): Similar to AADT but only for Mon-Fri, excluding public holidays.
Heavy Vehicle Percentage: (Sum of daily_total where classification_seq=3) / (Sum of daily_total where classification_seq=1) for a given period and station (only for classifying stations).
Geospatial Data: Ensure wgs84_latitude and wgs84_longitude are used to create the location_geom point data during data loading.

1. Streamlit App Structure 

Objective:  
Create basic  Streamlit eweb page with a simple. Each feature below could be a page or a section within a page. Use st.sidebar for global filters like date range or LGA selection where applicable.

Colour theme:

Primary Colors:
Use Magenta (230, 0, 230) as the primary accent color for buttons, headers, or highlights to reflect the vibrant tone of the website.
Use Black (0, 0, 0) for backgrounds (e.g., navigation bar) to create contrast.
Use White (255, 255, 255) for text on dark backgrounds for readability.
Secondary Colors:
Use Light Gray (150, 150, 150) for background elements or secondary sections to mimic the road texture.
Use Dark Gray (50, 50, 50) for subtle elements like shadows, borders, or muted text.

Stremlit toml colour config file: 
app/config.toml

Stremlit python colour tool file:
app/stremlit_color_pallet.py

Graphics folder for website:
app/gfx/ptc-logo-white.png

-------------
 Write Test driven design tests first for each def and majopr app logic for testing using pytest. Then use python library Panel for UI components and HoloViews/hvPlot for plotting  with Folium for maps where specified. All components are mandatory, and details regarding labels, titles, dynamic updates, data requirements, and calculations are included for each. App stack uses  PostgreSQL database (stations and hourly_counts tables as previously defined) accessed via Python using SQLAlchemy within a Streamlit web application framework, where Panel objects are rendered.
---------------

**Feature 1: Traffic Station Profile Dashboard **

STATUS = NOT IMPLEMENTED

Objective: Provide a quick, comprehensive view of a single traffic count station's characteristics and recent/typical trends.
UI Components (Panel within Streamlit):
Filters:
pn.widgets.Select widget for selecting station_id or station_key. Options populated dynamically from the stations table. Label: "Select Station".
pn.widgets.Select widget for selecting Traffic Direction (traffic_direction_seq). Options mapped from numerical values (e.g., 1, 2) to descriptive text (e.g., "Prescribed Direction", "Both Directions"). Label: "Select Direction".
Visualizations (arranged using pn.Column or pn.GridSpec):
Metadata Display: pn.Card titled f"Station Metadata: {selected_station_id}". Content displayed using pn.pane.DataFrame or formatted pn.pane.Markdown showing: Road Name, LGA, Suburb, Road Functional Hierarchy, Device Type, Vehicle Classifier Status (Yes/No), Permanent Station Status (Yes/No), Quality Rating.
Station Location Map: pn.pane.plot.Folium pane displaying a Folium map centered on the selected station. A single folium.Marker indicates the station location. Popup on marker click shows Station ID and Full Name. Title embedded within the Panel layout: f"Location: {selected_station_id}".
Typical Hourly Profile Chart: pn.pane.HoloViews pane displaying a HoloViews line chart generated via hvplot.
Input: Pandas DataFrame with columns ['Hour', 'Average Volume', 'Period'] ('Period' being 'Weekday' or 'Weekend').
Plot: df.hvplot.line(x='Hour', y='Average Volume', by='Period', title=f"Typical Hourly Traffic Profile ({selected_direction_desc})", xlabel="Hour of Day (0-23)", ylabel="Average Traffic Volume", legend='top_left', grid=True, responsive=True).
Labels: X-axis="Hour of Day (0-23)", Y-axis="Average Traffic Volume". Title is dynamic based on selection. Legend clearly labels "Weekday" and "Weekend".
Recent Daily Volume Trend Chart: pn.pane.HoloViews pane displaying a HoloViews line chart generated via hvplot.
Input: Pandas DataFrame with columns ['Date', 'Total Daily Volume'].
Plot: df.hvplot.line(x='Date', y='Total Daily Volume', title=f"Recent Daily Traffic Volume ({selected_direction_desc}) - Last 90 Days", xlabel="Date", ylabel="Total Daily Volume", grid=True, responsive=True).
Labels: X-axis="Date", Y-axis="Total Daily Volume". Title is dynamic based on selection.
Data Requirements:
SQL Query: SELECT * FROM stations WHERE station_key = :selected_key.
SQL Query: SELECT count_date, day_of_week, is_public_holiday, hour_00, ..., hour_23, daily_total FROM hourly_counts WHERE station_key = :selected_key AND traffic_direction_seq = :selected_direction AND classification_seq = 1 AND count_date >= :start_date_90_days AND count_date >= :start_date_last_year. Filters applied in Python.
Calculations Needed (Python/Pandas):
Filter hourly data for the last full year.
Calculate average volume for each hour (0-23) separately for weekdays (Mon-Fri, non-holiday) and weekends (Sat-Sun, non-holiday).
Filter hourly data for the last 90 days to get daily totals for the trend chart.
Dynamic Behavior: Define Python functions linked to the station_key and traffic_direction_seq widgets using @pn.depends or pn.bind. These functions will:
Fetch data from PostgreSQL based on widget values.
Perform calculations (averaging, filtering).
Generate Pandas DataFrames.
Create/update the Folium map object.
Create/update the HoloViews plot objects using hvplot.
Update the content/title of the pn.Card, pn.pane.DataFrame/Markdown, pn.pane.plot.Folium, and pn.pane.HoloViews panes.

**Feature 2: Peak Hour Analysis View**
STATUS = NOT IMPLEMENTED

Objective: Identify and visualize AM and PM peak traffic periods and volumes for selected areas or road types.
UI Components (Panel within Streamlit):
Filters:
pn.widgets.MultiSelect for selecting LGA(s). Label: "Select LGA(s)". Options populated from stations table.
pn.widgets.MultiSelect for selecting Suburb(s). Label: "Select Suburb(s)". Options dynamically filtered based on selected LGA(s).
pn.widgets.MultiSelect for selecting Road Functional Hierarchy (road_functional_hierarchy). Label: "Select Road Type(s)". Options populated from stations table.
pn.widgets.DateRangeSlider for selecting the analysis period. Label: "Select Date Range".
pn.widgets.Select for selecting Traffic Direction (traffic_direction_seq). Label: "Select Direction".
Visualizations:
Average Weekday Hourly Profile Chart: pn.pane.HoloViews pane displaying a HoloViews line chart with overlays.
Input: Pandas DataFrame ['Hour', 'Average Volume'].
Plot: profile_plot = df.hvplot.line(x='Hour', y='Average Volume', title=f"Average Weekday Hourly Profile ({selected_direction_desc})", xlabel="Hour of Day (0-23)", ylabel="Average Traffic Volume", grid=True, responsive=True).
Overlays: am_highlight = hv.VSpan(6, 10, color='lightblue', alpha=0.3), pm_highlight = hv.VSpan(15, 19, color='lightcoral', alpha=0.3). Combined plot: profile_plot * am_highlight * pm_highlight.
Labels: X-axis="Hour of Day (0-23)", Y-axis="Average Traffic Volume". Title is dynamic.
Peak Volume Table: pn.pane.DataFrame pane.
Input: Pandas DataFrame ['Station ID', 'Road Name', 'Avg AM Peak Volume', 'Avg PM Peak Volume'].
Display: Show the DataFrame, allow sorting by clicking column headers.
Title: pn.pane.Markdown(f"### Average Peak Period Volumes ({selected_direction_desc})").
Data Requirements:
SQL Query: SELECT station_key, station_id, road_name FROM stations WHERE lga IN :selected_lgas AND suburb IN :selected_suburbs AND road_functional_hierarchy IN :selected_hierarchies.
SQL Query: SELECT station_key, hour_06, ..., hour_09, hour_15, ..., hour_18, day_of_week, is_public_holiday FROM hourly_counts WHERE station_key IN :relevant_keys AND count_date BETWEEN :start_date AND :end_date AND classification_seq = 1 AND traffic_direction_seq = :selected_direction.
Calculations Needed (Python/Pandas):
Filter counts for weekdays (Mon-Fri) and non-public holidays.
Calculate the average volume for each hour (0-23) across all selected stations and valid days.
For each station, calculate the average sum of volumes for AM peak (hours 6-9) and PM peak (hours 15-18) over the valid days.
Dynamic Behavior: Define Python functions linked to all filter widgets. These functions re-query data, perform calculations, generate DataFrames, create/update the HoloViews plot (with overlays) and the DataFrame pane. The Suburb MultiSelect options should update reactively based on the LGA MultiSelect value.


**Feature 3: Corridor Traffic Flow Comparison** STATUS = NOT IMPLEMENTED
Objective: Compare traffic volumes and patterns at multiple stations along a specific road corridor.
UI Components (Panel within Streamlit):
Filters:
pn.widgets.AutocompleteInput for selecting Road Name (road_name or common_road_name). Options populated from stations table. Label: "Select Road Name".
pn.widgets.Select for selecting LGA (can be 'All'). Label: "Select LGA (Optional)". Options populated from stations table.
pn.widgets.Select for selecting Traffic Direction. Label: "Select Direction".
pn.widgets.DateRangeSlider for selecting the analysis period. Label: "Select Date Range".
Visualizations:
Corridor Map: pn.pane.plot.Folium pane.
Features: Displays a Folium map centered on the identified stations. Uses folium.Marker for each station. Popup on click shows station_id and full_name. folium.plugins.MarkerCluster is used.
Title: pn.pane.Markdown(f"### Stations along {selected_road_name}").
Comparative Hourly Profiles Chart: pn.pane.HoloViews pane.
Input: Pandas DataFrame ['Hour', 'Average Volume', 'Station ID'].
Plot: df.hvplot.line(x='Hour', y='Average Volume', by='Station ID', title=f"Hourly Profiles Along {selected_road_name} ({selected_direction_desc}, {selected_period})", xlabel="Hour of Day (0-23)", ylabel="Average Traffic Volume", legend='top_left', grid=True, responsive=True).
Labels: X-axis="Hour of Day (0-23)", Y-axis="Average Traffic Volume". Title dynamic. Legend identifies stations.
Volume Comparison Table: pn.pane.DataFrame pane.
Input: Pandas DataFrame ['Station ID', 'Full Name', 'Average Daily Total Volume'].
Display: Show the DataFrame, sortable by volume.
Title: pn.pane.Markdown(f"### Average Daily Volumes Along {selected_road_name} ({selected_direction_desc}, {selected_period})").
Data Requirements:
SQL Query: SELECT station_key, station_id, full_name, wgs84_latitude, wgs84_longitude FROM stations WHERE (road_name = :selected_road OR common_road_name = :selected_road) AND (:selected_lga = 'All' OR lga = :selected_lga).
SQL Query: SELECT station_key, hour_00, ..., hour_23, daily_total FROM hourly_counts WHERE station_key IN :corridor_keys AND count_date BETWEEN :start_date AND :end_date AND classification_seq = 1 AND traffic_direction_seq = :selected_direction.
Calculations Needed (Python/Pandas):
Calculate the average volume for each hour (0-23) for each station over the selected period.
Calculate the average daily_total for each station over the selected period.
Dynamic Behavior: Define Python functions linked to all filter widgets. They re-query data based on selections, calculate averages, generate DataFrames, create/update the Folium map and HoloViews chart objects, and update the Panel panes.

**Feature 4: Heavy Vehicle Pattern Explorer**

STATUS = NOT IMPLEMENTED

Objective: Analyze patterns specifically for heavy vehicles (trucks) at classifying stations.
UI Components (Panel within Streamlit):
Filters:
pn.widgets.MultiSelect for LGA(s). Label: "Select LGA(s)".
pn.widgets.MultiSelect for Road Functional Hierarchy. Label: "Select Road Type(s)".
pn.widgets.DateRangeSlider for period selection. Label: "Select Date Range".
pn.widgets.Select for Traffic Direction. Label: "Select Direction".
Visualizations:
HV Hourly Profile Chart: pn.pane.HoloViews pane.
Input: Pandas DataFrame ['Hour', 'Average HV Volume'].
Plot: df_hv.hvplot.line(x='Hour', y='Average HV Volume', title=f"Average Weekday Hourly Heavy Vehicle Profile ({selected_direction_desc})", xlabel="Hour of Day (0-23)", ylabel="Average Heavy Vehicle Volume", grid=True, responsive=True).
Labels: X-axis="Hour of Day (0-23)", Y-axis="Average Heavy Vehicle Volume". Title dynamic.
HV Percentage Profile Chart: pn.pane.HoloViews pane.
Input: Pandas DataFrame ['Hour', 'HV Percentage (%)'].
Plot: df_hv_perc.hvplot.line(x='Hour', y='HV Percentage (%)', title=f"Average Weekday Hourly Heavy Vehicle Percentage ({selected_direction_desc})", xlabel="Hour of Day (0-23)", ylabel="Heavy Vehicle Percentage (%)", grid=True, responsive=True).
Labels: X-axis="Hour of Day (0-23)", Y-axis="Heavy Vehicle Percentage (%)". Title dynamic.
Top HV Stations Table: pn.pane.DataFrame pane.
Input: Pandas DataFrame ['Station ID', 'Road Name', 'Avg Daily HV Volume', 'Avg Daily HV Percentage'].
Display: Sorted by Avg Daily HV Volume (descending).
Title: pn.pane.Markdown(f"### Top Heavy Vehicle Stations ({selected_direction_desc}, {selected_period})").
Data Requirements:
SQL Query: SELECT station_key, station_id, road_name FROM stations WHERE vehicle_classifier = True AND lga IN :selected_lgas AND road_functional_hierarchy IN :selected_hierarchies.
SQL Query: SELECT station_key, classification_seq, hour_00, ..., hour_23, daily_total, day_of_week, is_public_holiday FROM hourly_counts WHERE station_key IN :classifier_keys AND count_date BETWEEN :start_date AND :end_date AND classification_seq IN (1, 3) AND traffic_direction_seq = :selected_direction.
Calculations Needed (Python/Pandas):
Filter counts for weekdays (Mon-Fri) and non-public holidays.
Calculate average hourly volume for classification_seq=3 (Heavy) across selected stations/days.
Calculate average hourly volume for classification_seq=1 (All) across selected stations/days.
Calculate average hourly HV percentage = (Avg HV Volume / Avg All Volume) * 100.
Calculate average daily HV volume (from daily_total, seq=3) per station.
Calculate average daily All volume (from daily_total, seq=1) per station.
Calculate average daily HV percentage per station.
Dynamic Behavior: Define Python functions linked to filter widgets to re-query, calculate, generate DataFrames, update HoloViews plots, and update the DataFrame pane.

**Feature 5: Weekday vs. Weekend Traffic Comparison** 

STATUS = NOT IMPLEMENTED

Objective: Highlight differences in traffic patterns between typical weekdays and weekends.
UI Components (Panel within Streamlit):
Filters:
pn.widgets.Select widget for choosing selection mode (Station, LGA, Hierarchy). Label: "Select By".
Dynamic Widget (depends on selection mode):
If "Station": pn.widgets.MultiSelect for Station ID(s). Label: "Select Station(s)".
If "LGA": pn.widgets.Select for LGA. Label: "Select LGA".
If "Hierarchy": pn.widgets.Select for Road Functional Hierarchy. Label: "Select Road Type".
pn.widgets.Select for Traffic Direction. Label: "Select Direction".
pn.widgets.Select for Year. Label: "Select Year".
Visualizations:
pn.Tabs container with two tabs: "Hourly Profiles" and "Key Metrics".
Tab 1: Hourly Profiles Chart: pn.pane.HoloViews pane.
Input: Pandas DataFrame ['Hour', 'Average Volume', 'Period'] ('Period' is 'Weekday' or 'Weekend').
Plot: df.hvplot.line(x='Hour', y='Average Volume', by='Period', title=f"Weekday vs Weekend Hourly Profile ({selection_desc}, {selected_direction_desc}, {selected_year})", xlabel="Hour of Day (0-23)", ylabel="Average Traffic Volume", legend='top_left', grid=True, responsive=True).
Labels: X-axis="Hour of Day (0-23)", Y-axis="Average Traffic Volume". Title dynamic. Legend labels "Weekday" and "Weekend".
Tab 2: Key Metrics Table: pn.pane.DataFrame pane.
Input: Pandas DataFrame with index ['Weekday', 'Weekend'] and columns ['Average Daily Volume', 'Average AM Peak Volume', 'Average PM Peak Volume'].
Title: pn.pane.Markdown(f"### Weekday vs Weekend Key Metrics ({selection_desc}, {selected_direction_desc}, {selected_year})").
Data Requirements:
SQL Query: Based on filter selection, get relevant station_keys from stations.
SQL Query: SELECT station_key, day_of_week, is_public_holiday, hour_06, ..., hour_09, hour_15, ..., hour_18, daily_total FROM hourly_counts WHERE station_key IN :relevant_keys AND year = :selected_year AND classification_seq = 1 AND traffic_direction_seq = :selected_direction.
Calculations Needed (Python/Pandas):
Separate data into Weekdays (Mon-Fri, non-holiday) and Weekends (Sat-Sun, non-holiday).
Calculate average hourly profile across selected stations/days for each category.
Calculate average daily total volume for each category.
Calculate average AM Peak (sum hours 6-9) and PM Peak (sum hours 15-18) volumes for each category.
Dynamic Behavior: Define Python functions linked to all filters. Functions re-query, calculate, generate DataFrames, update the HoloViews plot and the DataFrame pane within the appropriate tab. The dynamic widget for station/LGA/hierarchy selection needs logic based on the "Select By" widget.

**Feature 6: Data Quality & Coverage Overview** 

STATUS = NOT IMPLEMENTED

Objective: Provide transparency on the reliability and completeness of the traffic data.
UI Components (Panel within Streamlit):
Filters:
pn.widgets.MultiSelect for LGA(s). Label: "Filter by LGA(s)".
pn.widgets.CheckboxGroup widget with options: 'Permanent Stations', 'Sample Stations', 'Vehicle Classifiers', 'Quality Rating 5', 'Quality Rating 4', 'Quality Rating <4'. Label: "Filter Station Types".
Visualizations:
Interactive Quality Map: pn.pane.plot.Folium pane.
Features: Folium map displaying stations matching filters. Use folium.CircleMarker for each station. Color code by quality_rating (5=green, 4=yellow, <4=red). Use marker fill/border or slightly different icons to indicate permanent_station (True/False) and vehicle_classifier (True/False) if desired and visually manageable. Popup shows: Station ID, Quality Rating, Device Type, Classifier (T/F), Permanent (T/F). Use folium.plugins.MarkerCluster. Implement logic to filter markers displayed based on the CheckboxGroup selection using Folium's FeatureGroup or LayerControl capabilities if rendering dynamically, or filter the DataFrame before creating markers if generating the map object wholesale on change.
Title: pn.pane.Markdown("### Station Data Quality and Type Overview").
Coverage Summary Table: pn.pane.DataFrame pane.
Input: Pandas DataFrame aggregated by LGA. Columns: LGA, Total Stations, Count Permanent, Count Sample, Count Classifier, Avg Quality Rating.
Title: pn.pane.Markdown("### Data Coverage Summary by LGA").
Data Requirements:
SQL Query: SELECT lga, station_key, quality_rating, device_type, permanent_station, vehicle_classifier, wgs84_latitude, wgs84_longitude FROM stations WHERE (:selected_lgas IS NULL OR lga IN :selected_lgas). Python applies further filtering based on CheckboxGroup.
Calculations Needed (Python/Pandas):
Group station data by LGA and calculate counts/averages for the summary table.
Filter station data based on CheckboxGroup selections before plotting on the map.
Dynamic Behavior: Define Python functions linked to LGA and CheckboxGroup widgets. Functions re-query the stations table, filter the resulting DataFrame based on checkboxes, generate the summary DataFrame, create/update the Folium map object, and update the Panel panes.

**Feature 7: LGA/Suburb Traffic Snapshot**

STATUS = NOT IMPLEMENTED

Objective: Generate a high-level summary report/dashboard for a specific council area or suburb.
UI Components (Panel within Streamlit):
Filters:
pn.widgets.Select for LGA. Label: "Select LGA". Options from stations.
pn.widgets.Select for Suburb. Label: "Select Suburb". Options dynamically updated based on selected LGA.
pn.widgets.Select for Year. Label: "Select Year for Averages".
Visualizations (arranged using pn.Column, pn.Row, pn.Card):
Snapshot Map: pn.pane.plot.Folium pane.
Features: Folium map centered on the LGA/Suburb. folium.Marker for each station within the selection. Popup shows Station ID and Road Name. Use folium.plugins.MarkerCluster.
Title: pn.pane.Markdown(f"### Traffic Stations in {selected_lga_suburb}").
Summary Statistics Card: pn.Card titled "Area Summary". Displays using pn.pane.Markdown:
Total Stations in Selection: [Count]
Average AADT (All Stations): [Value] (calculated across stations with data for the year)
Most Common Road Hierarchy: [Type]
Top 5 Busiest Stations Table: pn.pane.DataFrame pane.
Input: Pandas DataFrame ['Station ID', 'Road Name', 'AADT/Avg Daily Volume']. Sorted descending by volume.
Title: pn.pane.Markdown(f"### Top 5 Busiest Stations ({selected_year})").
Road Hierarchy Distribution Chart: pn.pane.HoloViews pane.
Input: Pandas DataFrame ['Hierarchy', 'Count'].
Plot: df_counts.hvplot.bar(x='Hierarchy', y='Count', title="Distribution of Station Road Types", xlabel="Road Hierarchy", ylabel="Number of Stations", rot=45, responsive=True).
Labels: X-axis="Road Hierarchy", Y-axis="Number of Stations". Title clear.
Data Requirements:
SQL Query: SELECT station_key, station_id, road_name, road_functional_hierarchy, wgs84_latitude, wgs84_longitude FROM stations WHERE lga = :selected_lga AND suburb = :selected_suburb.
SQL Query (or join/subquery): Retrieve daily_total from hourly_counts for the relevant station_keys and selected_year, where classification_seq = 1, to calculate AADT/Avg Daily.
Calculations Needed (Python/Pandas):
Calculate average daily volume per station for the selected year.
Calculate average daily volume across all selected stations.
Count stations per hierarchy type. Find the most common hierarchy.
Identify and rank the top 5 stations by average daily volume.
Dynamic Behavior: Define Python functions linked to LGA, Suburb, and Year widgets. Functions re-query, calculate stats, generate DataFrames, update the Folium map, HoloViews chart, DataFrame pane, and Card content. Suburb options update based on LGA selection.


**Feature 8: Directional Flow Analysis Dashboard**

STATUS = NOT IMPLEMENTED

Objective: Analyze and visualize the balance and dominance of traffic flow by direction.
UI Components (Panel within Streamlit):
Filters:
pn.widgets.Select for Station ID. Label: "Select Station".
pn.widgets.DateRangeSlider for period selection. Label: "Select Date Range".
pn.widgets.Select for Direction Pair (e.g., "Northbound vs Southbound", "Eastbound vs Westbound"). Label: "Select Direction Pair". Options dynamically enabled based on available cardinal_direction_seq for the selected station.
Visualizations:
Directional Hourly Profiles Chart: pn.pane.HoloViews pane.
Input: Pandas DataFrame ['Hour', 'Average Volume', 'Direction'].
Plot: df.hvplot.line(x='Hour', y='Average Volume', by='Direction', title=f"Average Hourly Volume by Direction ({selected_station_id}, {selected_period})", xlabel="Hour of Day (0-23)", ylabel="Average Traffic Volume", legend='top_left', grid=True, responsive=True).
Labels: X-axis="Hour of Day (0-23)", Y-axis="Average Traffic Volume". Title dynamic. Legend clearly labels directions (e.g., "Northbound", "Southbound").
Directional Split Chart: pn.pane.HoloViews pane.
Input: Pandas DataFrame ['Hour', 'Percentage', 'Direction'].
Plot: df_split.hvplot.area(x='Hour', y='Percentage', by='Direction', stacked=True, title=f"Hourly Directional Split Percentage ({selected_station_id}, {selected_period})", xlabel="Hour of Day (0-23)", ylabel="Directional Split (%)", ylim=(0, 100), grid=True, responsive=True).
Labels: X-axis="Hour of Day (0-23)", Y-axis="Directional Split (%)". Title dynamic. Legend labels directions.
Peak Directional Dominance Card: pn.Card titled "Peak Period Directional Dominance". Displays using pn.pane.Markdown:
AM Peak (6-10am): [Dominant Direction] ([XX]%) vs [Other Direction] ([YY]%)
PM Peak (3-7pm): [Dominant Direction] ([XX]%) vs [Other Direction] ([YY]%)
Data Requirements:
SQL Query: First query stations for the selected station_id to determine available cardinal_direction_seq pairs.
SQL Query: SELECT cardinal_direction_seq, hour_00, ..., hour_23 FROM hourly_counts WHERE station_key = :selected_key AND count_date BETWEEN :start_date AND :end_date AND classification_seq = 1 AND cardinal_direction_seq IN (:dir1, :dir2).
Calculations Needed (Python/Pandas):
Calculate average hourly profile for each selected direction over the period.
Calculate the total volume for each direction.
Calculate the percentage split for each hour: (Dir1_Vol / (Dir1_Vol + Dir2_Vol)) * 100.
Calculate total volume for each direction during AM peak (6-9) and PM peak (15-18) and determine the dominant direction and percentage split for peaks.
Dynamic Behavior: Define Python functions linked to Station, Period, and Direction Pair widgets. Functions check available directions for the station, update the Direction Pair widget options, re-query data, perform calculations, update HoloViews plots, and update the Card content.

**Feature 9: Road Hierarchy Traffic Benchmarking**

STATUS = NOT IMPLEMENTED
Objective: Compare typical traffic volumes and patterns across different road classes within a region.
UI Components (Panel within Streamlit):
Filters:
pn.widgets.Select for LGA or RMS Region (if available). Label: "Select Region/LGA".
pn.widgets.Select for Year. Label: "Select Year for Averages".
pn.widgets.CheckboxGroup to select Road Hierarchies to include. Label: "Include Road Types". Options populated from stations table.
Visualizations:
AADT Distribution by Hierarchy Chart: pn.pane.HoloViews pane.
Input: Pandas DataFrame ['Hierarchy', 'AADT/Avg Daily Volume'].
Plot: df_aadt.hvplot.box(y='AADT/Avg Daily Volume', by='Hierarchy', title=f"Volume Distribution by Road Hierarchy ({region_desc}, {selected_year})", ylabel="AADT / Avg Daily Volume", xlabel="Road Hierarchy", grid=True, rot=45, responsive=True).
Labels: Y-axis="AADT / Avg Daily Volume", X-axis="Road Hierarchy". Title dynamic.
Typical Hourly Profiles by Hierarchy Chart: pn.pane.HoloViews pane.
Input: Pandas DataFrame ['Hour', 'Average Volume', 'Hierarchy'].
Plot: df_profiles.hvplot.line(x='Hour', y='Average Volume', by='Hierarchy', title=f"Typical Weekday Hourly Profile by Road Hierarchy ({region_desc}, {selected_year})", xlabel="Hour of Day (0-23)", ylabel="Average Traffic Volume", legend='top_left', grid=True, responsive=True).
Labels: X-axis="Hour of Day (0-23)", Y-axis="Average Traffic Volume". Title dynamic. Legend indicates hierarchy.
Data Requirements:
SQL Query: SELECT station_key, road_functional_hierarchy FROM stations WHERE (:region_lga_filter applied) AND road_functional_hierarchy IN :selected_hierarchies.
SQL Query: SELECT station_key, day_of_week, is_public_holiday, hour_00, ..., hour_23, daily_total FROM hourly_counts WHERE station_key IN :relevant_keys AND year = :selected_year AND classification_seq = 1.
Calculations Needed (Python/Pandas):
Calculate AADT or Average Daily volume per station for the selected year.
Join volume data with station hierarchy.
Group data by hierarchy for the box plot.
Filter for weekdays (non-holiday). For each hierarchy group, calculate the average volume for each hour across all stations in that group.
Dynamic Behavior: Define Python functions linked to filters. Functions re-query, calculate AADT/averages, group data, generate DataFrames, update HoloViews plots.

**Feature 10: Monthly/Seasonal Trend Analyzer**

STATUS = NOT IMPLEMENTED

Objective: Identify and visualize variations in traffic volume across different months or seasons.
UI Components (Panel within Streamlit):
Filters:
pn.widgets.Select for selection mode (Station, LGA, Hierarchy). Label: "Select By".
Dynamic Widget based on selection mode (MultiSelect for Station, Select for LGA/Hierarchy).
pn.widgets.Select for Traffic Direction. Label: "Select Direction".
pn.widgets.MultiSelect for Year(s). Label: "Select Year(s)".
Visualizations:
Monthly Average Daily Traffic Chart: pn.pane.HoloViews pane.
Input: Pandas DataFrame ['Month', 'Average Daily Volume', 'Year'].
Plot: df_monthly.hvplot.bar(x='Month', y='Average Daily Volume', by='Year', title=f"Average Daily Traffic Volume by Month ({selection_desc}, {selected_direction_desc})", xlabel="Month", ylabel="Average Daily Volume", grid=True, responsive=True, legend='top_right').
Labels: X-axis="Month" (show names or numbers 1-12), Y-axis="Average Daily Volume". Title dynamic. Legend indicates year if multiple selected.
School Holiday vs Term Time Comparison Chart: pn.pane.HoloViews pane.
Input: Pandas DataFrame ['Month', 'Average Daily Volume', 'Holiday Status'] ('Holiday Status' being 'Term Time' or 'School Holiday'). Averages calculated across selected stations/days for the latest selected year.
Plot: df_holiday.hvplot.bar(x='Month', y='Average Daily Volume', by='Holiday Status', title=f"School Holiday vs Term Time Comparison ({latest_year})", xlabel="Month", ylabel="Average Daily Volume", grid=True, responsive=True, legend='top_right').
Labels: X-axis="Month", Y-axis="Average Daily Volume". Title dynamic. Legend labels "Term Time" and "School Holiday".
Data Requirements:
Query stations based on filter to get station_keys.
SQL Query: SELECT station_key, month, daily_total, is_school_holiday FROM hourly_counts WHERE station_key IN :relevant_keys AND year IN :selected_years AND classification_seq = 1 AND traffic_direction_seq = :selected_direction.
Calculations Needed (Python/Pandas):
Calculate average daily_total per month (and per year if comparing multiple).
For the latest selected year, calculate average daily_total grouped by month and is_school_holiday status.
Dynamic Behavior: Define Python functions linked to filters. Functions re-query, calculate averages, generate DataFrames, update HoloViews plots. Dynamic widget for selection mode required.