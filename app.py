import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import random

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Ramp-Up: Intelligence Dashboard", 
    layout="wide",
    initial_sidebar_state="expanded" 
)

# --- PROFESSIONAL UI DESIGN (Aggressive Cleanup) ---
def apply_professional_styles():
    bg_url = "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072&auto=format&fit=crop"
    st.markdown(
         f"""
         <style>
         /* Background and Base Text */
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

         /* SURGICAL BUTTON REMOVAL */
         /* This hides the entire top-right toolbar container specifically */
         [data-testid="stHeaderActionElements"] {{
             display: none !important;
         }}
         
         /* Hide the colored line at the top */
         [data-testid="stDecoration"] {{
             display: none !important;
         }}

         /* General UI Cleanup */
         .stDeployButton {{ display: none !important; }}
         footer {{ visibility: hidden !important; }}
         
         /* Transparent Header */
         header[data-testid="stHeader"] {{
             background-color: rgba(0,0,0,0) !important;
         }}
         </style>
         """,
         unsafe_allow_html=True
     )

apply_professional_styles()

# --- SECURITY GATE ---
def validate_access():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if st.session_state.authenticated:
        return True

    st.markdown("<h1 style='text-align: center;'>Ramp-Up Intelligence</h1>", unsafe_allow_html=True)
    
    left, mid, right = st.columns([1, 2, 1])
    with mid:
        code = st.text_input("Access Code", type="password")
        if code:
            # Fallback to default if secrets are not configured
            valid_code = st.secrets.get("GENERAL", {}).get("APP_PASSWORD", "licitakiller2025")
            if code == valid_code:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Access Denied")
    return False

if not validate_access():
    st.stop()

# --- DATA INFRASTRUCTURE ---
@st.cache_resource
def connect_to_storage():
    try:
        creds = st.secrets["R2"]
        con = duckdb.connect(database=':memory:')
        con.execute("INSTALL httpfs; LOAD httpfs;")
        con.execute(f"""
            SET s3_region='auto';
            SET s3_endpoint='{creds["ACCOUNT_ID"]}.r2.cloudflarestorage.com';
            SET s3_access_key_id='{creds["ACCESS_KEY"]}';
            SET s3_secret_access_key='{creds["SECRET_KEY"]}';
        """)
        return con
    except Exception as e:
        st.error(f"Storage Connection Error: {e}")
        return None

db = connect_to_storage()
DATA_SOURCE = "read_csv('s3://compra-agil-data/CA_2025.csv', delim=';', header=True, encoding='cp1252', ignore_errors=True)"

# --- FILTERS AND NAVIGATION ---
st.sidebar.header("Global Slicers")
regions = [
    "All Regions", "Region Metropolitana de Santiago", "Region de Antofagasta", 
    "Region de Arica y Parinacota", "Region de Atacama", 
    "Region de Aysen del General Carlos Ibanez del Campo", "Region de Coquimbo", 
    "Region de La Araucania", "Region de Los Lagos", "Region de Los Rios", 
    "Region de Magallanes y de la Antartica Chilena", "Region de Tarapaca", 
    "Region de Valparaiso", "Region del Biobio", 
    "Region del Libertador General Bernardo O'Higgins", "Region del Maule", "Region del Nuble"
]
target_region = st.sidebar.selectbox("Region", regions)
search_query = st.sidebar.text_input("Product Category", placeholder="Example: Software")

st.sidebar.markdown("---")
st.sidebar.markdown("### Internal Use Only")
st.sidebar.image("https://placehold.co/400x300/png?text=Market+Intelligence", use_container_width=True)

# --- MAIN DASHBOARD ---
st.markdown("<h1 style='text-align: center;'>Ramp-Up: Market Intelligence</h1>", unsafe_allow_html=True)

def build_filtered_query(base_sql):
    query = base_sql
    if target_region != "All Regions":
        query += f" AND RegionUnidadCompra = '{target_region}'"
    if search_query:
        query += f" AND (RubroN1 ILIKE '%{search_query}%' OR DescripcionOC ILIKE '%{search_query}%')"
    return query

t1, t2, t3 = st.tabs(["Market Summary", "Performance Analytics", "Data Records"])

with t1:
    if st.button("Refresh Dashboard", type="primary"):
        count_sql = build_filtered_query(f"SELECT COUNT(*) as Total FROM {DATA_SOURCE} WHERE 1=1")
        res = db.execute(count_sql).df()
        st.metric("Total Contracts Identified", f"{res['Total'][0]:,}")
    
    st.divider()
    l_col, r_col = st.columns([1, 3])
    with l_col:
        grouping = st.radio("Group By:", ["RegionUnidadCompra", "Institucion", "Proveedor", "RubroN1"], index=3)
    with r_col:
        if st.button("Execute Distribution Analysis"):
            pivot_sql = build_filtered_query(f"SELECT {grouping} as GroupName, COUNT(*) as Total FROM {DATA_SOURCE} WHERE 1=1") + f" GROUP BY GroupName ORDER BY Total DESC LIMIT 15"
            df = db.execute(pivot_sql).df()
            chart = px.bar(df, x='Total', y='GroupName', orientation='h', color='Total', template="plotly_dark")
            chart.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(chart, use_container_width=True)

with t2:
    if st.button("Generate Performance Tables"):
        c1, c2 = st.columns(2)
        with c1:
            st.write("**Top Suppliers**")
            sup_sql = build_filtered_query(f"SELECT Proveedor, COUNT(*) as Wins FROM {DATA_SOURCE} WHERE 1=1") + " GROUP BY Proveedor ORDER BY Wins DESC LIMIT 10"
            st.dataframe(db.execute(sup_sql).df())
        with c2:
            st.write("**Top Institutions**")
            ins_sql = build_filtered_query(f"SELECT Institucion, COUNT(*) as Buys FROM {DATA_SOURCE} WHERE 1=1") + " GROUP BY Institucion ORDER BY Buys DESC LIMIT 10"
            st.dataframe(db.execute(ins_sql).df())

with t3:
    count = st.slider("Record Limit", 10, 500, 50)
    if st.button("Fetch Detail View"):
        detail_sql = build_filtered_query(f"SELECT codigoOC, NombreOC, DescripcionOC FROM {DATA_SOURCE} WHERE 1=1") + f" LIMIT {count}"
        st.dataframe(db.execute(detail_sql).df())
