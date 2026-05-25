import os
from datetime import date

import folium
import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_folium import st_folium
from supabase import create_client


st.set_page_config(page_title="Powerhaven Borehole WebGIS", layout="wide")

TABLES = [
    "clients",
    "survey_points",
    "siting_reports",
    "boreholes",
    "drilling_reports",
]


def read_secret(name: str) -> str | None:
    try:
        return st.secrets[name]
    except (KeyError, FileNotFoundError):
        return os.getenv(name)


def first_existing(df: pd.DataFrame, names: list[str]) -> str | None:
    for name in names:
        if name in df.columns:
            return name
    return None


def demo_data() -> dict[str, pd.DataFrame]:
    clients = pd.DataFrame(
        [
            {
                "client_id": 1,
                "client_name": "Tariro Moyo",
                "phone": "+263 77 000 001",
                "address": "Murewa",
                "district": "Murewa",
            },
            {
                "client_id": 2,
                "client_name": "Nyasha Dube",
                "phone": "+263 77 000 002",
                "address": "Gwanda",
                "district": "Gwanda",
            },
            {
                "client_id": 3,
                "client_name": "Powerhaven Projects",
                "phone": "+263 77 000 003",
                "address": "Belvedere, Harare",
                "district": "Harare",
            },
        ]
    )

    boreholes = pd.DataFrame(
        [
            {
                "borehole_id": 1,
                "client_id": 1,
                "survey_id": 1,
                "borehole_name": "Murewa BH-01",
                "district": "Murewa",
                "village": "Chitowa",
                "latitude": -17.6468,
                "longitude": 31.7847,
                "yield_lph": 2200,
                "drilling_status": "Successful",
                "drilling_date": "2025-06-12",
            },
            {
                "borehole_id": 2,
                "client_id": 2,
                "survey_id": 2,
                "borehole_name": "Gwanda BH-04",
                "district": "Gwanda",
                "village": "Ntalale",
                "latitude": -20.9362,
                "longitude": 29.0069,
                "yield_lph": 0,
                "drilling_status": "Failed",
                "drilling_date": "2025-08-03",
            },
            {
                "borehole_id": 3,
                "client_id": 3,
                "survey_id": 3,
                "borehole_name": "Harare BH-07",
                "district": "Harare",
                "village": "Belvedere",
                "latitude": -17.8252,
                "longitude": 31.0335,
                "yield_lph": 3500,
                "drilling_status": "Successful",
                "drilling_date": "2025-09-18",
            },
        ]
    )

    survey_points = pd.DataFrame(
        [
            {"survey_id": 1, "client_id": 1, "latitude": -17.6468, "longitude": 31.7847, "site_condition": "Granite"},
            {"survey_id": 2, "client_id": 2, "latitude": -20.9362, "longitude": 29.0069, "site_condition": "Dry fractured zone"},
            {"survey_id": 3, "client_id": 3, "latitude": -17.8252, "longitude": 31.0335, "site_condition": "Dolerite contact"},
        ]
    )

    siting_reports = pd.DataFrame(
        [
            {"report_id": 1, "client_id": 1, "survey_id": 1, "report_date": "2025-06-01", "recommendation": "Proceed"},
            {"report_id": 2, "client_id": 2, "survey_id": 2, "report_date": "2025-07-25", "recommendation": "High risk"},
            {"report_id": 3, "client_id": 3, "survey_id": 3, "report_date": "2025-09-10", "recommendation": "Proceed"},
        ]
    )

    drilling_reports = pd.DataFrame(
        [
            {"report_id": 1, "client_id": 1, "borehole_id": 1, "depth_m": 65, "water_strike_m": 42, "report_url": ""},
            {"report_id": 2, "client_id": 2, "borehole_id": 2, "depth_m": 80, "water_strike_m": None, "report_url": ""},
            {"report_id": 3, "client_id": 3, "borehole_id": 3, "depth_m": 55, "water_strike_m": 38, "report_url": ""},
        ]
    )

    return {
        "clients": clients,
        "survey_points": survey_points,
        "siting_reports": siting_reports,
        "boreholes": boreholes,
        "drilling_reports": drilling_reports,
    }


