import streamlit as st
import duckdb
import pandas as pd
from pydantic import BaseModel
from datetime import date
from typing import Optional, Tuple

# 1. Pydantic model for data safety
class DashboardFilters(BaseModel):
    date_range: Optional[Tuple[date, date]] = None
    region: str = "All"
    product_category: Optional[str] = None

# 2. Setup the persistent Database connection
@st.cache_resource
def get_db_con():
    return duckdb.connect(database=':memory:')

st.set_page_config(page_title="Ramp-Up: Market Intelligence", layout="wide")
con = get_db_con()

# 3. Load data and REGISTER it (This fixes the BinderException)
@st.cache_data
def load_data():
    df = pd.read_csv("data.csv") # Make sure your file is named data.csv
    con.register("market_data", df)
    return df

df = load_data()

# 4. Sidebar UI
st.sidebar.title("Global Slicers")
raw_date = st.sidebar.date_input("Analysis Period", value=(date(2025, 1, 1), date(2025, 12, 31)))
raw_region = st.sidebar.selectbox("Region", options=["All"] + sorted(df['Region'].unique().tolist()))
raw_product = st.sidebar.text_input("Product Category")

# 5. Validate filters
filters = DashboardFilters(
    date_range=raw_date,
    region=raw_region,
    product_category=raw_product if raw_product else None
)

# 6. Main Dashboard Logic
st.title("Ramp-Up: Market Intelligence")
tabs = st.tabs(["Market Summary", "Specialty Analysis", "Leaderboards"])

with tabs[0]:
    query = "SELECT COUNT(*) as Total FROM market_data WHERE 1=1"
    
    if filters.region != "All":
        query += f" AND Region = '{filters.region}'"
    if filters.product_category:
        query += f" AND ProductCategory ILIKE '%{filters.product_category}%'"
    
    # Executing the fixed line
    try:
        res = con.execute(query).df()
        st.metric("Total Opportunities", f"{res['Total'].iloc[0]:,}")
    except Exception as e:
        st.error(f"Error: {e}")
