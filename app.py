import streamlit as st
import pandas as pd
from supabase import create_client, Client
import pydeck as pdk

# --- Supabase connection ---
url = "https://mhcsryyqvhyntzrbdyuc.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1oY3NyeXlxdmh5bnR6cmJkeXVjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjE4MDM1NTcsImV4cCI6MjA3NzM3OTU1N30.7aa5wtN-1XQbVsOchmsSyRe2CcpYDzPyBMPG59zsrOI"
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Powerhaven Boreholes Dashboard", layout="wide")

# ============================
# 🔹 LOAD DATA FUNCTION
# ============================
def load_data():
    # Load all tables
    bore_df = pd.DataFrame(supabase.table("boreholes").select("*").execute().data)
    clients_df = pd.DataFrame(supabase.table("clients").select("*").execute().data)
    survey_df = pd.DataFrame(supabase.table("survey_points").select("*").execute().data)
    siting_df = pd.DataFrame(supabase.table("siting_reports").select("*").execute().data)
    drilling_df = pd.DataFrame(supabase.table("drilling_reports").select("*").execute().data)

    # Ensure client_id is string for safe merging
    for df in [bore_df, clients_df, survey_df, siting_df, drilling_df]:
        if "client_id" in df.columns:
            df["client_id"] = df["client_id"].astype(str)

    # Start merging with clients table
    merged_df = clients_df.copy()

    if "client_id" in bore_df.columns:
        merged_df = merged_df.merge(bore_df, on="client_id", how="left", suffixes=("", "_bore"))
    if "client_id" in survey_df.columns:
        merged_df = merged_df.merge(survey_df, on="client_id", how="left", suffixes=("", "_survey"))
    if "client_id" in siting_df.columns:
        merged_df = merged_df.merge(siting_df, on="client_id", how="left", suffixes=("", "_siting"))
    if "client_id" in drilling_df.columns:
        merged_df = merged_df.merge(drilling_df, on="client_id", how="left", suffixes=("", "_drill"))

    # Ensure latitude and longitude are numeric
    for col in ["latitude", "longitude"]:
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
map_df = df.dropna(subset=["latitude", "longitude"])

if not map_df.empty:
    st.subheader("📍 Borehole / Survey Locations for All Clients")
    # Assign each client a unique color
    unique_clients = map_df["client_name"].dropna().unique().tolist()
    color_map = {name: [int(hash(name) % 256), (int(hash(name)*7) % 256), (int(hash(name)*13) % 256), 160] for name in unique_clients}
    map_df["color"] = map_df["client_name"].map(color_map)

    st.pydeck_chart(pdk.Deck(
        map_style='mapbox://styles/mapbox/light-v9',
        initial_view_state=pdk.ViewState(
            latitude=map_df["latitude"].mean(),
            longitude=map_df["longitude"].mean(),
            zoom=10,
            pitch=0,
        ),
        layers=[
            pdk.Layer(
                "ScatterplotLayer",
                data=map_df,
                get_position='[longitude, latitude]',
                get_color='color',
                get_radius=50,
                pickable=True
            )
        ]
    ))
else:
    st.info("No location data available to display on the map.")

