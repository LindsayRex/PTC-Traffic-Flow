# TDD-Style Test Plan

Here’s a condensed TDD‑style test plan in three broad categories:

1. Data Access & Validation  
   • DB session acquisition (success/failure)  
   • get_all_station_metadata, get_station_details, get_latest_data_date, get_hourly_data_for_stations  
     – Return valid data, empty DataFrame, or None → appropriate Streamlit error/warning branches  
   • Dynamic date‐range calc  
     – Valid latest_date → correct 90‑day & full‑year bounds  
     – latest_date None or error → warning path

2. Data Processing & Business Logic  
   • process_hourly_profile  
     – All hour_NN columns present → correct mean per hour & Period label  
     – Missing hour columns → skips them  
     – Empty input → empty result  
   • Recent daily trend grouping  
     – Correct daily total aggregation over last 90 days  
     – Empty or incomplete data → warning

3. Visualization & UI Rendering  
   • embed_bokeh_plot  
     – Renders valid HTML on success  
     – Returns None and logs error on render/save failure  
     – Temp file creation & cleanup behavior  
   • Streamlit components  
     – selectbox defaults and mapping  
     – Tabs flow: “Station Info” (table + map), “Traffic Profiles” (hvplot → components.html), “Daily Trends”  
     – st.error/st.warning invoked in each failure branch  
     – spinners around data loads  
   • Folium map rendering  
     – Valid lat/lon → map with marker  
     – Missing coords → warning message