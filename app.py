import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import random
import io
from datetime import datetime

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Ramp-Up: Intelligence Dashboard", 
    layout="wide",
    initial_sidebar_state="expanded" 
)

# --- 2. THE DESIGN (Eye-Comfort Dark Mode) ---
def apply_custom_ui():
    bg_url = "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072&auto=format&fit=crop"
    st.markdown(
         f"""
         <style>
         /* DEEP DARK OVERLAY (Reduces Glare) */
         .stApp {{
             background-image: url("{bg_url}");
             background-attachment: fixed;
             background-size: cover;
             background-color: rgba(5, 5, 10, 0.96); 
             background-blend-mode: darken;
         }}
         
         /* SOFT TEXT COLOR (Reduces Eye Strain) */
         .stMarkdown, .stText, h1, h2, h3, h4, h5, h6, p, li, span, label, div {{
             color: #cfd8dc !important; 
         }}
         
         /* HIDE PLATFORM TOOLBARS */
         div[data-testid="stToolbarActions"], 
         .stToolbarActions,
         div[data-testid="stToolbar"] {{
             display: none !important;
         }}

         header[data-testid="stHeader"] {{ background-color: rgba(0,0,0,0) !important; }}
         .stDeployButton {{ display: none !important; }}
         footer {{ visibility: hidden !important; }}
         [data-testid="stDecoration"] {{ display: none !important; }}
         </style>
         """,
         unsafe_allow_html=True
     )

apply_custom_ui()

# --- 3. SECURITY ---
if "password_correct" not in st.session_state:
    st.session_state.password_correct = False

if not st.session_state.password_correct:
    st.markdown("<h1 style='text-align: center;'>Ramp-Up Intelligence</h1>", unsafe_allow_html=True)
    pwd = st.text_input("Access Code", type="password")
    if pwd == st.secrets.get("GENERAL", {}).get("APP_PASSWORD", "licitakiller2025"):
        st.session_state.password_correct = True
        st.rerun()
    st.stop()

# --- 4. DATA CONNECTION ---
@st.cache_resource
def get_db():
    creds = st.secrets["R2"]
    con = duckdb.connect(database=':memory:')
    con.execute("INSTALL httpfs; LOAD httpfs;")
    con.execute(f"SET s3_region='auto'; SET s3_endpoint='{creds['ACCOUNT_ID']}.r2.cloudflarestorage.com'; SET s3_access_key_id='{creds['ACCESS_KEY']}'; SET s3_secret_access_key='{creds['SECRET_KEY']}';")
    return con

db = get_db()
# Using the CSV in your bucket
DATA_SOURCE = "read_csv('s3://compra-agil-data/CA_2025.csv', delim=';', header=True, encoding='cp1252', ignore_errors=True)"

# --- 5. SIDEBAR & MEME INTEGRATION ---
st.sidebar.header("Global Slicers")

# Your actual R2 Public URL
base_url = "https://pub-a626d3085678426eae26e41ff821191f.r2.dev" 

# File names taken from your R2 'Memes' folder
meme_playlist = [
    f"{base_url}/Memes/Drake%20Meme.jpg",
    f"{base_url}/Memes/Drake%20Meme%20afwt2v.jpg",
    f"{base_url}/Memes/Drake%20meme%20afwt19.jpg"
]

# Slicers
date_range = st.sidebar.date_input("Analysis Period", value=(datetime(2025, 1, 1), datetime(2025, 12, 31)))
target_region = st.sidebar.selectbox("Region", ["All Regions", "Region Metropolitana de Santiago", "Region de Antofagasta", "Region de Valparaiso", "Region del Biobio"])

with st.sidebar:
    st.markdown("---")
    st.markdown("### Internal Use Only")
    # Randomly picks one of your R2 memes on refresh
    st.image(random.choice(meme_playlist), use_container_width=True)
    st.caption("Daily Motivation")

# --- 6. DASHBOARD CONTENT ---
st.markdown("<h1 style='text-align: center;'>Ramp-Up: Market Intelligence</h1>", unsafe_allow_html=True)

def apply_filters(base_sql):
    sql = base_sql
    if target_region != "All Regions":
        sql += f" AND RegionUnidadCompra = '{target_region}'"
    if len(date_range) == 2:
        sql += f" AND FechaPublicacion BETWEEN '{date_range[0]}' AND '{date_range[1]}'"
    return sql

tabs = st.tabs(["Market Summary", "Specialty Analysis", "Leaderboards", "Competitive Analysis", "Detail View"])

# Summary Tab
with tabs[0]:
    if st.button("Refresh Summary Data", type="primary"):
        res = db.execute(apply_filters(f"SELECT COUNT(*) as Total FROM {DATA_SOURCE} WHERE 1=1")).df()
        st.metric("Total Contracts Found", f"{res['Total'][0]:,}")

# Specialty Tab (Felipe's Request)
with tabs[1]:
    st.header("Professional Specialty Distribution")
    spec_map = {"Psicologia": "Psicolo", "TENS": "TENS", "Enfermeria": "Enfermer"}
    if st.button("Analyze Professional Demand"):
        results = [{"Specialty": k, "Count": db.execute(apply_filters(f"SELECT COUNT(*) FROM {DATA_SOURCE} WHERE DescripcionOC ILIKE '%{v}%'")).df().iloc[0,0]} for k, v in spec_map.items()]
        st.bar_chart(pd.DataFrame(results).set_index("Specialty"))

# Leaderboards
with tabs[2]:
    st.markdown("### Top Awarded")
    if st.button("Load Leaderboards"):
        sql = apply_filters(f"SELECT Proveedor, COUNT(*) as Wins FROM {DATA_SOURCE} WHERE 1=1") + " GROUP BY Proveedor ORDER BY Wins DESC LIMIT 10"
        st.dataframe(db.execute(sql).df(), use_container_width=True)

# Detail View & Excel
with tabs[4]:
    if st.button("Load Records"):
        df_v = db.execute(apply_filters(f"SELECT codigoOC, NombreOC, DescripcionOC FROM {DATA_SOURCE} WHERE 1=1") + " LIMIT 100").df()
        st.dataframe(df_v, use_container_width=True)
        out = io.BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as w:
            df_v.to_excel(w, index=False)
        st.download_button("Export to Excel", data=out.getvalue(), file_name="market_data.xlsx")
