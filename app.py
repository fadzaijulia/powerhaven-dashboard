import streamlit as st
import pandas as pd
from supabase import create_client, Client
import pydeck as pdk

# --- Supabase connection ---
url = "https://mhcsryyqvhyntzrbdyuc.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1oY3NyeXlxdmh5bnR6cmJkeXVjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjE4MDM1NTcsImV4cCI6MjA3NzM3OTU1N30.7aa5wtN-1XQbVsOchmsSyRe2CcpYDzPyBMPG59zsrOI"  # Replace with your anon key
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Powerhaven Boreholes Dashboard", layout="wide")

# ============================
# 🔹 LOAD DATA FUNCTION
# ============================
def load_data():
    # Load tables
    try:
        clients_df = pd.DataFrame(supabase.table("clients").select("*").execute().data)
        boreholes_df = pd.DataFrame(supabase.table("boreholes").select("*").execute().data)
        survey_df = pd.DataFrame(supabase.table("survey_points").select("*").execute().data)
    except Exception as e:
        st.error(f"Error loading data from Supabase: {e}")
        return pd.DataFrame()

    # Ensure client_id is string
    for df in [clients_df, boreholes_df, survey_df]:
        if "client_id" in df.columns:
            df["client_id"] = df["client_id"].astype(str)

    # Merge tables on client_id
    merged_df = clients_df.copy()
    merged_df = merged_df.merge(boreholes_df, on="client_id", how="left", suffixes=("", "_bore"))
    merged_df = merged_df.merge(survey_df, on="client_id", how="left", suffixes=("", "_survey"))

    # Ensure coordinates are numeric
    for col in ["latitude", "longitude", "latitude_survey_points", "longitude_survey_points"]:
        if col in merged_df.columns:
            merged_df[col] = pd.to_numeric(merged_df[col], errors="coerce")

    return merged_df

# ============================
# 🔹 LOAD DATA
# ============================
st.title("💧 Powerhaven Boreholes & Survey Dashboard")

with st.spinner("Loading data from Supabase..."):
    df = load_data()

if df.empty:
    st.error("No data loaded.")
    st.stop()

# ============================
# 🔹 CLIENT FILTER
# ============================
client_options = df["client_name"].dropna().unique().tolist()
selected_client = st.selectbox("Select Client to view data", options=client_options)
filtered_df = df[df["client_name"] == selected_client]

st.subheader(f"📊 Data for {selected_client}")
st.dataframe(filtered_df)

# ============================
# 🔹 MAP
# ============================
# Combine coordinates: borehole first, then survey
map_df = filtered_df.copy()
map_df["map_lat"] = map_df["latitude"].combine_first(map_df["latitude_survey_points"])
map_df["map_lon"] = map_df["longitude"].combine_first(map_df["longitude_survey_points"])
map_df = map_df.dropna(subset=["map_lat", "map_lon"])

# If no valid coordinates, show a test point
if map_df.empty:
    map_df = pd.DataFrame({
        "map_lat": [-17.8277],
        "map_lon": [31.0530],
        "color": [[0,128,255,160]],
        "client_name": ["Test Client"]
    })
else:
    map_df["color"] = [[0,128,255,160]]*len(map_df)

st.subheader("📍 Borehole & Survey Locations")

st.pydeck_chart(pdk.Deck(
    map_style='mapbox://styles/mapbox/light-v9',
    initial_view_state=pdk.ViewState(
        latitude=map_df["map_lat"].mean(),
        longitude=map_df["map_lon"].mean(),
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
