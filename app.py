import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px

# --- PAGE CONFIG ---
st.set_page_config(page_title="Ramp-Up: Intelligence Dashboard", layout="wide")

# --- CSS MAGIC (Darker & Cleaner) 🎨 ---
def set_background_image():
    # Same cool background, but much darker overlay for readability
    bg_url = "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072&auto=format&fit=crop"
    st.markdown(
         f"""
         <style>
         .stApp {{
             background-image: url("{bg_url}");
             background-attachment: fixed;
             background-size: cover;
             /* Made darker (0.85) so text pops */
             background-color: rgba(0,0,0,0.85);
             background-blend-mode: darken;
         }}
         [data-testid="stHeader"] {{ background-color: rgba(0,0,0,0.0); }}
         section[data-testid="stSidebar"] {{
             background-color: rgba(0, 0, 0, 0.5);
         }}
         /* Makes metric numbers big and white */
         [data-testid="stMetricValue"] {{
            color: white !important;
         }}
         </style>
         """,
         unsafe_allow_html=True
     )
set_background_image()

# --- MAIN TITLE ---
st.markdown("<h1 style='text-align: center; color: white;'>🚀 Ramp-Up: Interactive Intelligence</h1>", unsafe_allow_html=True)

# ==========================================
# 😂 THE FUNNY PICTURE ZONE
# ==========================================
# Replace the URL below with a link to your funny image!
# It can be from imgur, stored in R2, or any public URL.
funny_image_url = "https://yt3.googleusercontent.com/gj9EIW8WipNrL5gmzaVljVudgcnf2p6q4PNSuW0IP6PU_TlVmoFP7aK5v0L6vKwDcSrFQNV-eA=s900-c-k-c0x00ffffff-no-rj"
col_spacer1, col_img, col_spacer2 = st.columns([1, 2, 1])
with col_img:
    st.image(funny_image_url, use_column_width=True)
# ==========================================


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

# Hardcoded list for speed
region_options = ["All Regions", "Region Metropolitana de Santiago", "Region de Valparaiso", "Region del Biobio", "Region de Antofagasta", "Region de La Araucania", "Region de Los Lagos"]
selected_region = st.sidebar.selectbox("📍 Region", region_options)
selected_keyword = st.sidebar.text_input("📦 Category/Product (Keyword)", placeholder="e.g. Computacion")

# --- QUERY BUILDER FUNCTION ---
def apply_filters(base_sql):
    if selected_region != "All Regions":
        base_sql += f" AND RegionUnidadCompra = '{selected_region}'"
    if selected_keyword:
        base_sql += f" AND (RubroN1 ILIKE '%{selected_keyword}%' OR DescripcionOC ILIKE '%{selected_keyword}%')"
    return base_sql

# ==========================================
# 📊 THE TABS
# ==========================================
tab1, tab2, tab3 = st.tabs(["🧮 Super Pivot & Metrics", "🏆 Leaderboards", "🕵️ Detail Detective"])

# === TAB 1: SUPER PIVOT & METRICS ===
with tab1:
    st.markdown("### 🔎 At a Glance (Filtered View)")
    
    # --- BIG READABLE METRICS ---
    # We calculate these based on the current filters
    sql_metrics = f"SELECT COUNT(*) as TotalTenders, COUNT(DISTINCT Proveedor) as UniqueSuppliers FROM {REMOTE_TABLE} WHERE 1=1"
    sql_metrics = apply_filters(sql_metrics)
    
    # Only run metrics if filters change to save time
    with st.spinner("Updating metrics..."):
        df_metrics = con.execute(sql_metrics).df()
        met_col1, met_col2, met_col3 = st.columns(3)
        met_col1.metric("Total Tenders Found", f"{df_metrics['TotalTenders'][0]:,}")
        met_col2.metric("Active Suppliers", f"{df_metrics['UniqueSuppliers'][0]:,}")
        met_col3.metric("Region Filter", selected_region if selected_region != "All Regions" else "Global")

    st.divider() # A nice line to separate sections

    st.markdown("### 🧮 Slice & Dice Volume")
    
    col_group, col_viz = st.columns([1, 3])
    
    with col_group:
        st.info("Select how to group the data shown above.")
        dimension = st.radio("Group By Axis:", 
                             ["RegionUnidadCompra", "Institucion", "Proveedor", "RubroN1"],
                             index=3) # Default to Rubro (Category)
    
    with col_viz:
        base_query = f"SELECT {dimension} as GroupName, COUNT(*) as Total FROM {REMOTE_TABLE} WHERE 1=1"
        filtered_query = apply_filters(base_query)
        final_query = filtered_query + " GROUP BY GroupName ORDER BY Total DESC LIMIT 15"
        
        with st.spinner("Pivoting chart..."):
            df_pivot = con.execute(final_query).df()
            fig = px.bar(df_pivot, x='Total', y='GroupName', # Swapped X and Y for horizontal bar (easier to read labels)
                         title=f"Top 15 by {dimension}",
                         color='Total', orientation='h', text_auto=True)
            # Dark theme for chart
            fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)

# === TAB 2: LEADERBOARDS (Cross-Filtered) ===
with tab2:
    st.markdown(f"### 🏆 Top Players ({selected_region})")
    
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
    st.markdown("### 🕵️ Deep Dive Data")
    st.caption("Raw data matching current filters.")
    limit_slider = st.slider("Rows to show", 10, 500, 50)
    
    sql_raw = f"SELECT codigoOC, NombreOC, DescripcionOC, RegionUnidadCompra, Proveedor, MontoTotalOC_CLP FROM {REMOTE_TABLE} WHERE 1=1"
    sql_raw = apply_filters(sql_raw) + f" LIMIT {limit_slider}"
    
    if st.button("🔎 Fetch Details"):
        with st.spinner("Retrieving records..."):
            df_raw = con.execute(sql_raw).df()
            st.dataframe(df_raw, use_container_width=True)
