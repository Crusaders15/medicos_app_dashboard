import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import random
import io
from datetime import datetime

# --- 1. PAGE CONFIG & DARK UI ---
st.set_page_config(page_title="Ramp-Up: Market Intelligence", layout="wide")

def apply_premium_ui():
    bg_url = "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072&auto=format&fit=crop"
    st.markdown(f"""
        <style>
        .stApp {{
            background-color: rgba(5, 5, 10, 0.98);
            background-image: url("{bg_url}");
            background-attachment: fixed;
            background-size: cover;
            background-blend-mode: darken;
        }}
        /* Restore Soft Text & Sidebar Dark Mode */
        .stMarkdown, .stText, h1, h2, h3, h4, h5, h6, p, label, .stTabs {{ color: #cfd8dc !important; }}
        section[data-testid="stSidebar"] {{
            background-color: rgba(10, 10, 20, 0.95) !important;
            border-right: 1px solid #333;
        }}
        /* Clean Up Platform UI */
        div[data-testid="stToolbarActions"], div[data-testid="stToolbar"] {{ display: none !important; }}
        header[data-testid="stHeader"] {{ background-color: rgba(0,0,0,0) !important; }}
        </style>
    """, unsafe_allow_html=True)

apply_premium_ui()

# --- 2. DATA INFRASTRUCTURE (THE BINDER FIX) ---
@st.cache_resource
def get_db():
    creds = st.secrets["R2"]
    con = duckdb.connect(database=':memory:')
    con.execute("INSTALL httpfs; LOAD httpfs;")
    con.execute(f"SET s3_region='auto'; SET s3_endpoint='{creds['ACCOUNT_ID']}.r2.cloudflarestorage.com'; SET s3_access_key_id='{creds['ACCESS_KEY']}'; SET s3_secret_access_key='{creds['SECRET_KEY']}';")
    return con

db = get_db()
# We define the data source precisely to avoid 'CleanDate' errors
CSV_PATH = "s3://compra-agil-data/CA_2025.csv"
DATA_SOURCE = f"read_csv('{CSV_PATH}', delim=';', header=True, encoding='cp1252', ignore_errors=True)"

# --- 3. SIDEBAR & MEME STYLING ---
# Using your verified R2 Public URL
base_url = "https://pub-a626d3085678426eae26e41ff821191f.r2.dev" 
meme_playlist = [
    f"{base_url}/Memes/Drake%20Meme.jpg",
    f"{base_url}/Memes/Drake%20Meme%20afwt2v.jpg",
    f"{base_url}/Memes/Drake%20meme%20afwt19.jpg"
]

with st.sidebar:
    st.image(random.choice(meme_playlist), use_container_width=True)
    st.markdown("---")
    st.header("Global Slicers")
    date_range = st.date_input("Analysis Period", value=(datetime(2025, 1, 1), datetime(2025, 12, 31)))
    target_region = st.selectbox("Region", ["All Regions", "Region Metropolitana de Santiago", "Region de Antofagasta", "Region de Valparaiso", "Region del Biobio"])
    st.markdown("---")
    st.caption("Ramp-Up Intelligence v33.0")

# --- 4. DATA FILTERING LOGIC ---
def apply_filters(base_sql):
    sql = base_sql
    if target_region != "All Regions":
        sql += f" AND RegionUnidadCompra = '{target_region}'"
    # Handling date filtering manually to avoid DuckDB casting issues
    if len(date_range) == 2:
        sql += f" AND CAST(FechaPublicacion AS DATE) BETWEEN '{date_range[0]}' AND '{date_range[1]}'"
    return sql

# --- 5. MAIN DASHBOARD CONTENT ---
st.markdown("<h1 style='text-align: center; text-shadow: 2px 2px 4px #000000;'>Ramp-Up: Market Intelligence</h1>", unsafe_allow_html=True)

tabs = st.tabs(["Market Trends", "Geography Heatmap", "Specialty Analysis", "Detail View"])

with tabs[0]:
    st.subheader("Tender Volume Trends")
    if st.button("Generate Trend Report"):
        trend_sql = apply_filters(f"SELECT month(CAST(FechaPublicacion AS DATE)) as Month, COUNT(*) as Total FROM {DATA_SOURCE} WHERE FechaPublicacion IS NOT NULL") + " GROUP BY Month ORDER BY Month"
        df_trend = db.execute(trend_sql).df()
        fig_trend = px.line(df_trend, x='Month', y='Total', markers=True, template="plotly_dark")
        fig_trend.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_trend, use_container_width=True)
    
    st.divider()
    if st.button("Calculate Market Metrics"):
        res = db.execute(apply_filters(f"SELECT COUNT(*) as Total FROM {DATA_SOURCE} WHERE 1=1")).df()
        st.metric("Total Contracts Found", f"{res['Total'][0]:,}")

with tabs[1]:
    st.subheader("Regional Geography")
    if st.button("Analyze City Distribution"):
        geo_sql = apply_filters(f"SELECT CiudadUnidadCompra as City, COUNT(*) as Volume FROM {DATA_SOURCE} WHERE 1=1") + " GROUP BY City ORDER BY Volume DESC LIMIT 20"
        df_geo = db.execute(geo_sql).df()
        fig_geo = px.bar(df_geo, x='Volume', y='City', orientation='h', color='Volume', template="plotly_dark")
        fig_geo.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_geo, use_container_width=True)

with tabs[2]:
    st.subheader("Professional Specialty Analysis")
    if st.button("Scan Specialty Demand"):
        spec_map = {"Psicologia": "Psicolo", "TENS": "TENS", "Enfermeria": "Enfermer"}
        results = [{"Specialty": k, "Count": db.execute(apply_filters(f"SELECT COUNT(*) FROM {DATA_SOURCE} WHERE DescripcionOC ILIKE '%{v}%'")).df().iloc[0,0]} for k, v in spec_map.items()]
        st.bar_chart(pd.DataFrame(results).set_index("Specialty"))

with tabs[3]:
    if st.button("Load Detailed Data (First 100)"):
        df_detail = db.execute(apply_filters(f"SELECT codigoOC, NombreOC, CiudadUnidadCompra FROM {DATA_SOURCE} WHERE 1=1") + " LIMIT 100").df()
        st.dataframe(df_detail, use_container_width=True)
