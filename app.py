import streamlit as st
import duckdb
import pandas as pd
import os

# --- CONFIGURATION ---
PAGE_TITLE = "Ramp-Up: Market Intelligence"
FILE_PATH = "data.csv"
TABLE_NAME = "market_data"

st.set_page_config(page_title=PAGE_TITLE, layout="wide")

# --- STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #D3D3D3; color: #2E2E2E; }
    .stSidebar { background-color: #BDB76B !important; }
    h1, h2, h3 { color: #4A4A4A !important; }
    </style>
    """, unsafe_allow_html=True)

# --- DATABASE CONNECTION ---
@st.cache_resource
def get_db():
    return duckdb.connect(database=':memory:')

con = get_db()

# --- DATA LOADER ---
@st.cache_data
def load_data():
    if not os.path.exists(FILE_PATH):
        return None
    
    try:
        df = pd.read_csv(FILE_PATH)
        con.register(TABLE_NAME, df)
        return df
    except Exception as e:
        st.error(f"Error reading CSV: {e}")
        return None

df = load_data()

# --- DASHBOARD LOGIC ---
st.title(PAGE_TITLE)

if df is None:
    st.error("CRITICAL ERROR: 'data.csv' was not found in this repository.")
    st.info("Action: Go to GitHub, click 'Add file' -> 'Upload files', and upload your data.csv.")
else:
    # Sidebar
    st.sidebar.title("Filters")
    regions = ["All"] + sorted(df['Region'].unique().tolist())
    selected_region = st.sidebar.selectbox("Region", regions)
    cat_search = st.sidebar.text_input("Category Search")

    # Query Builder
    query = f"SELECT COUNT(*) as Total FROM {TABLE_NAME} WHERE 1=1"
    
    if selected_region != "All":
        query += f" AND Region = '{selected_region}'"
    
    if cat_search:
        query += f" AND ProductCategory ILIKE '%{cat_search}%'"

    # Execution
    try:
        res = con.execute(query).df()
        st.metric("Total Opportunities", f"{res['Total'].iloc[0]:,}")
        st.dataframe(df.head(50))
    except Exception as e:
        st.error(f"Query Error: {e}")
