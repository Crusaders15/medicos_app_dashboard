import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import random
import io
from datetime import datetime

# --- 1. PAGE CONFIG & UI ---
st.set_page_config(page_title="Ramp-Up: Intelligence Dashboard", layout="wide")

def apply_ui():
    st.markdown("""
        <style>
        .stApp {
            background-color: rgba(5, 5, 10, 0.97);
            background-image: url("https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072&auto=format&fit=crop");
            background-attachment: fixed;
            background-size: cover;
            background-blend-mode: darken;
        }
        .stMarkdown, .stText, h1, h2, h3, h4, h5, h6, p, label { color: #cfd8dc !important; }
        div[data-testid="stToolbarActions"], div[data-testid="stToolbar"] { display: none !important; }
        </style>
    """, unsafe_allow_html=True)
apply_ui()

# --- 2. DATA CONNECTION ---
@st.cache_resource
def get_db():
    creds = st.secrets["R2"]
    con = duckdb.connect(database=':memory:')
    con.execute("INSTALL httpfs; LOAD httpfs;")
    con.execute(f"SET s3_region='auto'; SET s3_endpoint='{creds['ACCOUNT_ID']}.r2.cloudflarestorage.com'; SET s3_access_key_id='{creds['ACCESS_KEY']}'; SET s3_secret_access_key='{creds['SECRET_KEY']}';")
    return con

db = get_db()
# Optimization: We cast FechaPublicacion to DATE immediately
DATA_SOURCE = """
    (SELECT *, CAST(FechaPublicacion AS DATE) as CleanDate 
     FROM read_csv('s3://compra-agil-data/CA_2025.csv', delim=';', header=True, encoding='cp1252', ignore_errors=True))
"""

# --- 3. SIDEBAR, MEMES & FILTERS ---
st.sidebar.header("Global Slicers")

# MEME SECTION
base_url = "https://pub-a626d3085678426eae26e41ff821191f.r2.dev" 
meme_playlist = [
    f"{base_url}/Memes/Drake%20Meme.jpg",
    f"{base_url}/Memes/Drake%20Meme%20afwt2v.jpg",
    f"{base_url}/Memes/Drake%20meme%20afwt19.jpg"
]

with st.sidebar:
    st.markdown("---")
    st.image(random.choice(meme_playlist), use_container_width=True)
    st.markdown("---")

date_range = st.sidebar.date_input("Analysis Period", value=(datetime(2025, 1, 1), datetime(2025, 12, 31)))
target_region = st.sidebar.selectbox("Region", ["All Regions", "Region Metropolitana de Santiago", "Region de Antofagasta", "Region de Valparaiso", "Region del Biobio"])

# --- 4. FILTER LOGIC ---
def apply_filters(base_sql):
    sql = base_sql
    if target_region != "All Regions":
        sql += f" AND RegionUnidadCompra = '{target_region}'"
    if len(date_range) == 2:
        sql += f" AND CleanDate BETWEEN '{date_range[0]}' AND '{date_range[1]}'"
    return sql

# --- 5. TABS ---
t1, t2, t3, t4 = st.tabs(["Market Summary", "Specialty Analysis", "Competitive", "Detail View"])

with t1:
    st.markdown("### Market Trends")
    if st.button("Generate Trend Report"):
        # This query groups by Month
        trend_sql = apply_filters(f"SELECT month(CleanDate) as Month, COUNT(*) as Tenders FROM {DATA_SOURCE} WHERE 1=1") + " GROUP BY Month ORDER BY Month"
        df_trend = db.execute(trend_sql).df()
        
        fig_trend = px.line(df_trend, x='Month', y='Tenders', title="Tenders Volume by Month", markers=True, template="plotly_dark")
        fig_trend.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_trend, use_container_width=True)
    
    st.divider()
    if st.button("Calculate Current Metrics"):
        res = db.execute(apply_filters(f"SELECT COUNT(*) as Total FROM {DATA_SOURCE} WHERE 1=1")).df()
        st.metric("Total Contracts Found", f"{res['Total'][0]:,}")

with t2:
    st.header("Specialty Analysis")
    if st.button("Run Professional Demand Scan"):
        spec_map = {"Psicologia": "Psicolo", "TENS": "TENS", "Enfermeria": "Enfermer"}
        results = [{"Specialty": k, "Count": db.execute(apply_filters(f"SELECT COUNT(*) FROM {DATA_SOURCE} WHERE DescripcionOC ILIKE '%{v}%'")).df().iloc[0,0]} for k, v in spec_map.items()]
        st.bar_chart(pd.DataFrame(results).set_index("Specialty"))

with t4:
    if st.button("Load Detailed Data"):
        df_v = db.execute(apply_filters(f"SELECT CleanDate, codigoOC, NombreOC FROM {DATA_SOURCE} WHERE 1=1") + " LIMIT 100").df()
        st.dataframe(df_v, use_container_width=True)
