import streamlit as st
import pandas as pd
from supabase import create_client, Client
import pydeck as pdk

# --- Supabase connection ---
url = "https://mhcsryyqvhyntzrbdyuc.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1oY3NyeXlxdmh5bnR6cmJkeXVjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjE4MDM1NTcsImV4cCI6MjA3NzM3OTU1N30.7aa5wtN-1XQbVsOchmsSyRe2CcpYDzPyBMPG59zsrOI"  # Replace with your updated anon key
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Powerhaven Boreholes Dashboard", layout="wide")

# ============================
# 🔹 LOAD DATA FUNCTION
# ============================
def load_data():
    merged_df = pd.DataFrame()

    # Load tables with error handling
    tables = ["clients", "boreholes", "survey_points", "siting_reports", "drilling_reports"]
    dataframes = {}
    for table in tables:
        try:
            df = pd.DataFrame(supabase.table(table).select("*").execute().data)
            if "client_id" in df.columns:
                df["client_id"] = df["client_id"].astype(str)
            dataframes[table] = df
        except Exception as e:
            st.warning(f"Failed to load table '{table}': {e}")
            dataframes[table] = pd.DataFrame()

    clients_df = dataframes["clients"]
    merged_df = clients_df.copy()

    # Merge other tables
    for t in ["boreholes", "survey_points", "siting_reports", "drilling_reports"]:
        df = dataframes[t]
        if "client_id" in df.columns:
            merged_df = merged_df.merge(df, on="client_id", how="left", suffixes=("", f"_{t}"))

    # Ensure latitude and longitude columns are numeric
    for col in ["latitude", "longitude", "latitude_survey_points", "longitude_survey_points"]:
        if col in merged_df.columns:
            merged_df[col] = pd.to_numeric(merged_df[col], errors="coerce")

    return merged_df

# ============================
# 🔹 LOAD DATA
# ============================
st.title("💧 Powerhaven Boreholes & Solar Dashboard")

with st.spinner("Loading data from Supabase..."):
    df = load_data()

if df.empty:
    st.error("No data loaded.")
    st.stop()

# ------------------------
# Debug: Show coordinates
# ------------------------
st.subheader("Debug: Coordinates")
st.write(df[["client_name", "latitude", "longitude", "latitude_survey_points", "longitude_survey_points"]])
st.write("Number of valid borehole points:", df.dropna(subset=["latitude","longitude"]).shape[0])
st.write("Number of valid survey points:", df.dropna(subset=["latitude_survey_points","longitude_survey_points"]).shape[0])

# ============================
# 🔹 CLIENT FILTER (table only)
# ============================
client_options = df["client_name"].dropna().unique().tolist()
selected_client = st.selectbox("Select Client to view table", options=client_options)

filtered_df = df[df["client_name"] == selected_client]

st.subheader(f"📊 Data for {selected_client}")
st.dataframe(filtered_df)

# ============================
# 🔹 MAP WITH PYDECK (all clients)
# ============================

# Combine coordinates: use borehole coords if available, otherwise survey point coords
map_df = df.copy()
map_df["map_lat"] = map_df["latitude"].combine_first(map_df["latitude_survey_points"])
map_df["map_lon"] = map_df["longitude"].combine_first(map_df["longitude_survey_points"])

# Drop rows with no coordinates
map_df = map_df.dropna(subset=["map_lat", "map_lon"])

if map_df.empty:
    st.info("No location data available to display on the map.")
else:
    # Assign a unique color for each client
    unique_clients = map_df["client_name"].dropna().unique().tolist()
    color_map = {name: [int(hash(name) % 256), int((hash(name)*7) % 256), int((hash(name)*13) % 256), 160] for name in unique_clients}
    map_df["color"] = map_df["client_name"].map(color_map)

    # Default map view
    initial_lat = map_df["map_lat"].mean()
    initial_lon = map_df["map_lon"].mean()

    st.subheader("📍 Borehole / Survey Locations for All Clients")
    st.pydeck_chart(pdk.Deck(
        map_style='mapbox://styles/mapbox/light-v9',
        initial_view_state=pdk.ViewState(
            latitude=initial_lat,
            longitude=initial_lon,
            zoom=10,
            pitch=0
        ),
        layers=[
            pdk.Layer(
                "ScatterplotLayer",
                data=map_df,
                get_position='[map_lon, map_lat]',
                get_color='color',
                get_radius=50,
                pickable=True
            )
        ]
    ))

