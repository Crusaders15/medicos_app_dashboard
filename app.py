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

# --- DARK MODE UI DESIGN ---
def set_design():
    bg_url = "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072&auto=format&fit=crop"
    st.markdown(
         f"""
         <style>
         /* 1. Deep Dark Background */
         .stApp {{
             background-image: url("{bg_url}");
             background-attachment: fixed;
             background-size: cover;
             background-color: rgba(10, 10, 20, 0.92); /* Darker overlay for eye comfort */
             background-blend-mode: darken;
         }}
         
         /* 2. Soft White Text (Reduces Glare) */
         .stMarkdown, .stText, h1, h2, h3, h4, h5, h6, p, li, span, label, div {{
             color: #e0e0e0 !important;
         }}
         
         /* 3. Deep Charcoal Sidebar */
         section[data-testid="stSidebar"] {{
             background-color: rgba(5, 5, 10, 0.85) !important;
         }}

         /* 4. Muted Tabs & Buttons */
         .stTabs [data-baseweb="tab-list"] {{
             background-color: transparent;
         }}
         .stTabs [data-baseweb="tab"] {{
             color: #999999 !important;
         }}
         .stTabs [aria-selected="true"] {{
             color: #ffffff !important;
             border-bottom-color: #ffffff !important;
         }}

         /* 5. Toolbars & Cleanup */
         div[data-testid="stToolbarActions"], 
         .stToolbarActions,
         div[data-testid="stToolbar"] {{
             display: none !important;
         }}
         header[data-testid="stHeader"] {{ background-color: rgba(0,0,0,0) !important; }}
         .stDeployButton {{ display: none !important; }}
         footer {{ visibility: hidden !important; }}
         [data-testid="stDecoration"] {{ display: none !important; }}
         [data-testid="stSidebarCollapsedControl"] {{ color: #ffffff !important; }}
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
        if pwd_input == st.secrets.get("GENERAL", {}).get("APP_PASSWORD", "licitakiller2025"):
            st.session_state.password_correct = True
            st.rerun()
    return False

if not check_password():
    st.stop() 

# --- DATA CONNECTION ---
@st.cache_resource
def get_connection():
    creds = st.secrets["R2"]
    con = duckdb.connect(database=':memory:')
    con.execute("INSTALL httpfs; LOAD httpfs;")
    con.execute(f"SET s3_region='auto'; SET s3_endpoint='{creds['ACCOUNT_ID']}.r2.cloudflarestorage.com'; SET s3_access_key_id='{creds['ACCESS_KEY']}'; SET s3_secret_access_key='{creds['SECRET_KEY']}';")
    return con

db = get_connection()
DATA_SOURCE = "read_csv('s3://compra-agil-data/CA_2025.csv', delim=';', header=True, encoding='cp1252', ignore_errors=True)"

# --- SIDEBAR & FILTERS ---
st.sidebar.header("Global Slicers")
date_range = st.sidebar.date_input("Analysis Period", value=(datetime(2025, 1, 1), datetime(2025, 12, 31)))
regions = ["All Regions", "Region Metropolitana de Santiago", "Region de Antofagasta", "Region de Valparaiso", "Region del Biobio", "Region del Maule"]
target_region = st.sidebar.selectbox("Region", regions)
search_query = st.sidebar.text_input("Product Category", placeholder="Example: Software")

st.sidebar.markdown("---") 
st.sidebar.markdown("### Internal Use Only")

# --- MEME PLAYLIST (This is where you will add your links!) ---
meme_playlist = [
    "https://placehold.co/400x300/1a1a1a/ffffff/png?text=Market+Intelligence",
    "https://placehold.co/400x300/1a1a1a/ffffff/png?text=Target+Analysis",
    "https://placehold.co/400x300/1a1a1a/ffffff/png?text=Opportunity+Report"
]
st.sidebar.image(random.choice(meme_playlist), use_container_width=True)

# --- DASHBOARD CONTENT ---
st.markdown("<h1 style='text-align: center; text-shadow: 2px 2px 4px #000000;'>Ramp-Up: Market Intelligence</h1>", unsafe_allow_html=True)

def apply_filters(base_sql):
    sql = base_sql
    if target_region != "All Regions":
        sql += f" AND RegionUnidadCompra = '{target_region}'"
    if search_query:
        sql += f" AND (RubroN1 ILIKE '%{search_query}%' OR DescripcionOC ILIKE '%{search_query}%')"
    if len(date_range) == 2:
        sql += f" AND FechaPublicacion BETWEEN '{date_range[0]}' AND '{date_range[1]}'"
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
    specialty_map = {"Psicologia": "Psicolo", "Psiquiatria": "Psiquiatr", "Neurologia": "Neurolo", "TENS": "TENS", "Enfermeria": "Enfermer"}
    if st.button("Analyze Professional Demand"):
        results = []
        for label, keyword in specialty_map.items():
            query = apply_filters(f"SELECT COUNT(*) as Total FROM {DATA_SOURCE} WHERE (DescripcionOC ILIKE '%{keyword}%' OR NombreOC ILIKE '%{keyword}%')")
            count = db.execute(query).df()["Total"][0]
            results.append({"Specialty": label, "Count": count})
        df_spec = pd.DataFrame(results)
        c_pie, c_tab = st.columns(2)
        with c_pie:
            fig_p = px.pie(df_spec, values='Count', names='Specialty', hole=.4, template="plotly_dark")
            fig_p.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_p, use_container_width=True)
        with c_tab:
            st.dataframe(df_spec, use_container_width=True)

# --- TAB 3: LEADERBOARDS ---
with t3:
    s_filter = st.text_input("Filter by Supplier Name", placeholder="Search...")
    if st.button("Load Analytics"):
        c1, c2 = st.columns(2)
        with c1:
            st.write("**Top Suppliers**")
            sql = f"SELECT Proveedor, COUNT(*) as Wins FROM {DATA_SOURCE} WHERE 1=1"
            if s_filter: sql += f" AND Proveedor ILIKE '%{s_filter}%'"
            st.dataframe(db.execute(apply_filters(sql) + " GROUP BY Proveedor ORDER BY Wins DESC LIMIT 10").df(), use_container_width=True)
        with c2:
            st.write("**Top Purchasing Institutions**")
            st.dataframe(db.execute(apply_filters(f"SELECT Institucion, COUNT(*) as Buys FROM {DATA_SOURCE} WHERE 1=1") + " GROUP BY Institucion ORDER BY Buys DESC LIMIT 10").df(), use_container_width=True)

# --- TAB 4: COMPETITIVE ANALYSIS ---
with t4:
    ca, cb = st.columns(2)
    with ca: c1 = st.text_input("First Supplier", value="Proveedor A")
    with cb: c2 = st.text_input("Second Supplier", value="Proveedor B")
    if st.button("Compare Market Performance"):
        sql = apply_filters(f"SELECT Proveedor, COUNT(*) as Contracts FROM {DATA_SOURCE} WHERE (Proveedor ILIKE '%{c1}%' OR Proveedor ILIKE '%{c2}%') GROUP BY Proveedor")
        df_c = db.execute(sql).df()
        if not df_c.empty:
            fig_c = px.pie(df_c, values='Contracts', names='Proveedor', hole=.4, template="plotly_dark")
            fig_c.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_c, use_container_width=True)
        else:
            st.warning("No data found for these suppliers.")

# --- TAB 5: DETAIL VIEW ---
with t5:
    limit = st.slider("Record Limit", 10, 1000, 100)
    if st.button("Load Detailed Records"):
        df_v = db.execute(apply_filters(f"SELECT codigoOC, NombreOC, DescripcionOC, RegionUnidadCompra, Proveedor FROM {DATA_SOURCE} WHERE 1=1") + f" LIMIT {limit}").df()
        st.dataframe(df_v, use_container_width=True)
        out = io.BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as w:
            df_v.to_excel(w, index=False)
        st.download_button("Export to Excel", data=out.getvalue(), file_name="market_data.xlsx")
