import streamlit as st
import duckdb
import pandas as pd

# --- 1. CONFIGURATION & SETUP ---
st.set_page_config(page_title="Ramp-Up: Market Intelligence", layout="wide")

# Change this to your actual data file path
DATA_PATH = "your_data_file.csv" 
DATA_SOURCE = "market_data"

@st.cache_data
def load_data():
    # Load your data here
    df = pd.read_csv(DATA_PATH)
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"Could not load data: {e}")
    st.stop()

# Initialize DuckDB and register the dataframe
db = duckdb.connect(database=':memory:')
db.register(DATA_SOURCE, df)

# --- 2. SIDEBAR / GLOBAL SLICERS ---
st.sidebar.header("Global Slicers")

analysis_period = st.sidebar.date_input(
    "Analysis Period",
    value=(pd.to_datetime("2025-01-01"), pd.to_datetime("2025-12-31"))
)

region_options = ["All"] + sorted(df['Region'].unique().tolist()) if 'Region' in df.columns else ["All"]
region = st.sidebar.selectbox("Region", options=region_options)

product_cat = st.sidebar.text_input("Product Category", placeholder="Example: Medical")

# --- 3. FILTER LOGIC ---
def apply_filters(base_query):
    filters = []
    
    # Date Filter (Assuming your column is named 'Date')
    if len(analysis_period) == 2:
        start_date, end_date = analysis_period
        filters.append(f"Date >= '{start_date}' AND Date <= '{end_date}'")
    
    # Region Filter
    if region != "All":
        filters.append(f"Region = '{region}'")
    
    # Product Category Filter
    if product_cat:
        filters.append(f"ProductCategory LIKE '%{product_cat}%'")
    
    if filters:
        # Join filters and append to query. 
        # Since your base query has 'WHERE 1=1', we always use 'AND'
        return f"{base_query} AND " + " AND ".join(filters)
    
    return base_query

# --- 4. MAIN DASHBOARD ---
st.title("Ramp-Up: Market Intelligence")

tabs = st.tabs(["Market Summary", "Specialty Analysis", "Leaderboards", "Competitive Analysis", "Detail View"])

with tabs[0]:
    if st.button("Refresh Summary Data"):
        st.rerun()

    # --- LINE 108 FIX ---
    try:
        # We ensure DATA_SOURCE is registered and apply_filters is defined above
        query = apply_filters(f"SELECT COUNT(*) as Total FROM {DATA_SOURCE} WHERE 1=1")
        res = db.execute(query).df()
        
        total_records = res['Total'].iloc[0]
        
        # Display Metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Opportunities", f"{total_records:,}")
        
    except Exception as e:
        st.error(f"Error executing query: {e}")
        st.info("Check if column names (Date, Region, ProductCategory) match your CSV exactly.")

# --- 5. INTERNAL USE ONLY SECTION ---
st.sidebar.markdown("---")
st.sidebar.subheader("Internal Use Only")
st.sidebar.info("Market Intelligence")
