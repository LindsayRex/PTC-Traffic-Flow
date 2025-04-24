**Tables:**

stations - Main table storing static station metadata
Primary key: station_key
Contains location data, road info, and station characteristics
Uses PostGIS geometry column for spatial queries
hourly_counts - Time-series traffic data
Primary key: count_id
Foreign key: station_key references stations(station_key)
Stores 24 hourly columns (hour_00 to hour_23)
Includes metadata like date, classification, direction

**Indexes:**

idx_station_composite on stations(lga, suburb, road_name)
Optimizes queries filtering by location attributes
idx_hourly_composite on hourly_counts(station_key, count_date, classification_seq)
Improves performance for time-series queries
GiST index on stations(location_geom)
Enables efficient spatial queries using PostGIS
Regular indexes on frequently queried columns:
station_id
road_name
common_road_name
lga
suburb
road_functional_hierarchy
count_date
year
month
day_of_week
classification_seq
Calculated Columns/Values:

d**aily_total** - Sum of all hourly volumes (only set if ≥19 valid hours)
location_geom - PostGIS point geometry calculated from latitude/longitude
year, month, day_of_week - Extracted from count_date for easier querying
The schema is optimized for:

**Spatial queries using PostGIS**
Time-series analysis
Location-based filtering
Vehicle classification analysis
Directional flow studies
The big integer types are used for traffic counts to handle large volumes, and boolean flags help identify special conditions like holidays and permanent stations.


The **spatial_ref_sys** table is a special system table that's automatically created by PostGIS (the spatial extension for PostgreSQL) when you run CREATE EXTENSION postgis. This table contains information about spatial reference systems (coordinate systems) that PostGIS uses for geospatial operations.

In the context of your traffic flow application, this table is important because:

Your Station model has a location_geom column of type Geometry('POINT', srid=4326) which stores the geographical coordinates of each traffic counting station
The SRID 4326 refers to the WGS84 coordinate system (the standard system used for GPS coordinates)
PostGIS uses the spatial_ref_sys table to understand how to handle these coordinates and perform spatial calculations
You don't need to drop this table because:

It's a system table managed by PostGIS
Your application needs it for storing and querying station locations
It will be automatically recreated when PostGIS is enabled
This is why the table persists even after dropping all tables - it's intentionally protected as a system table.
