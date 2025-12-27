import streamlit as st
import duckdb
import pandas as pd

# --- 1. PAGE SETUP & THEME ---
st.set_page_config(page_title="Ramp-Up: Market Intelligence", layout="wide")

# Applying the dark theme and layout from your screenshot
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    [data-testid="stMetricValue"] { color: #ff4b4b; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: transparent; border-radius: 4px 4px 0px 0px; gap: 1px; padding-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE PERSISTENCE ---
@st.cache_resource
def get_db_connection():
    """Maintains a persistent DuckDB connection across Streamlit reruns."""
    return duckdb.connect(database=':memory:')

db = get_db_connection()

@st.cache_data
def load_data_and_register():
    """Loads CSV and registers it as a table in DuckDB."""
    try:
        # Load your specific file
        df = pd.read_csv("data.csv")
        
        # Ensure the Date column is actual datetime objects for filtering
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date']).dt.date
        
        # This is the critical fix: Registering the dataframe as a table name
        db.register("market_data", df)
        return df
    except Exception as e:
        st.error(f"Error loading data.csv: {e}")
        st.stop()

# Initialize data and database registration
df = load_data_and_register()

# --- 3. SIDEBAR (GLOBAL SLICERS) ---
st.sidebar.title("Global Slicers")

# Analysis Period
analysis_period = st.sidebar.date_input(
    "Analysis Period",
    value=(pd.to_datetime("2025-01-01"), pd.to_datetime("2025-12-31"))
)

# Region Filter
regions = ["All"] + sorted(df['Region'].unique().tolist())
selected_region = st.sidebar.selectbox("Region", options=regions)

# Product Category Filter
product_cat = st.sidebar.text_input("Product Category", placeholder="Example: Medical")

# --- 4. MAIN UI DASHBOARD ---
st.title("Ramp-Up: Market Intelligence")

tabs = st.tabs(["Market Summary", "Specialty Analysis", "Leaderboards", "Competitive Analysis", "Detail View"])

with tabs[0]:
    if st.button("Refresh Summary Data"):
        st.cache_data.clear()
        st.rerun()

    # --- THE PREVIOUSLY BROKEN SECTION (FIXED) ---
    try:
        # Build the dynamic SQL query string
        query = "SELECT COUNT(*) as Total FROM market_data WHERE 1=1"
        
        # Date Filter
        if isinstance(analysis_period, tuple) and len(analysis_period) == 2:
            query += f" AND Date >= '{analysis_period[0]}' AND Date <= '{analysis_period[1]}'"
        
        # Region Filter
        if selected_region != "All":
            query += f" AND Region = '{selected_region}'"
        
        # Product Filter (using ILIKE for case-insensitive matching)
        if product_cat:
            query += f" AND ProductCategory ILIKE '%{product_cat}%'"

        # Execute fixed query
        res = db.execute(query).df()
        total_opportunities = res['Total'].iloc[0]

        # Display Metrics
        st.metric("Total Opportunities", f"{total_opportunities:,}")
        
        # Data Preview Table
        st.subheader("Market Summary Table")
        table_query = query.replace("SELECT COUNT(*) as Total", "SELECT *") + " LIMIT 100"
        st.dataframe(db.execute(table_query).df(), use_container_width=True)

    except Exception as e:
        st.error(f"Database Error: {e}")
        st.info("Check if your CSV headers match 'Date', 'Region', and 'ProductCategory'.")

# --- 5. FOOTER ---
st.sidebar.markdown("---")
st.sidebar.subheader("Internal Use Only")
st.sidebar.info("Market Intelligence")
