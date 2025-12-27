import streamlit as st
import duckdb
import pandas as pd
import datetime
from typing import Optional, Tuple, Any

# --- CONSTANTS & CONFIGURATION ---
PAGE_TITLE: str = "Ramp-Up: Market Intelligence"
DATA_FILE_PATH: str = "data.csv"
TABLE_NAME: str = "market_data"
THEME_BG_COLOR: str = "#D3D3D3"
THEME_SIDEBAR_COLOR: str = "#BDB76B"

st.set_page_config(page_title=PAGE_TITLE, layout="wide")

# --- STYLING INJECTION ---
def inject_custom_css() -> None:
    """Injects 'Greige' theme CSS into the Streamlit app."""
    st.markdown(f"""
        <style>
        .stApp {{ background-color: {THEME_BG_COLOR}; color: #2E2E2E; }}
        .stSidebar {{ background-color: {THEME_SIDEBAR_COLOR} !important; }}
        h1, h2, h3 {{ color: #4A4A4A !important; }}
        </style>
        """, unsafe_allow_html=True)

inject_custom_css()

# --- DATABASE MANAGEMENT ---
@st.cache_resource
def get_db_connection() -> duckdb.DuckDBPyConnection:
    """
    Creates and caches a persistent in-memory DuckDB connection.
    Using cache_resource ensures the connection remains alive across reruns.
    """
    return duckdb.connect(database=':memory:')

# Global database connection instance
conn: duckdb.DuckDBPyConnection = get_db_connection()

@st.cache_data
def load_data_into_db(file_path: str, table: str) -> Optional[pd.DataFrame]:
    """
    Loads CSV data and explicitly registers it as a table in DuckDB.
    
    Args:
        file_path: Path to the CSV file.
        table: Name of the table to create in DuckDB.
        
    Returns:
        The loaded Pandas DataFrame or None if loading fails.
    """
    try:
        df: pd.DataFrame = pd.read_csv(file_path)
        # Explicit registration fixes the 'BinderException'
        conn.register(table, df)
        return df
    except FileNotFoundError:
        st.error(f"Critical Error: File '{file_path}' not found in the repository.")
        return None
    except Exception as e:
        st.error(f"Data Load Error: {str(e)}")
        return None

# Load data immediately
df_global: Optional[pd.DataFrame] = load_data_into_db(DATA_FILE_PATH, TABLE_NAME)

# --- QUERY LOGIC ---
def execute_query(sql: str) -> pd.DataFrame:
    """
    Executes a SQL query safely against the persistent connection.
    """
    try:
        return conn.execute(sql).df()
    except Exception as e:
        st.error(f"SQL Execution Failed: {str(e)}")
        return pd.DataFrame()

def build_sql_query(region: str, category: str) -> str:
    """
    Constructs a SQL query string with safe filter injection.
    """
    clauses: list[str] = ["1=1"]
    
    if region != "All":
        clauses.append(f"Region = '{region}'")
    
    # ILIKE provides case-insensitive matching
    if category:
        clauses.append(f"ProductCategory ILIKE '%{category}%'")
    
    condition_str: str = " AND ".join(clauses)
    return f"SELECT COUNT(*) as Total FROM {TABLE_NAME} WHERE {condition_str}"

# --- UI & INTERACTION ---
st.sidebar.title("Global Slicers")

# Date Input
analysis_period: Tuple[datetime.date, datetime.date] = st.sidebar.date_input(
    "Analysis Period",
    value=(datetime.date(2025, 1, 1), datetime.date(2025, 12, 31))
)

# Region Selector
unique_regions: list[str] = ["All"]
if df_global is not None:
    # Ensure strict type conversion to list
    unique_regions += sorted(list(df_global['Region'].unique()))

selected_region: str = st.sidebar.selectbox("Region", options=unique_regions)

# Category Input
category_input: str = st.sidebar.text_input("Product Category", placeholder="Example: Medical")

# --- MAIN EXECUTION ---
st.title(PAGE_TITLE)

if df_global is not None:
    # Ensure date input is a complete tuple
    if isinstance(analysis_period, tuple) and len(analysis_period) == 2:
        
        # Tabs for organization
        tab_summary, tab_details = st.tabs(["Market Summary", "Raw Data"])

        with tab_summary:
            if st.button("Refresh Summary Data"):
                st.rerun()

            # Generate and Run Query
            query_string: str = build_sql_query(selected_region, category_input)
            result_df: pd.DataFrame = execute_query(query_string)

            if not result_df.empty:
                total_opps: int = result_df['Total'].iloc[0]
                st.metric("Total Opportunities", f"{total_opps:,}")
            else:
                st.warning("No data returned from query.")

        with tab_details:
            st.dataframe(df_global.head(100), use_container_width=True)

    else:
        st.info("Please select both a Start Date and End Date.")
else:
    st.warning("Application is waiting for data source.")
