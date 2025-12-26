import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px

# --- PAGE CONFIG ---
st.set_page_config(page_title="Ramp-Up: Intelligence Dashboard", layout="wide")

# --- CSS MAGIC (Background) 🎨 ---
def set_background_image():
    bg_url = "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072&auto=format&fit=crop"
    st.markdown(
         f"""
         <style>
         .stApp {{
             background-image: url("{bg_url}");
             background-attachment: fixed;
             background-size: cover;
             background-color: rgba(0,0,0,0.8);
             background-blend-mode: darken;
         }}
         [data-testid="stHeader"] {{ background-color: rgba(0,0,0,0.0); }}
         /* Make sidebar semi-transparent */
         section[data-testid="stSidebar"] {{
             background-color: rgba(0, 0, 0, 0.5);
         }}
         </style>
         """,
         unsafe_allow_html=True
     )
set_background_image()

st.markdown("<h1 style='text-align: center; color: white;'>🚀 Ramp-Up: Interactive Intelligence</h1>", unsafe_allow_html=True)

# --- CONNECT TO DATA (R2) ---
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

# --- SOURCE DEFINITION ---
CSV_FILE = "s3://compra-agil-data/CA_2025.csv"
REMOTE_TABLE = f"read_csv('{CSV_FILE}', delim=';', header=True, encoding='cp1252', ignore_errors=True)"

# ==========================================
# 🧠 THE BRAIN: GLOBAL FILTERS (SIDEBAR)
# ==========================================
st.sidebar.header("🔍 Global Slicers")
st.sidebar.info("Adjust these filters to slice the entire dashboard.")

# 1. Region Slicer
# (We hardcode the list for speed, querying 2GB for this list every time is slow)
region_options = ["All Regions", "Region Metropolitana de Santiago", "Region de Valparaiso", "Region del Biobio", "Region de Antofagasta", "Region de La Araucania", "Region de Los Lagos"]
selected_region = st.sidebar.selectbox("📍 Region", region_options)

# 2. Category Keyword Slicer
selected_keyword = st.sidebar.text_input("📦 Category/Product (Keyword)", placeholder="e.g. Computacion")

# --- QUERY BUILDER FUNCTION ---
# This function injects the sidebar filters into ANY query we write below
def apply_filters(base_sql):
    if selected_region != "All Regions":
        base_sql += f" AND RegionUnidadCompra = '{selected_region}'"
    if selected_keyword:
        base_sql += f" AND (RubroN1 ILIKE '%{selected_keyword}%' OR DescripcionOC ILIKE '%{selected_keyword}%')"
    return base_sql

# ==========================================
# 📊 THE TABS
# ==========================================
tab1, tab2, tab3 = st.tabs(["🧮 Super Pivot (New!)", "🏆 Leaderboards", "🕵️ Detail Detective"])

# === TAB 1: SUPER PIVOT (The Excel Killer) ===
with tab1:
    st.markdown("### 🧮 Slice & Dice")
    st.caption("Group the data dynamically. No formulas needed.")
    
    col_group, col_viz = st.columns([1, 3])
    
    with col_group:
        st.markdown("**1. Group By:**")
        # Let the user choose the "Dimension"
        dimension = st.radio("Choose Axis:", 
                             ["RegionUnidadCompra", "Institucion", "Proveedor", "RubroN1"],
                             index=0)
        
        st.markdown("**2. Metric:**")
        # We stick to Count for now (Safest on raw CSV)
        metric_label = "Volume (Total Tenders)"
    
    with col_viz:
        # Build the Dynamic Query
        base_query = f"SELECT {dimension} as GroupName, COUNT(*) as Total FROM {REMOTE_TABLE} WHERE 1=1"
        filtered_query = apply_filters(base_query) # <--- MAGIC HAPPENS HERE
        final_query = filtered_query + " GROUP BY GroupName ORDER BY Total DESC LIMIT 15"
        
        with st.spinner("Pivoting data..."):
            df_pivot = con.execute(final_query).df()
            
            # Interactive Chart
            fig = px.bar(df_pivot, x='GroupName', y='Total', 
                         title=f"{metric_label} by {dimension}",
                         color='Total',
                         text_auto=True)
            fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)

# === TAB 2: LEADERBOARDS (Cross-Filtered) ===
with tab2:
    st.markdown(f"### 🏆 Top Players (Filtered: {selected_region})")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Top Suppliers**")
        sql_suppliers = f"SELECT Proveedor, COUNT(*) as Wins FROM {REMOTE_TABLE} WHERE 1=1"
        sql_suppliers = apply_filters(sql_suppliers) + " GROUP BY Proveedor ORDER BY Wins DESC LIMIT 10"
        
        df_supp = con.execute(sql_suppliers).df()
        st.dataframe(df_supp, use_container_width=True)
        
    with col2:
        st.markdown("**Top Buyers (Institutions)**")
        sql_buyers = f"SELECT Institucion, COUNT(*) as Buys FROM {REMOTE_TABLE} WHERE 1=1"
        sql_buyers = apply_filters(sql_buyers) + " GROUP BY Institucion ORDER BY Buys DESC LIMIT 10"
        
        df_buy = con.execute(sql_buyers).df()
        st.dataframe(df_buy, use_container_width=True)

# === TAB 3: DETAIL DETECTIVE ===
with tab3:
    st.markdown("### 🕵️ Deep Dive")
    st.write("This table shows the raw data matching your filters.")
    
    limit_slider = st.slider("Rows to show", 10, 1000, 50)
    
    sql_raw = f"SELECT codigoOC, NombreOC, DescripcionOC, RegionUnidadCompra, Proveedor FROM {REMOTE_TABLE} WHERE 1=1"
    sql_raw = apply_filters(sql_raw) + f" LIMIT {limit_slider}"
    
    if st.button("🔎 Fetch Details"):
        with st.spinner("Retrieving records..."):
            df_raw = con.execute(sql_raw).df()
            st.dataframe(df_raw, use_container_width=True)
