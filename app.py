import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px

# --- PAGE CONFIG ---
st.set_page_config(page_title="Ramp-Up: Intelligence Dashboard" #JoseAntonioLovers, layout="wide")

st.title("Ramp-Up: Market Intelligence #JoseAntonioLovers")

# --- CONNECT TO DATA (R2) ---
@st.cache_resource
def get_connection():
    # We get the keys securely from Streamlit Secrets
    aws_access_key_id = st.secrets["R2"]["ACCESS_KEY"]
    aws_secret_access_key = st.secrets["R2"]["SECRET_KEY"]
    account_id = st.secrets["R2"]["ACCOUNT_ID"]
    
    con = duckdb.connect(database=':memory:')
    con.execute("INSTALL httpfs; LOAD httpfs;")
    con.execute(f"""
        SET s3_region='auto';
        SET s3_endpoint='{account_id}.r2.cloudflarestorage.com';
        SET s3_access_key_id='{aws_access_key_id}';
        SET s3_secret_access_key='{aws_secret_access_key}';
    """)
    return con

# --- DEFINING THE SOURCE (The Fix) ---
# We use read_csv to handle the Chilean format (Semicolons + Latin-1 Encoding)
CSV_FILE = "s3://compra-agil-data/CA_2025.csv"
REMOTE_TABLE = f"read_csv('{CSV_FILE}', delim=';', header=True, encoding='latin-1', ignore_errors=True)"

try:
    con = get_connection()
    st.toast("Connected to Cloudflare R2 Cloud ☁️", icon="✅")
except Exception as e:
    st.error(f"Connection Failed: {e}")

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["📊 Market Overview", "🕵️ Profile Detective", "📥 Data Extractor"])

# === TAB 1: THE POWER BI ===
with tab1:
    st.markdown("### Market Distribution")
    if st.button("🔄 Load Regional Data"):
        # Note: We use {REMOTE_TABLE} without quotes now
        query_geo = f"SELECT RegionUnidadCompra as Region, COUNT(*) as Total FROM {REMOTE_TABLE} GROUP BY Region ORDER BY Total DESC"
        with st.spinner("Analyzing data..."):
            try:
                df_geo = con.execute(query_geo).df()
                fig = px.bar(df_geo, x='Region', y='Total', title="Tenders by Region")
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Query Error: {e}")

# === TAB 2: THE DETECTIVE ===
with tab2:
    st.markdown("###Find Hidden Professionals")
    st.info("Search descriptions for specific terms.")
    col_search, col_limit = st.columns([3, 1])
    search_term = col_search.text_input("Search Keyword", placeholder="e.g., Salud Mental")
    limit = col_limit.number_input("Max Results", value=50)

    if search_term:
        # We search in DescripcionItem or NombreItem (adjusted for standard column names)
        detective_query = f"""
            SELECT * FROM {REMOTE_TABLE} 
            WHERE DescripcionItem ILIKE '%{search_term}%' 
            OR NombreItem ILIKE '%{search_term}%'
            LIMIT {limit}
        """
        with st.spinner(f"Hunting for '{search_term}'..."):
            try:
                results = con.execute(detective_query).df()
                st.dataframe(results)
                st.success(f"Found {len(results)} matches.")
            except Exception as e:
                st.error(f"Query Error: {e}")

# === TAB 3: EXTRACTOR ===
with tab3:
    st.markdown("### Extract Codes")
    custom_sql = st.text_area("Custom SQL", value=f"SELECT * FROM {REMOTE_TABLE} LIMIT 5")
    if st.button("Run Custom SQL"):
        try:
            df_custom = con.execute(custom_sql).df()
            st.dataframe(df_custom)
        except Exception as e:
            st.error(f"Error: {e}")

