import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import random
import io
from datetime import datetime

# --- 1. PAGE CONFIG & SOFT LIGHT UI ---
st.set_page_config(page_title="Ramp-Up: Market Intelligence", layout="wide")

def apply_light_ui():
    st.markdown("""
        <style>
        .stApp {
            background-color: #f5f5f4; /* Professional Soft Greige */
            color: #1c1917 !important;
        }
        /* Sidebar styling: Darker for contrast but clean */
        section[data-testid="stSidebar"] {
            background-color: #e7e5e4 !important;
            border-right: 1px solid #d6d3d1;
        }
        /* Ensure all text is dark for readability */
        .stMarkdown, .stText, h1, h2, h3, h4, h5, h6, p, label, .stTabs { 
            color: #1c1917 !important; 
        }
        /* UI Cleanup */
        div[data-testid="stToolbarActions"], div[data-testid="stToolbar"] { display: none !important; }
        header[data-testid="stHeader"] { background-color: rgba(0,0,0,0) !important; }
        </style>
    """, unsafe_allow_html=True)

apply_light_ui()

# --- 2. DATA INFRASTRUCTURE (STABILITY FIRST) ---
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

# --- 3. SIDEBAR: FILTERS AT TOP, MEMES AT BOTTOM ---
with st.sidebar:
    st.header("Market Slicers")
    date_range = st.date_input("Analysis Period", value=(datetime(2025, 1, 1), datetime(2025, 12, 31)))
    target_region = st.selectbox("Region", ["All Regions", "Region Metropolitana de Santiago", "Region de Antofagasta", "Region de Valparaiso", "Region del Biobio"])
    
    # Push memes to the bottom
    st.container(height=300, border=False) # Spacer
    st.markdown("---")
    st.markdown("### Internal Use Only")
    
    base_url = "https://pub-a626d3085678426eae26e41ff821191f.r2.dev" 
    meme_playlist = [
        f"{base_url}/Memes/Drake%20Meme.jpg",
        f"{base_url}/Memes/Drake%20Meme%20afwt2v.jpg",
        f"{base_url}/Memes/Drake%20meme%20afwt19.jpg"
    ]
    st.image(random.choice(meme_playlist), use_container_width=True)
    st.caption("Ramp-Up Intelligence v34.0")

# --- 4. FILTERING LOGIC ---
def apply_filters(base_sql):
    sql = base_sql
    if target_region != "All Regions":
        sql += f" AND RegionUnidadCompra = '{target_region}'"
    # Basic date filtering
    if len(date_range) == 2:
        sql += f" AND CAST(FechaPublicacion AS DATE) BETWEEN '{date_range[0]}' AND '{date_range[1]}'"
    return sql

# --- 5. MAIN CONTENT ---
st.title("Ramp-Up: Market Intelligence")

tabs = st.tabs(["📊 Summary & Trends", "📍 Geography", "🩺 Specialties", "📄 Records"])

with tabs[0]:
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Generate Trend Report", type="primary"):
            try:
                trend_sql = f"SELECT month(CAST(FechaPublicacion AS DATE)) as Month, COUNT(*) as Total FROM {DATA_SOURCE} WHERE FechaPublicacion IS NOT NULL"
                if target_region != "All Regions": trend_sql += f" AND RegionUnidadCompra = '{target_region}'"
                trend_sql += " GROUP BY Month ORDER BY Month"
                df_trend = db.execute(trend_sql).df()
                fig = px.line(df_trend, x='Month', y='Total', title="Monthly Volume", markers=True)
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error("Select a valid date range to load trends.")

    with col2:
        if st.button("Load Quick Metrics"):
            res = db.execute(apply_filters(f"SELECT COUNT(*) as Total FROM {DATA_SOURCE} WHERE 1=1")).df()
            st.metric("Total Contracts", f"{res['Total'][0]:,}")

with tabs[1]:
    if st.button("Show City Distribution"):
        geo_sql = apply_filters(f"SELECT CiudadUnidadCompra as City, COUNT(*) as Volume FROM {DATA_SOURCE} WHERE 1=1") + " GROUP BY City ORDER BY Volume DESC LIMIT 20"
        st.bar_chart(db.execute(geo_sql).df().set_index("City"))

with tabs[2]:
    if st.button("Analyze Medical Demand"):
        spec_map = {"Psicologia": "Psicolo", "TENS": "TENS", "Enfermeria": "Enfermer"}
        results = [{"Specialty": k, "Count": db.execute(apply_filters(f"SELECT COUNT(*) FROM {DATA_SOURCE} WHERE (DescripcionOC ILIKE '%{v}%' OR NombreOC ILIKE '%{v}%')")).df().iloc[0,0]} for k, v in spec_map.items()]
        st.dataframe(pd.DataFrame(results), use_container_width=True)

with tabs[3]:
    if st.button("Load Detailed View"):
        df_detail = db.execute(apply_filters(f"SELECT codigoOC, NombreOC, CiudadUnidadCompra, Proveedor FROM {DATA_SOURCE} WHERE 1=1") + " LIMIT 100").df()
        st.dataframe(df_detail, use_container_width=True)
