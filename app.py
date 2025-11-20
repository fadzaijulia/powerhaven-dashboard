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

    # Merge boreholes with clients
    merged_bore = clients_df.merge(bore_df, on="client_id", how="left")
    merged_survey = clients_df.merge(survey_df, on="client_id", how="left")

    # Ensure numeric
    for df, lat_col, lon_col in [
        (merged_bore, "latitude", "longitude"),
        (merged_survey, "latitude", "longitude")
    ]:
        df[lat_col] = pd.to_numeric(df[lat_col], errors="coerce")
        df[lon_col] = pd.to_numeric(df[lon_col], errors="coerce")

    return merged_bore, merged_survey, clients_df

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
survey_filtered = survey_df[survey_df["client_name"] == selected_client].dropna(subset=["latitude","longitude"])

st.subheader(f"📊 Data for {selected_client}")
st.dataframe(pd.concat([bore_filtered, survey_filtered], ignore_index=True, sort=False))

# -------------------------
# Prepare Map Data
# -------------------------
# Add a type column for coloring
bore_filtered = bore_filtered.copy()
bore_filtered["type"] = "Borehole"

survey_filtered = survey_filtered.copy()
survey_filtered["type"] = "Survey"

# Merge bore and survey to find overlaps
merged = pd.concat([bore_filtered, survey_filtered], ignore_index=True)
merged["color"] = merged.apply(
    lambda row: [0, 200, 0] if row["type"]=="Survey" else [200, 0, 0], axis=1
)

# Highlight overlapping points (same lat/lon)
overlap = pd.merge(
    bore_filtered[["latitude","longitude"]],
    survey_filtered[["latitude","longitude"]],
    on=["latitude","longitude"]
)
if not overlap.empty:
    merged.loc[
        merged.apply(lambda row: ((row["latitude"],row["longitude"]) in list(zip(overlap["latitude"],overlap["longitude"]))), axis=1),
        "color"
    ] = [0,0,200]  # Blue for overlapping points

# -------------------------
# PyDeck Map
# -------------------------
if not merged.empty:
    st.subheader(f"📍 Borehole & Survey Locations for {selected_client}")
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=merged,
        get_position='[longitude, latitude]',
        get_fill_color='color',
        get_radius=50,
        pickable=True,
        auto_highlight=True
    )

    tooltip = {
        "html": "<b>Type:</b> {type} <br/> <b>Lat:</b> {latitude} <br/> <b>Lon:</b> {longitude}",
        "style": {"color": "white"}
    }

    st.pydeck_chart(pdk.Deck(
        map_style='mapbox://styles/mapbox/light-v9',
        initial_view_state=pdk.ViewState(
            latitude=merged["latitude"].mean(),
            longitude=merged["longitude"].mean(),
            zoom=12,
            pitch=0,
        ),
        layers=[layer],
        tooltip=tooltip
    ))
else:
    st.info("No location data available for this client.")

