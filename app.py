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
selected_client = st.selectb_
