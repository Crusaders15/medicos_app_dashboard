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

         /* SURGICAL BUTTON REMOVAL */
         div[data-testid="stToolbarActions"], 
         .stToolbarActions,
         div[data-testid="stToolbar"] {{
             display: none !important;
             visibility: hidden !important;
         }}

         header[data-testid="stHeader"] {{
             background-color: rgba(0,0,0,0) !important;
         }}

         .stDeployButton {{ display: none !important; }}
         footer {{ visibility: hidden !important; }}
         [data-testid="stDecoration"] {{ display: none !important; }}
         
         /* Ensure Sidebar toggle is white and always visible */
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
            secret_pwd = st.secrets.get("GENERAL", {}).get("APP_PASSWORD", "licitakiller2025")
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

try:
    db = get_connection()
except Exception as e:
    st.error(f"Connection Failed: {e}")

CSV_FILE = "s3://compra-agil-data/CA_2025.csv"
DATA_SOURCE = f"read_csv('{CSV_FILE}', delim=';', header=True, encoding='cp1252', ignore_errors=True)"

# --- SIDEBAR & FILTERS ---
st.sidebar.header("Global Slicers")

# Date Range Slicer
st.sidebar.subheader("Analysis Period")
date_range = st.sidebar.date_input(
    "Select Date Range",
    value=(datetime(2025, 1, 1), datetime(2025, 12, 31)),
    min_value=datetime(2024, 1, 1),
    max_value=datetime(2026, 12, 31)
)

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

# --- DASHBOARD CONTENT ---
st.markdown("<h1 style='text-align: center; text-shadow: 2px 2px 4px #000000;'>Ramp-Up: Market Intelligence</h1>", unsafe_allow_html=True)

def apply_filters(base_sql):
    sql = base_sql
    if target_region != "All Regions":
        sql += f" AND RegionUnidadCompra = '{target_region}'"
    if search_query:
        sql += f" AND (RubroN1 ILIKE '%{search_query}%' OR DescripcionOC ILIKE '%{search_query}%')"
    if len(date_range) == 2:
        start_date, end_date = date_range
        sql += f" AND FechaPublicacion BETWEEN '{start_date}' AND '{end_date}'"
    return sql

t1, t2, t3, t4, t5 = st.tabs(["Market Summary", "Specialty Analysis", "Leaderboards", "Competitive Analysis", "Detail View"])

# --- TAB 1: SUMMARY ---
with t1:
    if st.button("Refresh Summary Data", type="primary"):
        res = db.execute(apply_filters(f"SELECT COUNT(*) as Total FROM {DATA_SOURCE} WHERE 1=1")).df()
        st.metric("Total Contracts Found", f"{res['Total'][0]:,}")
    
    st.divider()
    l_col, r_col = st.columns([1, 3])
    with l_col:
        dimension = st.radio("Group Results By:", ["RegionUnidadCompra", "Institucion", "Proveedor", "RubroN1"], index=3)
    with r_col:
        if st.button("Generate Distribution Chart"):
            pivot_query = apply_filters(f"SELECT {dimension} as GroupName, COUNT(*) as Total FROM {DATA_SOURCE} WHERE 1=1") + f" GROUP BY GroupName ORDER BY Total DESC LIMIT 15"
            df = db.execute(pivot_query).df()
            chart = px.bar(df, x='Total', y='GroupName', orientation='h', color='Total', template="plotly_dark")
            chart.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(chart, use_container_width=True)

# --- TAB 2: SPECIALTY ANALYSIS ---
with t2:
    st.header("Professional Specialty Distribution")
    specialty_map = {
        "Psicologia": "Psicolo",
        "Psiquiatria": "Psiquiatr",
        "Neurologia": "Neurolo",
        "TENS": "TENS",
        "Enfermeria": "Enfermer"
    }
    
    if st.button("Analyze Professional Demand"):
        results = []
        for label, keyword in specialty_map.items():
            query = apply_filters(f"SELECT COUNT(*) as Total FROM {DATA_SOURCE} WHERE (DescripcionOC ILIKE '%{keyword}%' OR NombreOC ILIKE '%{keyword}%')")
            count = db.execute(query).df()["Total"][0]
            results.append({"Specialty": label, "Count": count})
        
        df_spec = pd.DataFrame(results)
        col_pie, col_tab = st.columns(2)
        with col_pie:
            fig_pie = px.pie(df_spec, values='Count', names='Specialty', title="Professional Demand Breakdown", hole=.4, template="plotly_dark")
            fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_pie, use_container_width=True)
        with col_tab:
            st.write("**Counts by Specialty**")
            st.dataframe(df_spec, use_container_width=True)

# --- TAB 3: LEADERBOARDS ---
with t3:
    st.markdown("### Performance Leaderboards")
    supplier_filter = st.text_input("Filter by Supplier Name", placeholder="Search...")
    if st.button("Load Analytics"):
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Top Suppliers**")
            sup_sql = f"SELECT Proveedor, COUNT(*) as Wins FROM {DATA_SOURCE} WHERE 1=1"
            if supplier_filter: sup_sql += f" AND Proveedor ILIKE '%{supplier_filter}%'"
            st.dataframe(db.execute(apply_filters(sup_sql) + " GROUP BY Proveedor ORDER BY Wins DESC LIMIT 10").df(), use_container_width=True)
        with col2:
            st.write("**Top Purchasing Institutions**")
            st.dataframe(db.execute(apply_filters(f"SELECT Institucion, COUNT(*) as Buys FROM {DATA_SOURCE} WHERE 1=1") + " GROUP BY Institucion ORDER BY Buys DESC LIMIT 10").df(), use_container_width=True)

# --- TAB 4: COMPETITIVE ANALYSIS ---
with t4:
    st.markdown("### Supplier Head-to-Head")
    col_a, col_b = st.columns(2)
    with col_a:
        comp_1 = st.text_input("First Supplier Name", value="Proveedor A")
    with col_b:
        comp_2 = st.text_input("Second Supplier Name", value="Proveedor B")
    
    if st.button("Compare Market Performance"):
        compare_sql = apply_filters(f"""
            SELECT Proveedor, COUNT(*) as Contracts 
            FROM {DATA_SOURCE} 
            WHERE (Proveedor ILIKE '%{comp_1}%' OR Proveedor ILIKE '%{comp_2}%')
            GROUP BY Proveedor
        """)
        df_comp = db.execute(compare_sql).df()
        if not df_comp.empty:
            fig_comp = px.pie(df_comp, values='Contracts', names='Proveedor', title="Market Share Comparison", hole=.4, template="plotly_dark")
            fig_comp.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_comp, use_container_width=True)
            st.dataframe(df_comp, use_container_width=True)
        else:
            st.warning("No data found for the specified suppliers in this period.")

# --- TAB 5: DETAIL VIEW ---
with t5:
    limit = st.slider("Record Limit", 10, 1000, 100)
    if st.button("Load Detailed Records"):
        df_view = db.execute(apply_filters(f"SELECT codigoOC, NombreOC, DescripcionOC, RegionUnidadCompra, Proveedor FROM {DATA_SOURCE} WHERE 1=1") + f" LIMIT {limit}").df()
        st.dataframe(df_view, use_container_width=True)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_view.to_excel(writer, index=False, sheet_name='MarketData')
        st.download_button(label="Export Current View to Excel", data=output.getvalue(), file_name="rampup_market_data.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
