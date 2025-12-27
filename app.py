import streamlit as st
import duckdb
import pandas as pd

# --- 1. SETTINGS & PERSISTENCE ---
st.set_page_config(page_title="Ramp-Up: Market Intelligence", layout="wide")

@st.cache_resource
def get_database():
    """Keeps the DuckDB connection alive so it doesn't lose your data."""
    con = duckdb.connect(database=':memory:')
    # Required to talk to Cloudflare R2
    con.execute("INSTALL httpfs; LOAD httpfs;")
    return con

con = get_database()

@st.cache_data
def load_data():
    try:
        # These MUST be set in your Streamlit Cloud 'Secrets'
        con.execute(f"SET s3_access_key_id='{st.secrets['R2_ACCESS_KEY']}'")
        con.execute(f"SET s3_secret_access_key='{st.secrets['R2_SECRET_KEY']}'")
        con.execute(f"SET s3_endpoint='{st.secrets['R2_ENDPOINT']}'")
        con.execute("SET s3_url_style='path'")

        # This queries your 'compra-agil-data' bucket directly
        # Ensure the file inside R2 is named exactly what you put here
        df = con.execute("SELECT * FROM read_csv_auto('s3://compra-agil-data/data.csv')").df()
        
        # This binds the name 'market_data' so line 108 works
        con.register("market_data", df)
        return df
    except Exception as e:
        st.error(f"Failed to connect to R2 bucket 'compra-agil-data'.")
        st.info("Check your Streamlit Secrets for R2_ACCESS_KEY, R2_SECRET_KEY, and R2_ENDPOINT.")
        st.stop()

df = load_data()

# --- 2. SIDEBAR ---
st.sidebar.title("Global Slicers")
date_range = st.sidebar.date_input("Analysis Period", value=(pd.to_datetime("2025-01-01"), pd.to_datetime("2025-12-31")))
region = st.sidebar.selectbox("Region", options=["All"] + sorted(df['Region'].unique().tolist()))
product = st.sidebar.text_input("Product Category")

# --- 3. MAIN UI ---
st.title("Ramp-Up: Market Intelligence")
tabs = st.tabs(["Market Summary", "Specialty Analysis", "Leaderboards", "Competitive Analysis", "Detail View"])

with tabs[0]:
    if st.button("Refresh Summary Data"):
        st.cache_data.clear()
        st.rerun()

    try:
        # THE FIX: Querying the registered table
        sql = "SELECT COUNT(*) as Total FROM market_data WHERE 1=1"
        
        if region != "All":
            sql += f" AND Region = '{region}'"
        
        if product:
            sql += f" AND ProductCategory ILIKE '%{product}%'"
            
        if isinstance(date_range, tuple) and len(date_range) == 2:
            sql += f" AND Date >= '{date_range[0]}' AND Date <= '{date_range[1]}'"

        res = con.execute(sql).df()
        st.metric("Total Opportunities", f"{res['Total'].iloc[0]:,}")
        
    except Exception as e:
        st.error(f"Database Error: {e}")

st.sidebar.markdown("---")
st.sidebar.info("LicitaKiller - Internal Use")
