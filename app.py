import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import random
import io
from datetime import datetime

# --- 1. PAGE CONFIG & GREIGE UI ---
st.set_page_config(page_title="Ramp-Up: Market Intelligence", layout="wide")

def apply_clean_ui():
    st.markdown("""
        <style>
        .stApp {
            background-color: #f5f5f4; /* Soft Greige for eye comfort */
            color: #1c1917 !important;
        }
        section[data-testid="stSidebar"] {
            background-color: #e7e5e4 !important;
            border-right: 1px solid #d6d3d1;
        }
        /* Restore Professional Text Color */
        .stMarkdown, .stText, h1, h2, h3, h4, h5, h6, p, label, .stTabs { 
            color: #1c1917 !important; 
        }
        /* Hide platform elements */
        div[data-testid="stToolbarActions"], div[data-testid="stToolbar"] { display: none !important; }
        header[data-testid="stHeader"] { background-color: rgba(0,0,0,0) !important; }
        </style>
    """, unsafe_allow_html=True)
apply_clean_ui()

# --- 2. DATA CONNECTION ---
@st.cache_resource
def get_db():
    creds = st.secrets["R2"]
    con = duckdb.connect(database=':memory:')
    con.execute("INSTALL httpfs; LOAD httpfs;")
    con.execute(f"SET s3_region='auto'; SET s3_endpoint='{creds['ACCOUNT_ID']}.r2.cloudflarestorage.com'; SET s3_access_key_id='{creds['ACCESS_KEY']}'; SET s3_secret_access_key='{creds['SECRET_KEY']}';")
    return con

db = get_db()
CSV_PATH = "s3://compra-agil-data/CA_2025.csv"
DATA_SOURCE = f"read_csv('{CSV_PATH}', delim=';', header=True, encoding='cp1252', ignore_errors=True)"

# --- 3. SIDEBAR: FILTERS TOP, MEMES BOTTOM ---
with st.sidebar:
    st.header("Market Filters")
    # Using text input for dates to avoid BinderException during development
    date_start = st.text_input("Start Date (YYYY-MM-DD)", "2025-01-01")
    date_end = st.text_input("End Date (YYYY-MM-DD)", "2025-12-31")
    
    regions = ["All Regions", "Region Metropolitana de Santiago", "Region de Antofagasta", "Region de Valparaiso", "Region del Biobio", "Region del Maule"]
    target_region = st.selectbox("Select Region", regions)
    
    # Push memes to the bottom
    st.container(height=300, border=False) 
    st.markdown("---")
    st.markdown("### Internal Use Only")
    
    base_url = "https://pub-a626d3085678426eae26e41ff821191f.r2.dev" 
    meme_playlist = [
        f"{base_url}/Memes/Drake%20Meme.jpg",
        f"{base_url}/Memes/Drake%20Meme%20afwt2v.jpg",
        f"{base_url}/Memes/Drake%20meme%20afwt19.jpg"
    ]
    st.image(random.choice(meme_playlist), use_container_width=True)
    st.caption("Baseline Recovery v40.0")

# --- 4. FILTERING LOGIC ---
def apply_filters(base_sql):
    sql = base_sql
    if target_region != "All Regions":
        sql += f" AND RegionUnidadCompra = '{target_region}'"
    # Basic string-based filtering to avoid complex casting errors
    sql += f" AND FechaPublicacion >= '{date_start}' AND FechaPublicacion <= '{date_end}'"
    return sql

# --- 5. MAIN CONTENT ---
st.markdown("<h1 style='text-align: center; font-weight: bold;'>Ramp-Up: Market Intelligence</h1>", unsafe_allow_html=True)

tabs = st.tabs(["Summary", "Regional Geography", "Specialty Analysis", "Detail View"])

with tabs[0]:
    if st.button("Refresh Summary Data", type="primary"):
        with st.spinner("Fetching from R2..."):
            res = db.execute(apply_filters(f"SELECT COUNT(*) as Total FROM {DATA_SOURCE} WHERE 1=1")).df()
            st.metric("Total Contracts identified", f"{res['Total'][0]:,}")

with tabs[1]:
    if st.button("Analyze City Distribution"):
        with st.spinner("Loading Geography..."):
            geo_sql = apply_filters(f"SELECT CiudadUnidadCompra as City, COUNT(*) as Count FROM {DATA_SOURCE} WHERE 1=1") + " GROUP BY City ORDER BY Count DESC LIMIT 15"
            df_geo = db.execute(geo_sql).df()
            st.bar_chart(df_geo.set_index("City"))

with tabs[2]:
    if st.button("Scan Professional Specialties"):
        with st.spinner("Analyzing Profiles..."):
            spec_map = {"Psicologia": "Psicolo", "TENS": "TENS", "Enfermeria": "Enfermer"}
            results = []
            for label, keyword in spec_map.items():
                count = db.execute(apply_filters(f"SELECT COUNT(*) FROM {DATA_SOURCE} WHERE DescripcionOC ILIKE '%{keyword}%'")).df().iloc[0,0]
                results.append({"Specialty": label, "Count": count})
            st.dataframe(pd.DataFrame(results).set_index("Specialty"), use_container_width=True)

with tabs[3]:
    if st.button("Load 100 Raw Records"):
        df_detail = db.execute(apply_filters(f"SELECT codigoOC, NombreOC, Proveedor FROM {DATA_SOURCE} WHERE 1=1") + " LIMIT 100").df()
        st.dataframe(df_detail, use_container_width=True)
