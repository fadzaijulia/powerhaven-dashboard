# Borehole Web GIS Dashboard Application

## Overview

This application:

1. Connects to a PostgreSQL/Supabase database.
2. Searches borehole records from the database.
3. Displays borehole information on a web application.
4. Shows dashboard statistics:

   * Total boreholes
   * Successful boreholes
   * Failed boreholes
   * Success rate
   * Failure rate
5. Displays all boreholes on an interactive Leaflet map.
6. Uses coordinates stored in the database.

The application uses:

* Python
* Streamlit
* Supabase/PostgreSQL
* Pandas
* Folium (Leaflet maps)
* Plotly

---

# 1. Install Required Packages

Open terminal or command prompt:

```bash
pip install streamlit pandas psycopg2-binary sqlalchemy folium streamlit-folium plotly
```

---

# 2. Example Database Table

Example table: `boreholes`

```sql
CREATE TABLE boreholes (
    borehole_id SERIAL PRIMARY KEY,
    borehole_name VARCHAR(100),
    district VARCHAR(100),
    village VARCHAR(100),
    yield_lph FLOAT,
    drilling_status VARCHAR(50),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    drilling_date DATE
);
```

Example values for `drilling_status`:

* Successful
* Failed

---

# 3. Streamlit Web Application Code (Supabase Version)

Create a file called:

```text
app.py
```

Paste the following code:

```python
import streamlit as st
import pandas as pd
from supabase import create_client, Client
import folium
from streamlit_folium import st_folium
import plotly.express as px

# =====================================================
# PAGE CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="Borehole Dashboard",
    layout="wide"
)

st.title("Borehole Drilling Dashboard")

# =====================================================
# SUPABASE CONNECTION
# =====================================================

SUPABASE_URL = "https://ewybimordizxtbxtughj.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV3eWJpbW9yZGl6eHRieHR1Z2hqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc5NjcwNzYsImV4cCI6MjA5MzU0MzA3Nn0.FBETeNXLGcp_0H3-lX2PTXJurbJENyAGQG12GuxTab0"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# =====================================================
# LOAD DATA FROM SUPABASE
# =====================================================

response = supabase.table("boreholes").select("*").execute()

# Convert to DataFrame

df = pd.DataFrame(response.data)

# =====================================================
# SIDEBAR SEARCH
# =====================================================

st.sidebar.header("Search Boreholes")

search_name = st.sidebar.text_input("Search by Borehole Name")

search_district = st.sidebar.selectbox(
    "Select District",
    ["All"] + sorted(df['district'].dropna().unique().tolist())
)

filtered_df = df.copy()

if search_name:
    filtered_df = filtered_df[
        filtered_df['borehole_name'].str.contains(search_name, case=False, na=False)
    ]

if search_district != "All":
    filtered_df = filtered_df[
        filtered_df['district'] == search_district
    ]

# =====================================================
# DASHBOARD METRICS
# =====================================================

successful = len(filtered_df[
    filtered_df['drilling_status'] == 'Successful'
])

failed = len(filtered_df[
    filtered_df['drilling_status'] == 'Failed'
])

total = len(filtered_df)

if total > 0:
    success_rate = round((successful / total) * 100, 2)
    failure_rate = round((failed / total) * 100, 2)
else:
    success_rate = 0
    failure_rate = 0

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Total Boreholes", total)
col2.metric("Successful", successful)
col3.metric("Failed", failed)
col4.metric("Success Rate", f"{success_rate}%")
col5.metric("Failure Rate", f"{failure_rate}%")

# =====================================================
# PIE CHART
# =====================================================

chart_df = pd.DataFrame({
    'Status': ['Successful', 'Failed'],
    'Count': [successful, failed]
})

fig = px.pie(
    chart_df,
    values='Count',
    names='Status',
    title='Borehole Success vs Failure'
)

st.plotly_chart(fig, use_container_width=True)

# =====================================================
# DISPLAY TABLE
# =====================================================

st.subheader("Borehole Records")

st.dataframe(filtered_df)

# =====================================================
# LEAFLET MAP
# =====================================================

st.subheader("Borehole Locations")

map_center = [-17.8252, 31.0335]

m = folium.Map(location=map_center, zoom_start=7)

for _, row in filtered_df.iterrows():

    if pd.notnull(row['latitude']) and pd.notnull(row['longitude']):

        color = 'green'

        if row['drilling_status'] == 'Failed':
            color = 'red'

        popup_text = f"""
        <b>Borehole:</b> {row['borehole_name']}<br>
        <b>District:</b> {row['district']}<br>
        <b>Village:</b> {row['village']}<br>
        <b>Yield:</b> {row['yield_lph']} LPH<br>
        <b>Status:</b> {row['drilling_status']}
        """

        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=popup_text,
            icon=folium.Icon(color=color)
        ).add_to(m)

st_folium(m, width=1200, height=600)

# =====================================================
# DOWNLOAD CSV
# =====================================================

csv = filtered_df.to_csv(index=False).encode('utf-8')

st.download_button(
    label="Download Filtered Data",
    data=csv,
    file_name='boreholes.csv',
    mime='text/csv'
)
```

---

# 4. Run the Application

Open terminal in the project folder:

```bash
streamlit run app.py
```

The app will open in your browser automatically.

---

# 5. Connecting Supabase

In Supabase:

1. Open your project.
2. Go to:

   * Settings
   * Database
3. Copy:

   * Host
   * Database name
   * Password
   * Port

Replace these values in the code:

```python
DB_HOST = "YOUR_HOST"
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASSWORD = "YOUR_PASSWORD"
DB_PORT = "5432"
```

---

# 6. Features of the System

## Search Functionality

Users can:

* Search boreholes by name.
* Filter boreholes by district.

---

## Dashboard Analytics

The dashboard automatically calculates:

* Total boreholes drilled
* Successful boreholes
* Failed boreholes
* Success percentage
* Failure percentage

---

## Interactive Leaflet Map

The map:

* Displays all borehole locations.
* Uses coordinates from the database.
* Shows popups with borehole information.
* Uses:

  * Green markers = successful boreholes
  * Red markers = failed boreholes

---

# 7. Suggested Improvements

You can later add:

* User login system
* Admin dashboard
* Upload CSV functionality
* PDF report generation
* Satellite basemap layers
* Spatial analysis
* Heatmaps
* Borehole clustering
* Water quality analysis
* Mobile responsiveness
* Real-time database updates

---

# 8. Recommended Folder Structure

```text
borehole_dashboard/

 app.py
 requirements.txt
 assets/
 data/
 README.md
```

---

# 9. requirements.txt

Create a file called:

```text
requirements.txt
```

Add:

```text
streamlit
pandas
psycopg2-binary
sqlalchemy
folium
streamlit-folium
plotly
```

---

# 10. Example Future GIS Expansion

You can later integrate:

* PostGIS
* GeoServer
* QGIS Server
* ArcGIS Online
* Remote sensing layers
* Borehole suitability models
* Groundwater interpolation
* Aquifer analysis

This can evolve into a complete Web GIS groundwater management system.
