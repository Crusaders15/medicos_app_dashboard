import streamlit as st
import duckdb
import pandas as pd
from pydantic import BaseModel, ValidationError
from datetime import date
from typing import Optional, List, Tuple

# --- 1. DATA MODELS (PYDANTIC) ---
class AppConfig(BaseModel):
    data_path: str = "data.csv"
    table_name: str = "market_intelligence_data"

class FilterParams(BaseModel):
    analysis_period: Tuple[date, date]
    region: str
    product_category: Optional[str] = None

# --- 2. DATABASE & DATA LOADING ---
@st.cache_resource
def get_db_connection():
    """Persistent DuckDB connection to prevent BinderExceptions."""
    return duckdb.connect(database=':memory:')

db = get_db_connection()

@st.cache_data
def load_and_register_data(file_path: str, table_name: str):
    """Loads CSV and registers it in DuckDB."""
    try:
        df = pd.read_csv(file_path)
        # Convert Date column to datetime if it isn't already
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date']).dt.date
        db.register(table_name, df)
        return df
    except Exception as e:
        st.error(f"Failed to load {file_path}: {e}")
        return None

# Initialize Configuration
config = AppConfig()
DATA_SOURCE = config.table_name
df = load_and_register_data(config.data_path, config.table_name)

# --- 3. PAGE SETUP & STYLING ---
st.set_page_config(page_title="Ramp-Up: Market Intelligence", layout="wide")

# Greige UI Theme Injection
st.markdown("""
    <style>
    .main { background-color: #f5f5f5; }
    .stSidebar { background-color: #e0e0e0; }
    div[data-testid="stMetricValue"] { color: #4A4A4A; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. SIDEBAR (GLOBAL SLICERS) ---
st.sidebar.title("Global Slicers")

if df is not None:
    # Period Filter
    date_val = st.sidebar.date_input(
        "Analysis Period",
        value=(date(2025, 1, 1), date(2025, 12, 31))
    )

    # Region Filter
    regions = ["All"] + sorted(df['Region'].unique().tolist())
    region_val = st.sidebar.selectbox("Region", options=regions)

    # Product Filter
    product_val = st.sidebar.text_input("Product Category", placeholder="Example: Medical")

    # Validate Inputs with Pydantic
    try:
        # Note: date_input can return a single date initially; ensure it's a tuple for Pydantic
        if isinstance(date_val, tuple) and len(date_val) == 2:
            current_filters = FilterParams(
                analysis_period=date_val,
                region=region_val,
                product_category=product_val if product_val else None
            )
        else:
            current_filters = None
    except ValidationError as e:
        st.error(f"Filter Validation Error: {e}")
        current_filters = None
else:
    st.warning("Please ensure data.csv is in the repository.")
    st.stop()

# --- 5. FILTER LOGIC ---
def apply_filters(base_sql: str) -> str:
    """Constructs the SQL WHERE clause based on Pydantic-validated filters."""
    if not current_filters:
        return base_sql
    
    clauses = []
    
    # Date Range
    start, end = current_filters.analysis_period
    clauses.append(f"Date >= '{start}' AND Date <= '{end}'")
    
    # Region
    if current_filters.region != "All":
        clauses.append(f"Region = '{current_filters.region}'")
        
    # Product Category (Case-Insensitive Search)
    if current_filters.product_category:
        clauses.append(f"ProductCategory ILIKE '%{current_filters.product_category}%'")
    
    if clauses:
        return f"{base_sql} AND " + " AND ".join(clauses)
    return base_sql

# --- 6. MAIN CONTENT ---
st.title("Ramp-Up: Market Intelligence")

tabs = st.tabs(["Market Summary", "Specialty Analysis", "Leaderboards", "Competitive Analysis", "Detail View"])

with tabs[0]:
    if st.button("Refresh Summary Data"):
        st.cache_data.clear()
        st.rerun()

    # --- THE LINE 108 FIX ---
    # We use 'db' (the persistent connection) and ensure DATA_SOURCE is registered
    try:
        query = apply_filters(f"SELECT COUNT(*) as Total FROM {DATA_SOURCE} WHERE 1=1")
        res = db.execute(query).df()
        total_count = res['Total'].iloc[0]

        # Display Metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Opportunities", f"{total_count:,}")
        
        # Optional: Show the data table
        st.subheader("Raw Data Preview")
        filtered_data_query = apply_filters(f"SELECT * FROM {DATA_SOURCE} WHERE 1=1 LIMIT 100")
        st.dataframe(db.execute(filtered_data_query).df(), use_container_width=True)

    except Exception as e:
        st.error(f"Binder Error: {e}")
        st.info("Ensure your CSV has columns named: 'Date', 'Region', and 'ProductCategory'.")

# Internal Use Footer
st.sidebar.markdown("---")
st.sidebar.subheader("Internal Use Only")
st.sidebar.info("Market Intelligence")
