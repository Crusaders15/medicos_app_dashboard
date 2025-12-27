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
        div[data-testid="stToolbarActions"], div[data-testid="stToolbar"] { display: none !important; }
        header[data-testid="stHeader"] { background-color: rgba(0,0,0,0) !important; }
        </style>
    """, unsafe_allow_html=True)
apply_stable_ui()

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

# --- 3. SIDEBAR & MEMES ---
st.sidebar.header("Global Slicers")
date_range = st.sidebar.date_input("Analysis Period", value=(datetime(2025, 1, 1), datetime(2025, 12, 31)))
target_region = st.sidebar.selectbox("Region", ["All Regions", "Region Metropolitana de Santiago", "Region de Antofagasta", "Region de Valparaiso", "Region del Biobio"])

with st.sidebar:
    for _ in range(10): st.write("") # Spacer
    st.markdown("---")
    base_url = "https://pub-a626d3085678426eae26e41ff821191f.r2.dev" 
    meme_playlist = [
        f"{base_url}/Memes/Drake%20Meme.jpg",
        f"{base_url}/Memes/Drake%20Meme%20afwt2v.jpg",
        f"{base_url}/Memes/Drake%20meme%20afwt19.jpg"
    ]
    st.image(random.choice(meme_playlist), use_container_width=True)
    st.caption("Baseline Recovery v39.0")

# --- 4. DATA FILTERING ---
def apply_filters(base_sql):
    sql = base_sql
    if target_region != "All Regions":
        sql += f" AND RegionUnidadCompra = '{target_region}'"
    if len(date_range) == 2:
        # Nuclear cast fix to prevent BinderExceptions
        sql += f" AND try_cast(FechaPublicacion AS DATE) BETWEEN '{date_range[0]}' AND '{date_range[1]}'"
    return sql

# --- 5. CONTENT ---
st.markdown("<h1 style='text-align: center;'>Ramp-Up: Market Intelligence</h1>", unsafe_allow_html=True)

tabs = st.tabs(["Market Summary", "Geography Analysis", "Specialty Scan", "Raw Data"])

with tabs[0]:
    if st.button("Calculate Metrics", type="primary"):
        res = db.execute(apply_filters(f"SELECT COUNT(*) as Total FROM {DATA_SOURCE} WHERE 1=1")).df()
        st.metric("Total Contracts identified", f"{res['Total'][0]:,}")

with tabs[1]:
    if st.button("Analyze Top Cities"):
        geo_sql = apply_filters(f"SELECT CiudadUnidadCompra as City, COUNT(*) as Count FROM {DATA_SOURCE} WHERE City IS NOT NULL") + " GROUP BY City ORDER BY Count DESC LIMIT 15"
        df_geo = db.execute(geo_sql).df()
        st.bar_chart(df_geo.set_index("City"))

with tabs[2]:
    if st.button("Scan Professional Specialties"):
        spec_map = {"Psicologia": "Psicolo", "TENS": "TENS", "Enfermeria": "Enfermer"}
        results = []
        for label, keyword in spec_map.items():
            count = db.execute(apply_filters(f"SELECT COUNT(*) FROM {DATA_SOURCE} WHERE DescripcionOC ILIKE '%{keyword}%'")).df().iloc[0,0]
            results.append({"Specialty": label, "Count": count})
        st.dataframe(pd.DataFrame(results), use_container_width=True)

with tabs[3]:
    if st.button("Load 100 Records"):
        df_detail = db.execute(apply_filters(f"SELECT codigoOC, NombreOC, Proveedor FROM {DATA_SOURCE} WHERE 1=1") + " LIMIT 100").df()
        st.dataframe(df_detail, use_container_width=True)
