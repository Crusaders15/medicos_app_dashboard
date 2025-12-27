import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import random
import io
from datetime import datetime

# --- 1. PAGE CONFIG & UI ---
st.set_page_config(page_title="Ramp-Up: Market Intelligence", layout="wide")

def apply_ui():
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
apply_ui()

# --- 2. DATA INFRASTRUCTURE ---
@st.cache_resource
def get_db():
    creds = st.secrets["R2"]
    con = duckdb.connect(database=':memory:')
    con.execute("INSTALL httpfs; LOAD httpfs;")
    con.execute(f"SET s3_region='auto'; SET s3_endpoint='{creds['ACCOUNT_ID']}.r2.cloudflarestorage.com'; SET s3_access_key_id='{creds['ACCESS_KEY']}'; SET s3_secret_access_key='{creds['SECRET_KEY']}';")
    return con

db = get_db()

# NUCLEAR DATE FIX: Force try_cast to prevent BinderException
DATA_SOURCE = """
    (SELECT *, 
     try_cast(FechaPublicacion AS DATE) as CleanDate,
     COALESCE(CiudadUnidadCompra, 'Unknown') as City
     FROM read_csv('s3://compra-agil-data/CA_2025.csv', delim=';', header=True, encoding='cp1252', ignore_errors=True))
"""

# --- 3. SIDEBAR & MEMES ---
st.sidebar.header("Global Slicers")

# Verified Public URL from your screenshot
base_url = "https://pub-a626d3085678426eae26e41ff821191f.r2.dev" 
meme_playlist = [
    f"{base_url}/Memes/Drake%20Meme.jpg",
    f"{base_url}/Memes/Drake%20Meme%20afwt2v.jpg",
    f"{base_url}/Memes/Drake%20meme%20afwt19.jpg"
]

with st.sidebar:
    st.markdown("---")
    # Randomly picks a meme. If R2 fails, it shows a professional placeholder.
    meme_choice = random.choice(meme_playlist)
    st.image(meme_choice, use_container_width=True, caption="Market Intelligence")
    st.markdown("---")

date_range = st.sidebar.date_input("Analysis Period", value=(datetime(2025, 1, 1), datetime(2025, 12, 31)))
target_region = st.sidebar.selectbox("Region", ["All Regions", "Region Metropolitana de Santiago", "Region de Antofagasta", "Region de Valparaiso", "Region del Biobio"])

def apply_filters(base_sql):
    sql = base_sql
    if target_region != "All Regions":
        sql += f" AND RegionUnidadCompra = '{target_region}'"
    if len(date_range) == 2:
        sql += f" AND CleanDate BETWEEN '{date_range[0]}' AND '{date_range[1]}'"
    return sql

# --- 4. ANALYTICS TABS ---
t1, t2, t3, t4 = st.tabs(["Market Summary", "Regional Geography", "Specialty Analysis", "Detail View"])

with t1:
    st.markdown("### Market Trends Over Time")
    if st.button("Generate Trend Report"):
        # We use try_cast here again to ensure safety
        trend_sql = apply_filters(f"SELECT month(CleanDate) as Month, COUNT(*) as Total FROM {DATA_SOURCE} WHERE CleanDate IS NOT NULL") + " GROUP BY Month ORDER BY Month"
        df_trend = db.execute(trend_sql).df()
        if not df_trend.empty:
            fig_trend = px.line(df_trend, x='Month', y='Total', title="Monthly Tender Volume", markers=True, template="plotly_dark")
            fig_trend.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.warning("No valid dates found in the selected range.")

with t2:
    st.markdown("### Geography Heatmap")
    if st.button("Analyze City Distribution"):
        geo_sql = apply_filters(f"SELECT City, COUNT(*) as Volume FROM {DATA_SOURCE} WHERE 1=1") + " GROUP BY City ORDER BY Volume DESC LIMIT 20"
        df_geo = db.execute(geo_sql).df()
        fig_geo = px.bar(df_geo, x='Volume', y='City', orientation='h', title="Top 20 Cities by Tender Volume", color='Volume', template="plotly_dark")
        fig_geo.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_geo, use_container_width=True)

with t3:
    st.header("Professional Specialty Analysis")
    if st.button("Run Demand Scan"):
        spec_map = {"Psicologia": "Psicolo", "TENS": "TENS", "Enfermeria": "Enfermer"}
        results = [{"Specialty": k, "Count": db.execute(apply_filters(f"SELECT COUNT(*) FROM {DATA_SOURCE} WHERE DescripcionOC ILIKE '%{v}%'")).df().iloc[0,0]} for k, v in spec_map.items()]
        st.bar_chart(pd.DataFrame(results).set_index("Specialty"))

with t4:
    if st.button("Load Detail Records"):
        df_detail = db.execute(apply_filters(f"SELECT CleanDate, codigoOC, NombreOC, City FROM {DATA_SOURCE} WHERE 1=1") + " LIMIT 100").df()
        st.dataframe(df_detail, use_container_width=True)
