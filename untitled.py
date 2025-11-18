@st.cache_data(ttl=60)
def load_data():
    # Load boreholes
    bore_resp = supabase.table("boreholes").select("borehole_id, client_id, survey_id, depth_m, casing_class, status, date_drilled").execute()
    bore_df = pd.DataFrame(bore_resp.data)
    
    # Load clients
    clients_resp = supabase.table("clients").select("client_id, client_name, address").execute()
    clients_df = pd.DataFrame(clients_resp.data)
    
    # Load survey_points (for coordinates)
    survey_resp = supabase.table("survey_points").select("survey_id, coordinates").execute()
    survey_df = pd.DataFrame(survey_resp.data)
    
    # Merge tables
    print(bore_df['survey_id'].dtype)
    print(survey_df['survey_id'].dtype)
    df = bore_df.merge(clients_df, on="client_id", how="left")
    df = df.merge(survey_df, on="survey_id", how="left")
    
    # Extract latitude & longitude from coordinates
    # Assumes coordinates stored like: {'lat': xx.xxxx, 'lng': yy.yyyy}
    if not df.empty and "coordinates" in df.columns:
        df['latitude'] = df['coordinates'].apply(lambda x: x['lat'] if x else None)
        df['longitude'] = df['coordinates'].apply(lambda x: x['lng'] if x else None)
    
    return df

df = load_data()

if df.empty:
    st.warning("No data found in Supabase table.")
else:
    st.success(f"{len(df)} records successfully loaded from Supabase!")





    import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- Supabase connection ---
url = "https://mhcsryyqvhyntzrbdyuc.supabase.co"
key = "YOUR_SUPABASE_KEY"
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Powerhaven Boreholes Dashboard", layout="wide")

# ============================
# 🔹 LOAD DATA FUNCTION
# ============================
@st.cache_data
def load_data():
    # --- Load all data from Supabase ---
    bore_resp = supabase.table("boreholes").select("*").execute()
    clients_resp = supabase.table("clients").select("*").execute()
    survey_resp = supabase.table("survey_points").select("*").execute()
    drilling_resp = supabase.table("drilling_reports").select("*").execute()
    siting_resp = supabase.table("siting_reports").select("*").execute()

    # --- Convert to DataFrames ---
    bore_df = pd.DataFrame(bore_resp.data)
    clients_df = pd.DataFrame(clients_resp.data)
    survey_df = pd.DataFrame(survey_resp.data)
    drilling_df = pd.DataFrame(drilling_resp.data)
    siting_df = pd.DataFrame(siting_resp.data)

    # --- Ensure all key columns are strings to avoid merge issues ---
    for df in [bore_df, drilling_df]:
        if 'borehole_id' in df.columns:
            df['borehole_id'] = df['borehole_id'].astype(str)
    for df in [bore_df, clients_df]:
        if 'client_id' in df.columns:
            df['client_id'] = df['client_id'].astype(str)
    for df in [bore_df, survey_df, siting_df]:
        if 'survey_id' in df.columns:
            df['survey_id'] = df['survey_id'].astype(str)

    # --- Merge tables correctly ---
    # Merge boreholes with clients
    merged_df = bore_df.merge(clients_df, on="client_id", how="left")

    # Merge boreholes with drilling_reports
    merged_df = merged_df.merge(drilling_df, on="borehole_id", how="left", suffixes=('', '_drilling'))

    # Merge survey_points with siting_reports first
    survey_siting_df = survey_df.merge(siting_df, on="survey_id", how="left", suffixes=('', '_siting'))

    # Merge everything with merged_df on survey_id
    merged_df = merged_df.merge(survey_siting_df, on="survey_id", how="left", suffixes=('', '_survey'))

    # --- Extract latitude and longitude from coordinates ---
    if 'coordinates' in merged_df.columns:
        try:
            merged_df['latitude'] = merged_df['coordinates'].apply(lambda x: x.get('lat') if isinstance(x, dict) else None)
            merged_df['longitude'] = merged_df['coordinates'].apply(lambda x: x.get('lng') if isinstance(x, dict) else None)
        except Exception as e:
            st.warning(f"Coordinate extraction issue: {e}")

    return merged_df

# ============================
# 🔹 LOAD THE DATA
# ============================
st.title("💧 Powerhaven Boreholes & Solar Dashboard")

with st.spinner("Loading data from Supabase..."):
    df = load_data()

if df is None or df.empty:
    st.error("No data available. Check Supabase connection.")
    st.stop()

# ============================
# 🔹 FILTERS AND DISPLAY
# ============================
client_options = df["client_name"].dropna().unique().tolist()

selected_client = st.selectbox(
    "Select Client",
    options=client_options,
)

st.subheader(f"📊 Data for {selected_client}")
filtered_df = df[df["client_name"] == selected_client]
st.dataframe(filtered_df)
