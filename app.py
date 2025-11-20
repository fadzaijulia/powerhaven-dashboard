import streamlit as st
import pandas as pd
from supabase import create_client, Client

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
    # Load tables
    bore_df = pd.DataFrame(supabase.table("boreholes").select("*").execute().data)
    clients_df = pd.DataFrame(supabase.table("clients").select("*").execute().data)
    survey_df = pd.DataFrame(supabase.table("survey_points").select("*").execute().data)
    siting_df = pd.DataFrame(supabase.table("siting_reports").select("*").execute().data)
    drilling_df = pd.DataFrame(supabase.table("drilling_reports").select("*").execute().data)

    # Convert client_id to string for merging
    for df in [bore_df, clients_df, survey_df, siting_df, drilling_df]:
        if "client_id" in df.columns:
            df["client_id"] = df["client_id"].astype(str)

    # Start merge with clients
    merged_df = clients_df.copy()

    if "client_id" in bore_df.columns:
        merged_df = merged_df.merge(bore_df, on="client_id", how="left", suffixes=("", "_bore"))
    if "client_id" in survey_df.columns:
        merged_df = merged_df.merge(survey_df, on="client_id", how="left", suffixes=("", "_survey"))
    if "client_id" in siting_df.columns:
        merged_df = merged_df.merge(siting_df, on="client_id", how="left", suffixes=("", "_siting"))
    if "client_id" in drilling_df.columns:
        merged_df = merged_df.merge(drilling_df, on="client_id", how="left", suffixes=("", "_drill"))

    # -------------------------
    # Use actual latitude/longitude columns (new ones in Supabase)
    # -------------------------
    # Borehole
    if "latitude" in merged_df.columns and "longitude" in merged_df.columns:
        merged_df["latitude"] = pd.to_numeric(merged_df["latitude"], errors="coerce")
        merged_df["longitude"] = pd.to_numeric(merged_df["longitude"], errors="coerce")

    # Survey points
    if "latitude_survey_points" in merged_df.columns and "longitude_survey_points" in merged_df.columns:
        merged_df["latitude"] = merged_df["latitude"].combine_first(merged_df["latitude_survey_points"])
        merged_df["longitude"] = merged_df["longitude"].combine_first(merged_df["longitude_survey_points"])

    return merged_df

# -------------------------
# Load Data
# -------------------------
st.title("💧 Powerhaven Boreholes & Solar Dashboard")

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
# Map Section (FREE: st.map)
# -------------------------
map_df = filtered_df.dropna(subset=["latitude", "longitude"])

if not map_df.empty:
    st.subheader(f"📍 Borehole / Survey Locations for {selected_client}")
    st.map(map_df[["latitude", "longitude"]])
else:
    st.info("No location data available for this client to display on the map.")
