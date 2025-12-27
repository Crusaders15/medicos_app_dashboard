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

# --- 2. THE DESIGN FUNCTION (This is what you couldn't find!) ---
def apply_custom_ui():
    bg_url = "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072&auto=format&fit=crop"
    st.markdown(
         f"""
         <style>
         /* DEEP DARK BACKGROUND (96% Dark Overlay for Eye Comfort) */
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
         
         /* HIDE PLATFORM BUTTONS (Share, Star, GitHub) */
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

# Call the function to apply the design
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
DATA_SOURCE = "read_csv('s3://compra-agil-data/CA_2025.csv', delim=';', header=True, encoding='cp1252', ignore_errors=True)"

# --- 5. SIDEBAR, FILTERS & MEMES ---
st.sidebar.header("Global Slicers")
date_range = st.sidebar.date_input("Analysis Period", value=(datetime(2025, 1, 1), datetime(2025, 12, 31)))
target_region = st.sidebar.selectbox("Region", ["All Regions", "Region Metropolitana de Santiago", "Region de Antofagasta", "Region de Valparaiso", "Region del Biobio"])

# --- MEME INTEGRATION ---
# REPLACE the URL below with your 'Public Development URL' from R2 Settings
base_url = "https://pub-your-id.r2.dev" 

meme_playlist = [
    f"{base_url}/Memes/Drake%20Meme.jpg",
    f"{base_url}/Memes/Drake%20Meme%20afwt2v.jpg",
    f"{base_url}/Memes/Drake%20meme%20afwt19.jpg"
]

with st.sidebar:
    st.markdown("---")
    st.markdown("### Internal Use Only")
    # Randomly picks one of your R2 memes
    st.image(random.choice(meme_playlist), use_container_width=True)

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

# Other tabs remain functional as in previous versions...
