import streamlit as st
import pandas as pd
from supabase import create_client, Client
import pydeck as pdk

# -------------------------
# Supabase connection
# -------------------------
url = "https://mhcsryyqvhyntzrbdyuc.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1oY3NyeXlxdmh5bnR6cmJkeXVjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjE4MDM1NTcsImV4cCI6MjA3NzM3OTU1N30.7aa5wtN-1XQbVsOchmsSyRe2CcpYDzPyBMPG59zsrOI"
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Powerhaven Boreholes Dashboard", layout="wide")

# -------------------------
# Load Data
# -------------------------
@st.cache_data
def load_data():
    bore_df = pd.DataFrame(supabase.table("boreholes").select("*").execute().data)
    clients_df = pd.DataFrame(supabase.table("clients").select("*").execute().data)
    survey_df = pd.DataFrame(supabase.table("survey_points").select("*").execute().data)

    # Convert client_id to string
    for df in [bore_df, clients_df, survey_df]:
        if "client_id" in df.columns:
            df["client_id"] = df["client_id"].astype(str)

    # Merge with clients
    bore_df = clients_df.merge(bore_df, on="client_id", how="left")
    survey_df = clients_df.merge(survey_df, on="client_id", how="left")

    # Ensure numeric columns
    if "latitude" in bore_df.columns and "longitude" in bore_df.columns:
        bore_df["latitude"] = pd.to_numeric(bore_df["latitude"], errors="coerce")
        bore_df["longitude"] = pd.to_numeric(bore_df["longitude"], errors="coerce")

    if "latitude_survey_points" in survey_df.columns and "longitude_survey_points" in survey_df.columns:
        survey_df["latitude_survey_points"] = pd.to_numeric(survey_df["latitude_survey_points"], errors="coerce")
        survey_df["longitude_survey_points"] = pd.to_numeric(survey_df["longitude_survey_points"], errors="coerce")

    return bore_df, survey_df, clients_df

# -------------------------
# Load Data
# -------------------------
st.title("💧 Powerhaven Boreholes & Survey Dashboard")
with st.spinner("Loading data from Supabase..."):
    bore_df, survey_df, clients_df = load_data()

# -------------------------
# Client Filter
# -------------------------
client_options = clients_df["client_name"].dropna().unique().tolist()
selected_client = st.selectbox("Select Client", options=client_options)

bore_filtered = bore_df[bore_df["client_name"] == selected_client].dropna(subset=["latitude","longitude"])
survey_filtered = survey_df[survey_df["client_name"] == selected_client].dropna(subset=["latitude_survey_points","longitude_survey_points"])

st.subheader(f"📊 Data for {selected_client}")
st.dataframe(pd.concat([bore_filtered, survey_filtered], ignore_index=True, sort=False))

# -------------------------
# Prepare Map Data
# -------------------------
# Boreholes
bore_filtered = bore_filtered.copy()
bore_filtered["type"] = "Borehole"
bore_filtered["lat"] = bore_filtered["latitude"]
bore_filtered["lon"] = bore_filtered["longitude"]
bore_filtered["color"] = [200,0,0]  # Red

# Survey points
survey_filtered = survey_filtered.copy()
survey_filtered["type"] = "Survey"
survey_filtered["lat"] = survey_filtered["latitude_survey_points"]
survey_filtered["lon"] = survey_filtered["longitude_survey_points"]
survey_filtered["color"] = [0,200,0]  # Green

# Combine
map_df = pd.concat([bore_filtered, survey_filtered], ignore_index=True)

# Highlight overlapping points (same lat/lon)
overlap = pd.merge(
    bore_filtered[["lat","lon"]],
    survey_filtered[["lat","lon"]],
    on=["lat","lon"]
)
if not overlap.empty:
    for idx, row in overlap.iterrows():
        map_df.loc[(map_df["lat"]==row["lat"]) & (map_df["lon"]==row["lon"]), "color"] = [0,0,200]  # Blue

# -------------------------
# PyDeck Map
# -------------------------
if not map_df.empty:
    st.subheader(f"📍 Borehole & Survey Locations for {selected_client}")
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_df,
        get_position='[lon, lat]',
        get_fill_color='color',
        get_radius=50,
        pickable=True,
        auto_highlight=True
    )

    tooltip = {
        "html": "<b>Type:</b> {type} <br/> <b>Lat:</b> {lat} <br/> <b>Lon:</b> {lon}",
        "style": {"color": "white"}
    }

    st.pydeck_chart(pdk.Deck(
        map_style='mapbox://styles/mapbox/light-v9',
        initial_view_state=pdk.ViewState(
            latitude=map_df["lat"].mean(),
            longitude=map_df["lon"].mean(),
            zoom=12,
            pitch=0,
        ),
        layers=[layer],
        tooltip=tooltip
    ))
else:
    st.info("No location data available for this client.")

