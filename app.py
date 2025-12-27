import streamlit as st
import duckdb
import pandas as pd
import datetime
from pydantic import BaseModel
from typing import Optional, Tuple

# --- CONFIGURATION & VALIDATION ---
class AppConfig(BaseModel):
    title: str = "Ramp-Up: Market Intelligence"
    table_name: str = "market_data"
    file_path: str = "data.csv"

class FilterSchema(BaseModel):
    region: str
    product_cat: Optional[str] = None
    dates: Tuple[datetime.date, datetime.date]

config = AppConfig()

st.set_page_config(page_title=config.title, layout="wide")

# --- GREIGE STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #D3D3D3; color: #2E2E2E; }
    .stSidebar { background-color: #BDB76B !important; }
    h1, h2, h3 { color: #4A4A4A !important; }
    </style>
    """, unsafe_allow_html=True)

# --- DATABASE ENGINE ---
@st.cache_resource
def get_connection():
    return duckdb.connect(database=':memory:')

con = get_connection()

@st.cache_data
def load_and_register():
    try:
        df = pd.read_csv(config.file_path)
        con.register(config.table_name, df)
        return df
    except Exception as e:
        st.error(f"Error loading {config.file_path}: {e}")
        return None

df = load_and_register()

# --- SIDEBAR FILTERS ---
st.sidebar.title("Global Slicers")

date_range = st.sidebar.date_input(
    "Analysis Period", 
    value=(datetime.date(2025, 1, 1), datetime.date(2025, 12, 31))
)

# Populate regions from CSV
if df is not None:
    region_options = ["All"] + sorted(df['Region'].unique().tolist())
else:
    region_options = ["All"]

selected_region = st.sidebar.selectbox("Region", options=region_options)
product_input = st.sidebar.text_input("Product Category", placeholder="e.g. Medical")

# --- MAIN DASHBOARD ---
st.title(config.title)

if df is not None:
    # Validate inputs using Pydantic
    if isinstance(date_range, tuple) and len(date_range) == 2:
        filters = FilterSchema(
            region=selected_region,
            product_cat=product_input,
            dates=date_range
        )

        tabs = st.tabs(["Market Summary", "Specialty Analysis", "Leaderboards"])

        with tabs[0]:
            try:
                # Build Query
                where = ["1=1"]
                if filters.region != "All":
                    where.append(f"Region = '{filters.region}'")
                if filters.product_cat:
                    where.append(f"ProductCategory ILIKE '%{filters.product_cat}%'")
                
                sql = f"SELECT COUNT(*) as Total FROM {config.table_name} WHERE " + " AND ".join(where)
                
                # Execute
                res = con.execute(sql).df()
                total = res['Total'].iloc[0]
                
                st.metric("Total Opportunities", f"{total:,}")
                st.dataframe(df.head(50), use_container_width=True)
                
            except Exception as e:
                st.error(f"Query Error: {e}")
                st.info("Ensure your CSV has 'Region' and 'ProductCategory' columns.")
    else:
        st.info("Select a full date range (Start and End) to see data.")
else:
    st.warning(f"File '{config.file_path}' not found in the repository.")
