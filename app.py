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

    # Ensure client_id is string
    for df in [bore_df, clients_df, survey_df]:
        if "client_id" in df.columns:
            df["client_id"] = df["client_id"].astype(str)

    # Merge boreholes and survey points with clients
    merged_df = clients_df.copy()
    merged_df = merged_df.merge(bore_df, on="client_id", how="left", suffixes=("", "_bore"))
    merged_df = merged_df.merge(survey_df, on="client_id", how="left", suffixes=("", "_survey"))

    # Convert coordinates to numeric
    for col in ["latitude", "longitude", "latitude_survey_points", "longitude_survey_points"]:
        if col in merged_df.columns:
            merged_df[col] = pd.to_numeric(merged_df[col], errors="coerce")

    return merged_df

# -------------------------
# Load data
# -------------------------
st.title("💧 Powerhaven Boreholes & Survey Dashboard")

with st.spinner("Loading data from Supabase..."):
    df = load_data()

if df.empty:
    st.error("No data loaded.")
    st.stop()

# -------------------------
# Client Filter
# -------------------------
client_options = df["client_name"].dropna().unique().tolist()
selected_client = st.selectbox("Select Client", options=client_options)
filtered_df = df[df["client_name"] == selected_client]

st.subheader(f"📊 Data for {selected_client}")
st.dataframe(filtered_df)

# -------------------------
# Prepare Map Data
# -------------------------
bore_df = filtered_df.dropna(subset=["latitude", "longitude"]).copy()
bore_df["type"] = "borehole"

survey_df = filtered_df.dropna(subset=["latitude_survey_points", "longitude_survey_points"]).copy()
survey_df["type"] = "survey"
survey_df.rename(columns={"latitude_survey_points":"latitude", "longitude_survey_points":"longitude"}, inplace=True)

# Combine and check for overlaps
combined_df = pd.concat([bore_df[["latitude","longitude","type"]], survey_df[["latitude","longitude","type"]]], ignore_index=True)

# Mark overlap points
def mark_overlap(row):
    matching = bore_df[(bore_df["latitude"] == row["latitude"]) & (bore_df["longitude"] == row["longitude"])]
    if not matching.empty and row["type"]=="survey":
        return "both"
    return row["type"]

combined_df["type"] = combined_df.apply(mark_overlap, axis=1)

# Assign colors
color_map = {
    "borehole": [255, 0, 0],      # Red
    "survey": [0, 0, 255],        # Blue
    "both": [128, 0, 128]         # Purple
}
combined_df["color"] = combined_df["type"].map(color_map)

# -------------------------
# Pydeck Map
# -------------------------
if not combined_df.empty:
    st.subheader("📍 Borehole & Survey Locations Map")

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=combined_df,
        get_position='[longitude, latitude]',
        get_color='color',
        get_radius=50,
        pickable=True
    )

    tooltip = {"html": "<b>Type:</b> {type} <br/> <b>Lat:</b> {latitude} <br/> <b>Lon:</b> {longitude}", "style": {"color": "white"}}

    view_state = pdk.ViewState(
        latitude=combined_df["latitude"].mean(),
        longitude=combined_df["longitude"].mean(),
        zoom=12,
        pitch=0
    )

    r = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip=tooltip
    )

    st.pydeck_chart(r)
else:
    st.info("No coordinates to display on the map.")