@st.cache_resource
def get_supabase_client():
    supabase_url = read_secret("SUPABASE_URL")
    supabase_key = read_secret("SUPABASE_KEY")
    if not supabase_url or not supabase_key:
        return None
    return create_client(supabase_url, supabase_key)


@st.cache_data(ttl=300)
def load_table(table_name: str, configured: bool) -> pd.DataFrame:
    if not configured:
        return demo_data()[table_name]

    client = get_supabase_client()
    response = client.table(table_name).select("*").execute()
    return pd.DataFrame(response.data)


def load_data() -> tuple[dict[str, pd.DataFrame], bool]:
    configured = get_supabase_client() is not None
    data = {}
    for table_name in TABLES:
        try:
            data[table_name] = load_table(table_name, configured)
        except Exception as exc:
            st.warning(f"Could not load `{table_name}` from Supabase: {exc}")
            data[table_name] = pd.DataFrame()
    return data, configured


def apply_filters(boreholes: pd.DataFrame) -> pd.DataFrame:
    filtered = boreholes.copy()

    st.sidebar.header("Search and Filter")
    search_text = st.sidebar.text_input("Search records")

    district_col = first_existing(filtered, ["district"])
    status_col = first_existing(filtered, ["drilling_status", "status"])

    if district_col:
        districts = sorted(filtered[district_col].dropna().astype(str).unique().tolist())
        selected_district = st.sidebar.selectbox("District", ["All"] + districts)
        if selected_district != "All":
            filtered = filtered[filtered[district_col].astype(str) == selected_district]

    if status_col:
        statuses = sorted(filtered[status_col].dropna().astype(str).unique().tolist())
        selected_status = st.sidebar.selectbox("Drilling status", ["All"] + statuses)
        if selected_status != "All":
            filtered = filtered[filtered[status_col].astype(str) == selected_status]

    if search_text:
        text_columns = filtered.select_dtypes(include=["object", "string"]).columns
        mask = pd.Series(False, index=filtered.index)
        for column in text_columns:
            mask = mask | filtered[column].astype(str).str.contains(search_text, case=False, na=False)
        filtered = filtered[mask]

    return filtered


def status_counts(df: pd.DataFrame) -> tuple[int, int, int, float, float]:
    status_col = first_existing(df, ["drilling_status", "status"])
    total = len(df)
    if not status_col:
        return total, 0, 0, 0.0, 0.0

    statuses = df[status_col].fillna("").astype(str).str.lower()
    successful = statuses.eq("successful").sum()
    failed = statuses.eq("failed").sum()
    success_rate = round((successful / total) * 100, 2) if total else 0.0
    failure_rate = round((failed / total) * 100, 2) if total else 0.0
    return total, successful, failed, success_rate, failure_rate


def dashboard_tab(filtered: pd.DataFrame, reports: pd.DataFrame):
    total, successful, failed, success_rate, failure_rate = status_counts(filtered)
    yield_col = first_existing(filtered, ["yield_lph", "yield", "yield_litres_per_hour"])
    average_yield = round(pd.to_numeric(filtered[yield_col], errors="coerce").mean(), 2) if yield_col else 0

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Boreholes", total)
    col2.metric("Successful", successful)
    col3.metric("Failed", failed)
    col4.metric("Success Rate", f"{success_rate}%")
    col5.metric("Failure Rate", f"{failure_rate}%")
    col6.metric("Average Yield", f"{average_yield} LPH")

    left, right = st.columns(2)
    chart_df = pd.DataFrame({"Status": ["Successful", "Failed"], "Count": [successful, failed]})
    left.plotly_chart(
        px.pie(
            chart_df,
            values="Count",
            names="Status",
            title="Drilling Success vs Failure",
            color="Status",
            color_discrete_map={"Successful": "#2e7d32", "Failed": "#c62828"},
        ),
        use_container_width=True,
    )

    district_col = first_existing(filtered, ["district"])
    if district_col and yield_col:
        yield_by_district = (
            filtered.assign(**{yield_col: pd.to_numeric(filtered[yield_col], errors="coerce")})
            .groupby(district_col, as_index=False)[yield_col]
            .mean()
            .sort_values(yield_col, ascending=False)
        )
        right.plotly_chart(
            px.bar(yield_by_district, x=district_col, y=yield_col, title="Average Yield by District"),
            use_container_width=True,
        )
    else:
        right.info("Add district and yield columns to show yield analysis.")

    if not reports.empty:
        st.subheader("Drilling Reports")
        st.dataframe(reports, use_container_width=True, hide_index=True)


