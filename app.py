import streamlit as st
import duckdb
import pandas as pd
from pydantic import BaseModel
from datetime import date
from typing import Optional, Tuple

# --- PERSISTENCE LAYER ---
@st.cache_resource
def get_database_connection():
    """Keeps the DuckDB connection alive across app reruns."""
    return duckdb.connect(database=':memory:')

# --- DATA VALIDATION ---
class DashboardFilters(BaseModel):
    date_range: Optional[Tuple[date, date]] = None
    region: str = "All"
    product_category: Optional[str] = None

# --- APP SETUP ---
st.set_page_config(page_title="Ramp-Up: Market Intelligence", layout="wide")
con = get_database_connection()

@st.cache_data
def load_and_register_data():
    """Loads the CSV and binds it to DuckDB."""
    try:
        # Update this filename if your CSV has a different name
        df = pd.read_csv("data.csv") 
        con.register("market_data", df)
        return df
    except Exception as e:
        st.error(f"Could not load data.csv: {e}")
        st.stop()

df = load_and_register_data()

# --- SIDEBAR UI ---
st.sidebar.title("Global Slicers")
raw_date = st.sidebar.date_input("Analysis Period", value=(date(2025, 1, 1), date(2025, 12, 31)))

# Dynamic region list from your data
region_list = ["All"] + sorted(df['Region'].unique().tolist())
raw_region = st.sidebar.selectbox("Region", options=region_list)
raw_product = st.sidebar.text_input("Product Category")

# Validate inputs using Pydantic
filters = DashboardFilters(
    date_range=raw_date,
    region=raw_region,
    product_category=raw_product if raw_product else None
)

# --- MAIN DASHBOARD ---
st.title("Ramp-Up: Market Intelligence")
tabs = st.tabs(["Market Summary", "Specialty Analysis", "Leaderboards"])

with tabs[0]:
    # This replaces the broken Line 108 logic
    base_query = "SELECT COUNT(*) as Total FROM market_data WHERE 1=1"
    
    if filters.region != "All":
        base_query += f" AND Region = '{filters.region}'"
    if filters.product_category:
        base_query += f" AND ProductCategory ILIKE '%{filters.product_category}%'"
    
    try:
        # Execute fixed query
        res = con.execute(base_query).df()
        total_value = res['Total'].iloc[0]
        st.metric("Total Opportunities", f"{total_value:,}")
    except Exception as e:
        st.error(f"Query Error: {e}")

st.sidebar.markdown("---")
st.sidebar.info("Internal Use Only: Market Intelligence")
