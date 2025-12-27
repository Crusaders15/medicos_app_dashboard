import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import random
import io
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Ramp-Up: Intelligence Dashboard", 
    layout="wide",
    initial_sidebar_state="expanded" 
)

# --- PROFESSIONAL UI DESIGN (THE NUCLEAR FIX) ---
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

         /* THE SNIPER KILL: Targets exactly what you saw in DevTools */
         div[data-testid="stToolbarActions"], 
         .stToolbarActions,
         div[data-testid="stToolbar"],
         .st-emotion-cache-1p1m4ay {{
             display: none !important;
             visibility: hidden !important;
         }}

         /* Ensure header is transparent but exists for the arrow */
         header[data-testid="stHeader"] {{
             background-color: rgba(0,0,0,0) !important;
         }}

         .stDeployButton {{ display: none !important; }}
         footer {{ visibility: hidden !important; }}
         [data-testid="stDecoration"] {{ display: none !important; }}
         
         /* Force Sidebar arrow to stay white and visible */
         [data-testid="stSidebarCollapsedControl"] {{
             display: block !important;
             color: white !important;
             z-index: 100000 !important;
         }}
         </style>
         """,
         unsafe_allow_html=True
     )
set_design()

# --- SECURITY SYSTEM ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
    if st.session_state.password_correct:
        return True

    st.markdown("<h1 style='text-align: center;'>Ramp-Up Intelligence</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        pwd_input = st.text_input("Access Code", type="password")
        if pwd_input:
            secret_pwd = st.secrets.get("GENERAL", {}).get("APP_PASSWORD", "BichoGordito@15!")
            if pwd_input == secret_pwd:
                st.session_state.password_correct = True
                st.rerun()  
            else:
                st.error("Access Denied")
    return False

if not check_password():
    st.stop() 

# --- DATA CONNECTION ---
@st.cache_resource
def get_connection():
    aws_access_key_id = st.secrets["R2"]["ACCESS_KEY"]
    aws_secret_access_key = st.secrets["R2"]["SECRET_KEY"]
    account_id = st.secrets["R2"]["ACCOUNT_ID"]
    con = duckdb.connect(database=':memory:')
    con.execute("INSTALL httpfs; LOAD httpfs;")
    con.execute(f"""
        SET s3_region='auto';
        SET s3_endpoint='{account_id}.r2.cloudflarestorage.com';
        SET s3_access_key_id='{aws_access_key_id}';
        SET s3_secret_access_key='{aws_secret_access_key}';
    """)
    return con

try:
    con = get_connection()
except Exception as e:
    st.error(f"Connection Failed: {e}")

CSV_FILE = "s3://compra-agil-data/CA_2025.csv"
# Assuming the date column in your CSV is named 'FechaPublicacion'
REMOTE_TABLE = f"read_csv('{CSV_FILE}', delim=';', header=True, encoding='cp1252', ignore_errors=True)"

# --- SIDEBAR & FILTERS ---
st.sidebar.header("Global Slicers")

# 1. New Date Range Slicer
st.sidebar.subheader("Analysis Period")
date_range = st.sidebar.date_input(
    "Select Date Range",
    value=(datetime(2025, 1, 1), datetime(2025, 12, 31)),
    min_value=datetime(2024, 1, 1),
    max_value=datetime(2026, 12, 31)
)

# 2. Existing Filters
region_options = [
    "All Regions", "Region Metropolitana de Santiago", "Region de Antofagasta", 
    "Region de Arica y Parinacota", "Region de Atacama", 
    "Region de Aysen del General Carlos Ibanez del Campo", "Region de Coquimbo", 
    "Region de La Araucania", "Region de Los Lagos", "Region de Los Rios", 
    "Region de Magallanes y de la Antartica Chilena", "Region de Tarapaca", 
    "Region de Valparaiso", "Region del Biobio", 
    "Region del Libertador General Bernardo O'Higgins", "Region del Maule", "Region del Nuble"
]
selected_region = st.sidebar.selectbox("Region", region_options)
selected_keyword = st.sidebar.text_input("Product Category", placeholder="Example: Software")

st.sidebar.markdown("---") 
st.sidebar.markdown("### Internal Use Only")
st.sidebar.image("https://placehold.co/400x300/png?text=Market+Intelligence", use_container_width=True)

# --- DASHBOARD CONTENT ---
st.markdown("<h1 style='text-align: center; text-shadow: 2px 2px 4px #000000;'>Ramp-Up: Interactive Intelligence</h1>", unsafe_allow_html=True)

def apply_filters(base_sql):
    sql = base_sql
    if selected_region != "All Regions":
        sql += f" AND RegionUnidadCompra = '{selected_region}'"
    if selected_keyword:
        sql += f" AND (RubroN1 ILIKE '%{selected_keyword}%' OR DescripcionOC ILIKE '%{selected_keyword}%')"
    
    # Apply Date Filter (assuming column 'FechaPublicacion')
    if len(date_range) == 2:
        start_date, end_date = date_range
        # Note: adjust column name if different in your CSV
        sql += f" AND FechaPublicacion BETWEEN '{start_date}' AND '{end_date}'"
        
    return sql

tab1, tab2, tab3 = st.tabs(["Market Summary", "Performance Leaderboards", "Detail View"])

with tab1:
    if st.button("Refresh Summary Data", type="primary"):
        sql = apply_filters(f"SELECT COUNT(*) as Total FROM {REMOTE_TABLE} WHERE 1=1")
        df = con.execute(sql).df()
        st.metric("Total Contracts Found", f"{df['Total'][0]:,}")
    
    st.divider()
    col_group, col_viz = st.columns([1, 3])
    with col_group:
        dimension = st.radio("Group Results By:", ["RegionUnidadCompra", "Institucion", "Proveedor", "RubroN1"], index=3)
    with col_viz:
        if st.button("Generate Distribution Chart"):
            final_query = apply_filters(f"SELECT {dimension} as GroupName, COUNT(*) as Total FROM {REMOTE_TABLE} WHERE 1=1") + f" GROUP BY GroupName ORDER BY Total DESC LIMIT 15"
            df_pivot = con.execute(final_query).df()
            fig = px.bar(df_pivot, x='Total', y='GroupName', orientation='h', color='Total', template="plotly_dark")
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.markdown("### Performance Leaderboards")
    supplier_search = st.text_input("Filter Leaderboards by Supplier Name", placeholder="Enter supplier name...")
    
    if st.button("Load Analytics"):
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Top Suppliers**")
            sup_sql = f"SELECT Proveedor, COUNT(*) as Wins FROM {REMOTE_TABLE} WHERE 1=1"
            if supplier_search:
                sup_sql += f" AND Proveedor ILIKE '%{supplier_search}%'"
            sup_sql = apply_filters(sup_sql) + " GROUP BY Proveedor ORDER BY Wins DESC LIMIT 10"
            st.dataframe(con.execute(sup_sql).df(), use_container_width=True)
        with col2:
            st.write("**Top Purchasing Institutions**")
            ins_sql = apply_filters(f"SELECT Institucion, COUNT(*) as Buys FROM {REMOTE_TABLE} WHERE 1=1") + " GROUP BY Institucion ORDER BY Buys DESC LIMIT 10"
            st.dataframe(con.execute(ins_sql).df(), use_container_width=True)

with tab3:
    row_count = st.slider("Record Limit", 10, 1000, 100)
    if st.button("Load Detailed Records"):
        df_details = con.execute(apply_filters(f"SELECT codigoOC, NombreOC, DescripcionOC, RegionUnidadCompra, Proveedor FROM {REMOTE_TABLE} WHERE 1=1") + f" LIMIT {row_count}").df()
        st.dataframe(df_details, use_container_width=True)
        
        # EXCEL EXPORT
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_details.to_excel(writer, index=False, sheet_name='MarketData')
        processed_data = output.getvalue()
        
        st.download_button(
            label="Export Current View to Excel",
            data=processed_data,
            file_name="rampup_market_intelligence.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

