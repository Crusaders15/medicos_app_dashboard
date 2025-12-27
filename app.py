import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import random
import io
import time
from datetime import datetime

# --- 1. PAGE CONFIG & PREMIUM GREIGE UI ---
st.set_page_config(page_title="Ramp-Up: Market Intelligence", layout="wide")

def apply_professional_ui():
    st.markdown("""
        <style>
        .stApp {
            background-color: #f5f5f4; /* Professional Greige */
            color: #1c1917 !important;
        }
        section[data-testid="stSidebar"] {
            background-color: #e7e5e4 !important;
            border-right: 1px solid #d6d3d1;
        }
        /* Restore Title Visibility */
        .main-title {
            text-align: center;
            font-size: 3rem;
            font-weight: bold;
            color: #1c1917;
            margin-bottom: 20px;
        }
        /* No Emojis & Clean Platform UI */
        div[data-testid="stToolbarActions"], div[data-testid="stToolbar"] { display: none !important; }
        header[data-testid="stHeader"] { background-color: rgba(0,0,0,0) !important; }
        </style>
    """, unsafe_allow_html=True)

apply_professional_ui()

# --- 2. DATA INFRASTRUCTURE (THE ULTIMATE BINDER FIX) ---
@st.cache_resource
def get_db():
    creds = st.secrets["R2"]
    con = duckdb.connect(database=':memory:')
    con.execute("INSTALL httpfs; LOAD httpfs;")
    con.execute(f"SET s3_region='auto'; SET s3_endpoint='{creds['ACCOUNT_ID']}.r2.cloudflarestorage.com'; SET s3_access_key_id='{creds['ACCESS_KEY']}'; SET s3_secret_access_key='{creds['SECRET_KEY']}';")
    return con

db = get_db()
CSV_PATH = "s3://compra-agil-data/CA_2025.csv"
# We define a flat table name for SQL simplicity to avoid BinderException
DATA_SOURCE = f"read_csv('{CSV_PATH}', delim=';', header=True, encoding='cp1252', ignore_errors=True)"

# --- 3. SIDEBAR: FILTERS AT TOP, MEMES AT BOTTOM ---
with st.sidebar:
    st.header("Market Filters")
    date_range = st.date_input("Analysis Period", value=(datetime(2025, 1, 1), datetime(2025, 12, 31)))
    regions = ["All Regions", "Region Metropolitana de Santiago", "Region de Antofagasta", "Region de Valparaiso", "Region del Biobio", "Region del Maule"]
    target_region = st.selectbox("Select Region", regions)
    
    # Push memes to the very bottom
    for i in range(15): st.write("") # Manual Spacer
    st.markdown("---")
    
    base_url = "https://pub-a626d3085678426eae26e41ff821191f.r2.dev" 
    meme_playlist = [
        f"{base_url}/Memes/Drake%20Meme.jpg",
        f"{base_url}/Memes/Drake%20Meme%20afwt2v.jpg",
        f"{base_url}/Memes/Drake%20meme%20afwt19.jpg"
    ]
    # No emojis in captions
    st.image(random.choice(meme_playlist), use_container_width=True)
    st.caption("Internal Use Only - v36.0")

# --- 4. FILTERING LOGIC ---
def apply_filters(base_sql):
    sql = base_sql
    if target_region != "All Regions":
        sql += f" AND RegionUnidadCompra = '{target_region}'"
    if len(date_range) == 2:
        # Robust casting using try_cast to avoid crashes
        sql += f" AND try_cast(FechaPublicacion AS DATE) BETWEEN '{date_range[0]}' AND '{date_range[1]}'"
    return sql

# --- 5. MAIN DASHBOARD CONTENT ---
st.markdown("<h1 class='main-title'>Ramp-Up: Market Intelligence</h1>", unsafe_allow_html=True)

tabs = st.tabs(["Trends and Summary", "Regional Geography", "Specialty Analysis", "Detail View"])

with tabs[0]:
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Generate Trend Report", type="primary"):
            with st.spinner("Fetching Trends..."):
                try:
                    trend_sql = f"SELECT month(try_cast(FechaPublicacion AS DATE)) as Month, COUNT(*) as Tenders FROM {DATA_SOURCE} WHERE FechaPublicacion IS NOT NULL"
                    if target_region != "All Regions": trend_sql += f" AND RegionUnidadCompra = '{target_region}'"
                    trend_sql += " GROUP BY Month ORDER BY Month"
                    df_trend = db.execute(trend_sql).df()
                    fig = px.line(df_trend, x='Month', y='Tenders', title="Monthly Tender Volume", markers=True)
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Error loading trends: {str(e)}")
    
    with col_b:
        if st.button("Calculate Current Metrics"):
            with st.spinner("Running Analysis..."):
                res = db.execute(apply_filters(f"SELECT COUNT(*) as Total FROM {DATA_SOURCE} WHERE 1=1")).df()
                st.metric("Total Contracts Found", f"{res['Total'][0]:,}")

with tabs[1]:
    if st.button("Analyze City Activity"):
        with st.spinner("Mapping Cities..."):
            try:
                # Binder Fix: Be extremely explicit with column names
                geo_sql = apply_filters(f"SELECT CiudadUnidadCompra, COUNT(*) as Volume FROM {DATA_SOURCE} WHERE CiudadUnidadCompra IS NOT NULL") + " GROUP BY CiudadUnidadCompra ORDER BY Volume DESC LIMIT 20"
                df_geo = db.execute(geo_sql).df()
                fig_geo = px.bar(df_geo, x='Volume', y='CiudadUnidadCompra', orientation='h', title="Top Cities by Volume")
                st.plotly_chart(fig_geo, use_container_width=True)
            except Exception as e:
                st.error(f"Error loading Geography: {str(e)}")

with tabs[2]:
    if st.button("Run Profile Scan"):
        with st.spinner("Analyzing Professional Profiles..."):
            spec_map = {"Psicologia": "Psicolo", "TENS": "TENS", "Enfermeria": "Enfermer", "Neurologia": "Neuro"}
            results = []
            for label, keyword in spec_map.items():
                count_sql = apply_filters(f"SELECT COUNT(*) FROM {DATA_SOURCE} WHERE (DescripcionOC ILIKE '%{keyword}%' OR NombreOC ILIKE '%{keyword}%')")
                count = db.execute(count_sql).df().iloc[0,0]
                results.append({"Specialty": label, "Count": count})
            st.dataframe(pd.DataFrame(results), use_container_width=True)

with tabs[3]:
    if st.button("Load Raw Records"):
        with st.spinner("Fetching Data..."):
            df_raw = db.execute(apply_filters(f"SELECT codigoOC, NombreOC, Proveedor FROM {DATA_SOURCE} WHERE 1=1") + " LIMIT 100").df()
            st.dataframe(df_raw, use_container_width=True)
