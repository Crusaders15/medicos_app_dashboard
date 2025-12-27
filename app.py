import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import random
import io
from datetime import datetime

# --- 1. PAGE CONFIG & STABLE DARK UI ---
st.set_page_config(page_title="Ramp-Up: Intelligence Dashboard", layout="wide")

def apply_stable_ui():
    st.markdown("""
        <style>
        .stApp {
            background-color: rgba(5, 5, 10, 0.98);
            background-image: url("https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072&auto=format&fit=crop");
            background-attachment: fixed;
            background-size: cover;
            background-blend-mode: darken;
        }
        .stMarkdown, .stText, h1, h2, h3, h4, h5, h6, p, label { color: #cfd8dc !important; }
        /* Hide platform clutter */
        div[data-testid="stToolbarActions"], div[data-testid="stToolbar"] { display: none !important; }
        header[data-testid="stHeader"] { background-color: rgba(0,0,0,0) !important; }
        </style>
    """, unsafe_allow_html=True)
apply_stable_ui()

# --- 2. DATA INFRASTRUCTURE (RECOVERY LOGIC) ---
@st.cache_resource
def get_db():
    creds = st.secrets["R2"]
    con = duckdb.connect(database=':memory:')
    con.execute("INSTALL httpfs; LOAD httpfs;")
    con.execute(f"SET s3_region='auto'; SET s3_endpoint='{creds['ACCOUNT_ID']}.r2.cloudflarestorage.com'; SET s3_access_key_id='{creds['ACCESS_KEY']}'; SET s3_secret_access_key='{creds['SECRET_KEY']}';")
    return con

db = get_db()
CSV_PATH = "s3://compra-agil-data/CA_2025.csv"
# Stable Data Source definition
DATA_SOURCE = f"read_csv('{CSV_PATH}', delim=';', header=True, encoding='cp1252', ignore_errors=True)"

# --- 3. SIDEBAR: FILTERS TOP, MEMES BOTTOM ---
with st.sidebar:
    st.header("Global Slicers")
    date_range = st.date_input("Analysis Period", value=(datetime(2025, 1, 1), datetime(2025, 12, 31)))
    target_region = st.selectbox("Region", ["All Regions", "Region Metropolitana de Santiago", "Region de Antofagasta", "Region de Valparaiso", "Region del Biobio"])
    
    # Push memes to the bottom
    for _ in range(10): st.write("") 
    st.markdown("---")
    
    base_url = "https://pub-a626d3085678426eae26e41ff821191f.r2.dev" 
    meme_playlist = [
        f"{base_url}/Memes/Drake%20Meme.jpg",
        f"{base_url}/Memes/Drake%20Meme%20afwt2v.jpg",
        f"{base_url}/Memes/Drake%20meme%20afwt19.jpg"
    ]
    st.image(random.choice(meme_playlist), use_container_width=True)
    st.caption("Stable Recovery v38.0")

# --- 4. DATA FILTERING ---
def apply_filters(base_sql):
    sql = base_sql
    if target_region != "All Regions":
        sql += f" AND RegionUnidadCompra = '{target_region}'"
    if len(date_range) == 2:
        # Use try_cast to prevent BinderException crashes
        sql += f" AND try_cast(FechaPublicacion AS DATE) BETWEEN '{date_range[0]}' AND '{date_range[1]}'"
    return sql

# --- 5. CONTENT ---
st.markdown("<h1 style='text-align: center;'>Ramp-Up: Market Intelligence</h1>", unsafe_allow_html=True)

tabs = st.tabs(["Market Summary", "Geography Analysis", "Specialty Scan", "Raw Data"])

with tabs[0]:
    if st.button("Calculate Metrics", type="primary"):
        with st.spinner("Accessing R2 Storage..."):
            res = db.execute(apply_filters(f"SELECT COUNT(*) as Total FROM {DATA_SOURCE} WHERE 1=1