def map_tab(filtered: pd.DataFrame, survey_points: pd.DataFrame):
    lat_col = first_existing(filtered, ["latitude", "lat"])
    lon_col = first_existing(filtered, ["longitude", "lon", "lng"])

    if not lat_col or not lon_col:
        st.info("Add latitude and longitude fields to display the borehole map.")
        return

    map_df = filtered.copy()
    map_df[lat_col] = pd.to_numeric(map_df[lat_col], errors="coerce")
    map_df[lon_col] = pd.to_numeric(map_df[lon_col], errors="coerce")
    map_df = map_df.dropna(subset=[lat_col, lon_col])

    if map_df.empty:
        st.info("No mapped boreholes match the current filters.")
        return

    m = folium.Map(location=[map_df[lat_col].mean(), map_df[lon_col].mean()], zoom_start=7, tiles="OpenStreetMap")
    folium.TileLayer("CartoDB positron", name="Light basemap").add_to(m)
    folium.TileLayer("CartoDB dark_matter", name="Dark basemap").add_to(m)

    name_col = first_existing(map_df, ["borehole_name", "name"])
    district_col = first_existing(map_df, ["district"])
    village_col = first_existing(map_df, ["village"])
    yield_col = first_existing(map_df, ["yield_lph", "yield", "yield_litres_per_hour"])
    status_col = first_existing(map_df, ["drilling_status", "status"])

    for _, row in map_df.iterrows():
        status = str(row.get(status_col, "")) if status_col else ""
        color = "red" if status.lower() == "failed" else "green"
        popup = f"""
        <b>Borehole:</b> {row.get(name_col, "Unknown") if name_col else "Unknown"}<br>
        <b>District:</b> {row.get(district_col, "") if district_col else ""}<br>
        <b>Village:</b> {row.get(village_col, "") if village_col else ""}<br>
        <b>Yield:</b> {row.get(yield_col, "") if yield_col else ""} LPH<br>
        <b>Status:</b> {status}
        """
        folium.Marker(
            location=[row[lat_col], row[lon_col]],
            popup=popup,
            tooltip=row.get(name_col, "Borehole") if name_col else "Borehole",
            icon=folium.Icon(color=color, icon="tint", prefix="fa"),
        ).add_to(m)

    if not survey_points.empty:
        survey_lat = first_existing(survey_points, ["latitude", "lat"])
        survey_lon = first_existing(survey_points, ["longitude", "lon", "lng"])
        if survey_lat and survey_lon:
            survey_layer = folium.FeatureGroup(name="Survey points")
            for _, row in survey_points.dropna(subset=[survey_lat, survey_lon]).iterrows():
                folium.CircleMarker(
                    location=[float(row[survey_lat]), float(row[survey_lon])],
                    radius=5,
                    color="#1565c0",
                    fill=True,
                    fill_opacity=0.7,
                    popup="Survey point",
                ).add_to(survey_layer)
            survey_layer.add_to(m)

    folium.LayerControl().add_to(m)
    st_folium(m, height=650, use_container_width=True)


