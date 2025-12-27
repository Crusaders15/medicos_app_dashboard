import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import random
import io
from datetime import datetime

# --- 1. PAGE CONFIG & DARK UI ---
st.set_page_config(
    page_title="Ramp-Up: Market Intelligence", 
    layout="wide",
    initial_sidebar_state="expanded" 
)

def set_design():
    bg_url = "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072&auto=format&fit=crop"
    st.markdown(
         f"""
         <style>
         .stApp {{
             background-image: url("{bg_url}");
             background-attachment: fixed;
             background-size: cover;
             background-color: rgba(0,0,0,0.85);
             background-blend-mode: darken;
         }}
         .stMarkdown, .stText, h1, h2, h3, h4, h5, h6, p, li, span, label, div {{
             color: white !important;
         }}
         section[data-testid="stSidebar"] {{
             background-color: rgba(0, 0, 0, 0.6);
         }}
         div[data-testid="stToolbarActions"], .stToolbarActions, div[data-testid="stToolbar"] {{
             display: none !important;
         }}
         header[data-testid="stHeader"] {{ background-color: rgba(0,0,0,0) !important; }}
         .stDeployButton {{ display: none !important; }}
         footer {{ visibility: hidden !important; }}
         </style>
         """,
         unsafe_allow_html=True
     )

set_design()

# --- 2. SECURITY SYSTEM ---
if "password_correct" not in st.session_state:
    st.session_state.password_correct = False

if not st.session_state.password_correct:
    st.markdown("<h1 style='text-align: center;'>Ramp-Up Intelligence</h1>", unsafe_allow_html=True)
    pwd_input = st.text_input("Access Code", type="password")
    if pwd_input:
        if pwd_input == st.secrets.get("GENERAL", {}).get("APP_PASSWORD", "licitakiller2025"):
            st.session_state.password_correct = True
            st.rerun()
        else:
            st.error("Access Denied")
    st.stop()

# --- 3. DATA CONNECTION ---
@st.cache_resource
def get_connection():
    creds = st.secrets["R2"]
    con = duckdb.connect(database=':memory:')
    con.execute("INSTALL httpfs; LOAD httpfs;")
    con.execute(f"SET s3_region='auto'; SET s3_endpoint='{creds['ACCOUNT_ID']}.r2.cloudflarestorage.com'; SET s3_access_key_id='{creds['ACCESS_KEY']}'; SET s3_secret_access_key='{creds['SECRET_KEY']}';")
    return con

try:
    db = get_connection()
except Exception as e:
    st.error(f"Cloud Connection Error: {e}")

CSV_FILE = "s3://compra-agil-data/CA_2025.csv"
DATA_SOURCE = f"read_csv('{CSV_FILE}', delim=';', header=True, encoding='cp1252', ignore_errors=True)"

# --- 4. SIDEBAR & FILTERS ---
st.sidebar.header("Global Slicers")
date_range = st.sidebar.date_input("Analysis Period", value=(datetime(2025, 1, 1), datetime(2025, 12, 31)))
regions = ["All Regions", "Region Metropolitana de Santiago", "Region de Antofagasta", "Region de Valparaiso", "Region del Biobio"]
target_region = st.sidebar.selectbox("Region", regions)
search_query = st.sidebar.text_input("Product Category", placeholder="Example: Medical")

st.sidebar.markdown("---") 
st.sidebar.markdown("### Internal Use Only")
st.sidebar.image("https://placehold.co/400x300/png?text=Market+Intelligence", use_container_width=True)

def apply_filters(base_sql):
    sql = base_sql
    if target_region != "All Regions":
        sql += f" AND RegionUnidadCompra = '{target_region}'"
    if search_query:
        sql += f" AND (RubroN1 ILIKE '%{search_query}%' OR DescripcionOC ILIKE '%{search_query}%')"
    if len(date_range) == 2:
        sql += f" AND FechaPublicacion BETWEEN '{date_range[0]}' AND '{date_range[1]}'"
    return sql

# --- 5. MAIN DASHBOARD CONTENT ---
st.markdown("<h1 style='text-align: center; text-shadow: 2px 2px 4px #000000;'>Ramp-Up: Market Intelligence</h1>", unsafe_allow_html=True)

tabs = st.tabs(["Market Summary", "Specialty Analysis", "Leaderboards", "Competitive Analysis", "Detail View"])

# Summary Tab
with tabs[0]:
    if st.button("Refresh Summary Data", type="primary"):
        res = db.execute(apply_filters(f"SELECT COUNT(*) as Total FROM {DATA_SOURCE} WHERE 1=1")).df()
        st.metric("Total Contracts Found", f"{res['Total'][0]:,}")
    
    dimension = st.radio("Group Results By:", ["RegionUnidadCompra", "Institucion", "Proveedor", "RubroN1"], index=3)
    if st.button("Generate Distribution Chart"):
        pivot_query = apply_filters(f"SELECT {dimension} as GroupName, COUNT(*) as Total FROM {DATA_SOURCE} WHERE 1=1") + " GROUP BY GroupName ORDER BY Total DESC LIMIT 15"
        df = db.execute(pivot_query).df()
        chart = px.bar(df, x='Total', y='GroupName', orientation='h', template="plotly_dark")
        st.plotly_chart(chart, use_container_width=True)

# Specialty Analysis Tab
with tabs[1]:
    st.header("Professional Specialty Distribution")
    spec_map = {"Psicologia": "Psicolo", "TENS": "TENS", "Enfermeria": "Enfermer", "Psiquiatria": "Psiquiatr"}
    if st.button("Analyze Professional Demand"):
        results = []
        for label, keyword in spec_map.items():
            query = apply_filters(f"SELECT COUNT(*) as Total FROM {DATA_SOURCE} WHERE (DescripcionOC ILIKE '%{keyword}%' OR NombreOC ILIKE '%{keyword}%')")
            count = db.execute(query).df()["Total"][0]
            results.append({"Specialty": label, "Count": count})
        st.dataframe(pd.DataFrame(results), use_container_width=True)

# Leaderboards Tab
with tabs[2]:
    if st.button("Load Leaderboards"):
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Top Purchasing Institutions**")
            st.dataframe(db.execute(apply_filters(f"SELECT Institucion, COUNT(*) as Buys FROM {DATA_SOURCE} WHERE 1=1") + " GROUP BY Institucion ORDER BY Buys DESC LIMIT 10").df(), use_container_width=True)
        with col2:
            st.write("**Top Suppliers**")
            st.dataframe(db.execute(apply_filters(f"SELECT Proveedor, COUNT(*) as Wins FROM {DATA_SOURCE} WHERE 1=1") + " GROUP BY Proveedor ORDER BY Wins DESC LIMIT 10").df(), use_container_width=True)

# Detail View
with tabs[4]:
    if st.button("Load Detailed Records"):
        df_view = db.execute(apply_filters(f"SELECT codigoOC, NombreOC, Proveedor FROM {DATA_SOURCE} WHERE 1=1") + " LIMIT 100").df()
        st.dataframe(df_view, use_container_width=True)
