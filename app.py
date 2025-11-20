import streamlit as st
import pandas as pd
from supabase import create_client, Client
import pydeck as pdk

# -------------------------
# Streamlit Page Settings
# -------------------------
st.set_page_config(page_title="Powerhaven Boreholes Dashboard", layout="wide")

# -------------------------
# Supabase Connection
# -------------------------
url = "https://mhcsryyqvhyntzrbdyuc.supabase.co"
key = st.secrets["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1oY3NyeXlxdmh5bnR6cmJkeXVjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjE4MDM1NTcsImV4cCI6MjA3NzM3OTU1N30.7aa5wtN-1XQbVsOchmsSyRe2CcpYDzPyBMPG59zsrOI"]  # You MUST add SUPABASE_KEY to secrets
supabase: Client = create_client(url, key)

# -------------------------
# Load Data From Supabase
# -------------------------
@st.cache_data
def load_data():
    bore_df = pd.DataFrame(supabase.table("boreholes").select("*").execute().data)
    clients_df = pd.DataFrame(supabase.table("clients").select("*").execute().data)
    survey_df = pd.DataFrame(supabase.table("survey_points").select("*").execute().data)
    siting_df = pd.DataFrame(supabase.table("siting_reports").select("*").execute().data)
    drilling_df = pd.DataFrame(supabase.table("drilling_reports").select("*").execute().data)

    # Convert client_id to string for consistent merging
    for df in [bore_df, clients_df, survey_df, siting_df, drilling_df]:
        if "client_id" in df.columns:
            df["client_id"] = df["client_id"].astype(str)

    # Start merging from clients
    merged = clients_df.copy()

    merged = merged.merge(bore_df, on="client_id", how="left")
    merged = merged.merge(survey_df, on="client_id", how="left", suffixes=("", "_survey"))
    merged = merged.merge(siting_df, on="client_id", how="left")
    merged = merged.merge(drilling_df, on="client_id", how="left")

    # Normalize column names that might be inconsistent
    if "Longitude" in merged.columns:  # Capital L case
        merged["longitude_survey_points"] = merged["Longitude"]

    if "latitude_survey_points" not in merged.columns and "latitude" in survey_df.columns:
        merged["latitude_survey_points"] = merged["latitude"]

    return merged


# -------------------------
# Load the Data
# -------------------------
st.title("💧 Powerhaven Boreholes & Solar Dashboard")

with st.spinner("Loading database..."):
    df = load_data()

if df.empty:
    st.error("No data found.")
    st.stop()

# -------------------------
# Client Selector
# -------------------------
client_options = df["client_name"].dropna().unique().tolist()
selected = st.selectbox("Select Client", client_options)

filtered = df[df["client_name"] == selected]

st.subheader(f"📊 Data for {selected}")
st.dataframe(filtered)

# -------------------------
# Build Map Data
# -------------------------

map_df = filtered.copy()

# Create unified map_lat/map_lon fields
map_df["map_lat"] = map_df["latitude"].combine_first(map_df["latitude_survey_points"])
map_df["map_lon"] = map_df["longitude"].combine_first(map_df["longitude_survey_points"])

map_df = map_df.dropna(subset=["map_lat", "map_lon"])

# -------------------------
# DISPLAY MAP
# -------------------------
if not map_df.empty:
    st.subheader(f"📍 Locations for {selected}")

    # Load Mapbox token
    mapbox_token = st.secrets["MAPBOX_API_KEY"]

    st.pydeck_chart(pdk.Deck(
        map_style='mapbox://styles/mapbox/light-v10',
        mapbox_key=mapbox_token,
        initial_view_state=pdk.ViewState(
            latitude=map_df["map_lat"].mean(),
            longitude=map_df["map_lon"].mean(),
            zoom=13,
            pitch=0,
        ),
        layers=[
            pdk.Layer(
                "ScatterplotLayer",
                data=map_df,
                get_position='[map_lon, map_lat]',
                get_color='[200, 30, 0, 160]',
                get_radius=80,
                pickable=True
            )
        ]
    ))

else:
    st.info("No location data found for this client.")

