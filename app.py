import os

import folium
import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_folium import st_folium
from supabase import create_client


st.set_page_config(page_title="Borehole Dashboard", layout="wide")

st.title("Borehole Drilling Dashboard")


def get_secret(name: str, default: str | None = None) -> str | None:
    """Read a value from Streamlit secrets first, then environment variables."""
    try:
        return st.secrets[name]
    except (KeyError, FileNotFoundError):
        return os.getenv(name, default)


@st.cache_data(ttl=300)
def load_boreholes() -> pd.DataFrame:
    supabase_url = get_secret("https://ewybimordizxtbxtughj.supabase.co")
    supabase_key = get_secret("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV3eWJpbW9yZGl6eHRieHR1Z2hqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc5NjcwNzYsImV4cCI6MjA5MzU0MzA3Nn0.FBETeNXLGcp_0H3-lX2PTXJurbJENyAGQG12GuxTab0")

    if not supabase_url or not supabase_key:
        st.error(
            "Missing Supabase configuration. Add SUPABASE_URL and SUPABASE_KEY "
            "to .streamlit/secrets.toml or set them as environment variables."
        )
        st.stop()

    client = create_client(supabase_url, supabase_key)
    response = client.table("boreholes").select("*").execute()
    return pd.DataFrame(response.data)


df = load_boreholes()

required_columns = {
    "borehole_name",
    "district",
    "village",
    "yield_lph",
    "drilling_status",
    "latitude",
    "longitude",
}

missing_columns = sorted(required_columns.difference(df.columns))
if missing_columns:
    st.error(f"Missing expected database columns: {', '.join(missing_columns)}")
    st.stop()

st.sidebar.header("Search Boreholes")

search_name = st.sidebar.text_input("Search Borehole Name")

districts = sorted(df["district"].dropna().unique().tolist())
search_district = st.sidebar.selectbox("Select District", ["All"] + districts)

filtered_df = df.copy()

if search_name:
    filtered_df = filtered_df[
        filtered_df["borehole_name"].str.contains(search_name, case=False, na=False)
    ]

if search_district != "All":
    filtered_df = filtered_df[filtered_df["district"] == search_district]

successful = len(filtered_df[filtered_df["drilling_status"] == "Successful"])
failed = len(filtered_df[filtered_df["drilling_status"] == "Failed"])
total = len(filtered_df)

success_rate = round((successful / total) * 100, 2) if total else 0
failure_rate = round((failed / total) * 100, 2) if total else 0

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Total", total)
col2.metric("Successful", successful)
col3.metric("Failed", failed)
col4.metric("Success Rate", f"{success_rate}%")
col5.metric("Failure Rate", f"{failure_rate}%")

chart_df = pd.DataFrame(
    {
        "Status": ["Successful", "Failed"],
        "Count": [successful, failed],
    }
)

fig = px.pie(
    chart_df,
    values="Count",
    names="Status",
    title="Borehole Success vs Failure",
    color="Status",
    color_discrete_map={"Successful": "#2e7d32", "Failed": "#c62828"},
)

st.plotly_chart(fig, use_container_width=True)

st.subheader("Borehole Records")
st.dataframe(filtered_df, use_container_width=True)

st.subheader("Borehole Locations")

map_df = filtered_df.dropna(subset=["latitude", "longitude"])

if map_df.empty:
    st.info("No boreholes with latitude and longitude are available for this filter.")
else:
    center_lat = map_df["latitude"].astype(float).mean()
    center_lon = map_df["longitude"].astype(float).mean()
    m = folium.Map(location=[center_lat, center_lon], zoom_start=7)

    for _, row in map_df.iterrows():
        marker_color = "red" if row["drilling_status"] == "Failed" else "green"

        popup = f"""
        <b>Borehole:</b> {row['borehole_name']}<br>
        <b>District:</b> {row['district']}<br>
        <b>Village:</b> {row['village']}<br>
        <b>Yield:</b> {row['yield_lph']} LPH<br>
        <b>Status:</b> {row['drilling_status']}
        """

        folium.Marker(
            location=[float(row["latitude"]), float(row["longitude"])],
            popup=popup,
            icon=folium.Icon(color=marker_color),
        ).add_to(m)

    st_folium(m, width=None, height=600)
