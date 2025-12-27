import streamlit as st
import duckdb
import pandas as pd
import datetime
from pydantic import BaseModel
from typing import Optional, Tuple

# --- 1. CONFIGURATION (PYDANTIC) ---
class DashboardConfig(BaseModel):
    title: str = "Ramp-Up: Market Intelligence"
    table_name: str = "market_data"
    file_path: str = "data.csv"
    bg_color: str = "#D3D3D3"
    sidebar_color: str = "#BDB76B"
    text_color: str = "#2E2E2E"

class FilterSchema(BaseModel):
    region: str
    product_cat: Optional[str] = None
    dates: Tuple[datetime.date, datetime.date]

config = DashboardConfig()

# --- 2. LAYOUT & STYLING ---
st.set_page_config(page_title=config.title, layout="wide")

st.markdown(f"""
    <style>
    .stApp {{ background-color: {config.bg_color}; color: {config.text_color}; }}
    .stSidebar {{ background-color: {config.sidebar_color} !important; }}
    h1, h2, h3 {{ color: #4A4A4A !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATA & DATABASE ---
@st.cache_resource
def get_db_connection():
    # Persistent in-memory DuckDB connection
    return duckdb.connect(database=':memory:')

con = get_db_connection()

@st.cache_data
def load_and_register():
    try:
        df = pd.read_csv(config.file_path)
        # This registration prevents the BinderException on line 108
        con.register(config.table_name, df)
        return df
    except Exception as e:
        st.error(f"Could not find or load {config.file_path}. Error: {e}")
        return None

df = load_and_register()

# --- 4. SIDEBAR FILTERS ---
st.sidebar.title("Global Slicers")

# Analysis Period
date_range = st.sidebar.date_input(
    "Analysis Period", 
    value=(datetime.date(2025, 1, 1), datetime.date(2025, 12, 31))
)

# Dynamic Region List
regions = ["All"] + sorted(df['Region'].unique().tolist()) if df is not None else ["All"]
selected_region = st.sidebar.selectbox("Region", options=regions)

# Product Search
product_input = st.sidebar.text_input("Product Category", placeholder="Example: Medical")

st.sidebar.markdown("---")
st.sidebar.subheader("Internal Use Only")
st.sidebar.info("Market Intelligence")

# --- 5. MAIN DASHBOARD ---
st.title(config.title)

if df is not None:
    # Ensure a full date range is selected
    if isinstance(date_range, tuple) and len(date_range) == 2:
        # Validate inputs via Pydantic
        filters = FilterSchema(
            region=selected_region,
            product_cat=product_input,
            dates=date_range
        )

        tabs = st.tabs(["Market Summary", "Specialty Analysis", "Leaderboards", "Competitive Analysis", "Detail View"])

        with tabs[0]:
            if st.button("Refresh Summary Data"):
                st.rerun()

            try:
                # Build SQL logic
                where_clauses = ["1=1"]
                if filters.region != "All":
                    where_clauses.append(f"Region = '{filters.region}'")
                if filters.product_cat:
                    where_clauses.append(f"ProductCategory ILIKE '%{filters.product_cat}%'")
                
                sql_query = f"SELECT COUNT(*) as Total FROM {config.table_name} WHERE " + " AND ".join(where_clauses)
                
                # Execute query using the persistent connection
                res = con.execute(sql_query).df()
                total_records = res['Total'].iloc[0]
                
                # Display Result
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Opportunities", f"{total_records:,}")
                
                st.subheader("Data Preview")
                st.dataframe(df.head(100), use_container_width=True)

            except Exception as e:
                st.error(f"Query Execution Error: {e}")
                st.info("Check if your CSV columns match exactly: 'Region', 'ProductCategory'.")
    else:
        st.info("Please select both a Start and End date in the sidebar.")
else:
    st.warning("Please ensure 'data.csv' is uploaded to your GitHub repository.")