def records_tab(data: dict[str, pd.DataFrame], filtered: pd.DataFrame):
    st.subheader("Borehole Records")
    st.dataframe(filtered, use_container_width=True, hide_index=True)

    st.subheader("Related Geodatabase Tables")
    table_tabs = st.tabs(["Clients", "Survey Points", "Siting Reports", "Drilling Reports"])
    for tab, table_name in zip(table_tabs, ["clients", "survey_points", "siting_reports", "drilling_reports"]):
        with tab:
            df = data.get(table_name, pd.DataFrame())
            if df.empty:
                st.info(f"No records found in `{table_name}`.")
            else:
                st.dataframe(df, use_container_width=True, hide_index=True)


def data_entry_tab(configured: bool):
    if not configured:
        st.info("Configure Supabase secrets to enable live inserts. Demo mode is read-only.")
        return

    client = get_supabase_client()
    left, right = st.columns(2)

    with left:
        st.subheader("Add Client")
        with st.form("client_form", clear_on_submit=True):
            client_name = st.text_input("Client name")
            phone = st.text_input("Phone")
            address = st.text_area("Address")
            district = st.text_input("District")
            submitted = st.form_submit_button("Save Client")
            if submitted:
                client.table("clients").insert(
                    {
                        "client_name": client_name,
                        "phone": phone,
                        "address": address,
                        "district": district,
                    }
                ).execute()
                st.cache_data.clear()
                st.success("Client saved.")

    with right:
        st.subheader("Add Borehole")
        with st.form("borehole_form", clear_on_submit=True):
            borehole_name = st.text_input("Borehole name")
            client_id = st.number_input("Client ID", min_value=1, step=1)
            district = st.text_input("District", key="bh_district")
            village = st.text_input("Village")
            latitude = st.number_input("Latitude", format="%.6f")
            longitude = st.number_input("Longitude", format="%.6f")
            yield_lph = st.number_input("Yield LPH", min_value=0.0, step=100.0)
            drilling_status = st.selectbox("Status", ["Successful", "Failed", "Pending"])
            drilling_date = st.date_input("Drilling date", value=date.today())
            submitted = st.form_submit_button("Save Borehole")
            if submitted:
                client.table("boreholes").insert(
                    {
                        "borehole_name": borehole_name,
                        "client_id": int(client_id),
                        "district": district,
                        "village": village,
                        "latitude": latitude,
                        "longitude": longitude,
                        "yield_lph": yield_lph,
                        "drilling_status": drilling_status,
                        "drilling_date": drilling_date.isoformat(),
                    }
                ).execute()
                st.cache_data.clear()
                st.success("Borehole saved.")


def schema_tab():
    st.subheader("Project Geodatabase Design")
    st.markdown(
        """
        The project document describes five linked tables:

        - `clients`
        - `survey_points`
        - `siting_reports`
        - `boreholes`
        - `drilling_reports`

        Use `schema.sql` in this project folder to create the same relational structure in Supabase or pgAdmin.
        """
    )


st.title("Powerhaven Borehole WebGIS")
st.caption("Geodatabase and web application for borehole drilling records, reports, yields, and mapped locations.")

data, supabase_configured = load_data()
if not supabase_configured:
    st.info("Running in demo mode. Add Supabase credentials to `.streamlit/secrets.toml` to use your live geodatabase.")

boreholes = data.get("boreholes", pd.DataFrame())
if boreholes.empty:
    st.error("No borehole records were found. Check the `boreholes` table in Supabase.")
    st.stop()

filtered_boreholes = apply_filters(boreholes)

dashboard, webgis_map, records, data_entry, schema = st.tabs(
    ["Dashboard", "WebGIS Map", "Records", "Data Entry", "Schema Guide"]
)

with dashboard:
    dashboard_tab(filtered_boreholes, data.get("drilling_reports", pd.DataFrame()))

with webgis_map:
    map_tab(filtered_boreholes, data.get("survey_points", pd.DataFrame()))

with records:
    records_tab(data, filtered_boreholes)

with data_entry:
    data_entry_tab(supabase_configured)

with schema:
    schema_tab()