import os

import folium
import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_folium import st_folium
from supabase import create_client


st.set_page_config(page_title="Borehole Dashboard", layout="wide")

st.title("Borehole Drilling Dashboard")


def get_secret(name: str, default: str | None = None) -> str | None:
    """Read a value from Streamlit secrets first, then environment variables."""
    try:
        return st.secrets[name]
    except (KeyError, FileNotFoundError):
        return os.getenv(name, default)


@st.cache_data(ttl=300)
def load_boreholes() -> pd.DataFrame:
    supabase_url = get_secret("SUPABASE_URL")
    supabase_key = get_secret("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        st.error(
            "Missing Supabase configuration. Add SUPABASE_URL and SUPABASE_KEY "
            "to .streamlit/secrets.toml or set them as environment variables."
        )
        st.stop()

    client = create_client(supabase_url, supabase_key)
    response = client.table("boreholes").select("*").execute()
    return pd.DataFrame(response.data)


df = load_boreholes()

required_columns = {
    "borehole_name",
    "district",
    "village",
    "yield_lph",
    "drilling_status",
    "latitude",
    "longitude",
}

missing_columns = sorted(required_columns.difference(df.columns))
if missing_columns:
    st.error(f"Missing expected database columns: {', '.join(missing_columns)}")
    st.stop()

st.sidebar.header("Search Boreholes")

search_name = st.sidebar.text_input("Search Borehole Name")

districts = sorted(df["district"].dropna().unique().tolist())
search_district = st.sidebar.selectbox("Select District", ["All"] + districts)

filtered_df = df.copy()

if search_name:
    filtered_df = filtered_df[
        filtered_df["borehole_name"].str.contains(search_name, case=False, na=False)
    ]

if search_district != "All":
    filtered_df = filtered_df[filtered_df["district"] == search_district]

successful = len(filtered_df[filtered_df["drilling_status"] == "Successful"])
failed = len(filtered_df[filtered_df["drilling_status"] == "Failed"])
total = len(filtered_df)

success_rate = round((successful / total) * 100, 2) if total else 0
failure_rate = round((failed / total) * 100, 2) if total else 0

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Total", total)
col2.metric("Successful", successful)
col3.metric("Failed", failed)
col4.metric("Success Rate", f"{success_rate}%")
col5.metric("Failure Rate", f"{failure_rate}%")

chart_df = pd.DataFrame(
    {
        "Status": ["Successful", "Failed"],
        "Count": [successful, failed],
    }
)

fig = px.pie(
    chart_df,
    values="Count",
    names="Status",
    title="Borehole Success vs Failure",
    color="Status",
    color_discrete_map={"Successful": "#2e7d32", "Failed": "#c62828"},
)

st.plotly_chart(fig, use_container_width=True)

st.subheader("Borehole Records")
st.dataframe(filtered_df, use_container_width=True)

st.subheader("Borehole Locations")

map_df = filtered_df.dropna(subset=["latitude", "longitude"])

if map_df.empty:
    st.info("No boreholes with latitude and longitude are available for this filter.")
else:
    center_lat = map_df["latitude"].astype(float).mean()
    center_lon = map_df["longitude"].astype(float).mean()
    m = folium.Map(location=[center_lat, center_lon], zoom_start=7)

    for _, row in map_df.iterrows():
        marker_color = "red" if row["drilling_status"] == "Failed" else "green"

        popup = f"""
        <b>Borehole:</b> {row['borehole_name']}<br>
        <b>District:</b> {row['district']}<br>
        <b>Village:</b> {row['village']}<br>
        <b>Yield:</b> {row['yield_lph']} LPH<br>
        <b>Status:</b> {row['drilling_status']}
        """

        folium.Marker(
            location=[float(row["latitude"]), float(row["longitude"])],
            popup=popup,
            icon=folium.Icon(color=marker_color),
        ).add_to(m)

    st_folium(m, width=None, height=600)
