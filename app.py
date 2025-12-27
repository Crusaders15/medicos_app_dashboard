import streamlit as st
import duckdb
import pandas as pd
from pydantic import BaseModel, ValidationError
from datetime import date
from typing import Optional, Tuple

# --- 1. DATA VALIDATION (PYDANTIC) ---
class DashboardFilters(BaseModel):
    date_range: Optional[Tuple[date, date]] = None
    region: str = "All"
    product_category: Optional[str] = None

# --- 2. THEME & SETUP ---
st.set_page_config(page_title="Ramp-Up: Market Intelligence", layout="wide")

# Applying the Greige style
st.markdown("""
    <style>
    .stApp { background-color: #D3D3D3; color: #2E2E2E; }
    .stSidebar { background-color: #BDB76B !important; }
    h1, h2, h3 { color: #4A4A4A !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. PERSISTENT DATABASE & R2 CONNECTION ---
@st.cache_resource
def get_db():
    con = duckdb.connect(database=':memory:')
    con.execute("INSTALL httpfs; LOAD httpfs;")
    return con

con = get_db()

@st.cache_data
def load_data_from_r2():
    try:
        # These credentials must be in your Streamlit Secrets
        con.execute(f"SET s3_access_key_id='{st.secrets['R2_ACCESS_KEY']}'")
        con.execute(f"SET s3_secret_access_key='{st.secrets['R2_SECRET_KEY']}'")
        con.execute(f"SET s3_endpoint='{st.secrets['R2_ENDPOINT']}'")
        con.execute("SET s3_url_style='path'")

        # This queries your 'compra-agil-data' bucket directly
        # Ensure the filename inside the bucket is 'data.csv'
        df = con.execute("SELECT * FROM read_csv_auto('s3://compra-agil-data/data.csv')").df()
        
        con.register("market_data", df)
        return df
    except Exception as e:
        st.error(f"CRITICAL ERROR: Failed to connect to Cloudflare R2 'compra-agil-data'.")
        st.info("Ensure R2_ACCESS_KEY, R2_SECRET_KEY, and R2_ENDPOINT are in your Streamlit Secrets.")
        st.stop()

df = load_data_from_r2()

# --- 4. SIDEBAR ---
st.sidebar.title("Global Slicers")
raw_date = st.sidebar.date_input("Analysis Period", value=(date(2025, 1, 1), date(2025, 12, 31)))
raw_region = st.sidebar.selectbox("Region", options=["All"] + sorted(df['Region'].unique().tolist()))
raw_product = st.sidebar.text_input("Product Category")

# Validate with Pydantic
try:
    filters = DashboardFilters(
        date_range=raw_date,
        region=raw_region,
        product_category=raw_product if raw_product else None
    )
except ValidationError as e:
    st.error(f"Filter Validation Error: {e}")
    st.stop()

# --- 5. MAIN DASHBOARD ---
st.title("Ramp-Up: Market Intelligence")
tabs = st.tabs(["Market Summary", "Specialty Analysis", "Leaderboards", "Competitive Analysis", "Detail View"])

with tabs[0]:
    if st.button("Refresh Summary Data"):
        st.cache_data.clear()
        st.rerun()

    try:
        sql = "SELECT COUNT(*) as Total FROM market_data WHERE 1=1"
        if filters.region != "All":
            sql += f" AND Region = '{filters.region}'"
        if filters.product_category:
            sql += f" AND ProductCategory ILIKE '%{filters.product_category}%'"
        if filters.date_range and len(filters.date_range) == 2:
            sql += f" AND Date >= '{filters.date_range[0]}' AND Date <= '{filters.date_range[1]}'"

        res = con.execute(sql).df()
        st.metric("Total Opportunities", f"{res['Total'].iloc[0]:,}")
        
    except Exception as e:
        st.error(f"Database Error: {e}")

st.sidebar.markdown("---")
st.sidebar.info("LicitaKiller - Internal Use")
