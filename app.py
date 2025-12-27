import streamlit as st
import duckdb
import pandas as pd
import os

# --- 1. SETUP & THEME ---
st.set_page_config(page_title="Ramp-Up: Market Intelligence", layout="wide")

# Theme styling to match your dark dashboard
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    [data-testid="stMetricValue"] { color: #ff4b4b; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CLOUDFLARE R2 / S3 CONFIGURATION ---
# Using the bucket name from your setup: 'compra-agil-data'
BUCKET_NAME = "compra-agil-data"
DATA_KEY = "market_intelligence.csv" # Update this to your specific .csv object name in R2

@st.cache_resource
def get_db_con():
    con = duckdb.connect(database=':memory:')
    # Loading the S3 extension for R2 compatibility
    con.execute("INSTALL httpfs; LOAD httpfs;")
    # These should be set in your Streamlit secrets or environment variables
    # con.execute(f"SET s3_access_key_id='{st.secrets['R2_ACCESS_KEY']}'")
    # con.execute(f"SET s3_secret_access_key='{st.secrets['R2_SECRET_KEY']}'")
    # con.execute(f"SET s3_endpoint='{st.secrets['R2_ENDPOINT']}'")
    return con

con = get_db_con()

@st.cache_data
def load_and_register():
    try:
        # Note: For your specific R2 bucket 'compra-agil-data'
        # If testing locally with a file, use the line below:
        df = pd.read_csv("compra-agil-data.csv") # Updated name based on your bucket context
        
        # Ensure column names match for the filters below
        con.register("market_data", df)
        return df
    except Exception as e:
        st.error(f"Error loading {BUCKET_NAME} data: {e}")
        st.stop()

df = load_and_register()

# --- 3. SIDEBAR FILTERS ---
st.sidebar.title("Global Slicers")
date_range = st.sidebar.date_input("Analysis Period", value=(pd.to_datetime("2025-01-01"), pd.to_datetime("2025-12-31")))

# Using 'Region' as seen in your previous dashboard configuration
region_col = 'Region' 
regions = ["All"] + sorted(df[region_col].unique().tolist())
selected_region = st.sidebar.selectbox("Region", options=regions)

product_col = 'ProductCategory'
product_search = st.sidebar.text_input("Product Category")

# --- 4. MAIN UI ---
st.title("Ramp-Up: Market Intelligence")
tabs = st.tabs(["Market Summary", "Specialty Analysis", "Leaderboards", "Competitive Analysis", "Detail View"])

with tabs[0]:
    if st.button("Refresh Summary Data"):
        st.cache_data.clear()
        st.rerun()

    try:
        # Constructing the SQL query for the 'market_data' table
        sql = "SELECT COUNT(*) as Total FROM market_data WHERE 1=1"
        
        if selected_region != "All":
            sql += f" AND {region_col} = '{selected_region}'"
        
        if product_search:
            sql += f" AND {product_col} ILIKE '%{product_search}%'"
            
        if isinstance(date_range, tuple) and len(date_range) == 2:
            sql += f" AND Date >= '{date_range[0]}' AND Date <= '{date_range[1]}'"

        res = con.execute(sql).df()
        st.metric("Total Opportunities", f"{res['Total'].iloc[0]:,}")
        
    except Exception as e:
        st.error(f"Database Error: {e}")

# --- 5. INTERNAL SECTION ---
st.sidebar.markdown("---")
st.sidebar.subheader("Internal Use Only")
st.sidebar.info("LicitaKiller - Market Intelligence")
