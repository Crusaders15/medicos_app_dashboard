import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px

# --- PAGE CONFIG ---
st.set_page_config(page_title="Ramp-Up: Intelligence Dashboard", layout="wide")

# --- CSS MAGIC (Ghost Mode & White Text) ---
def set_design():
    bg_url = "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072&auto=format&fit=crop"
    st.markdown(
         f"""
         <style>
         /* 1. Background Image */
         .stApp {{
             background-image: url("{bg_url}");
             background-attachment: fixed;
             background-size: cover;
             background-color: rgba(0,0,0,0.85);
             background-blend-mode: darken;
         }}
         
         /* 2. FORCE TEXT TO BE WHITE */
         .stMarkdown, .stText, h1, h2, h3, h4, h5, h6, p, li, span, label {{
             color: white !important;
         }}
         
         /* 3. Make Metrics (Big Numbers) White */
         [data-testid="stMetricValue"] {{
            color: white !important;
         }}
         
         /* 4. Sidebar Transparency */
         section[data-testid="stSidebar"] {{
             background-color: rgba(0, 0, 0, 0.6);
         }}
         
         /* 5. GHOST MODE: HIDE MENUS & GITHUB BUTTONS  */
         #MainMenu {{visibility: hidden;}}
         footer {{visibility: hidden;}}
         header {{visibility: hidden;}}
         .stDeployButton {{display:none;}}
         
         </style>
         """,
         unsafe_allow_html=True
     )
set_design()

# --- MAIN TITLE ---
st.markdown("<h1 style='text-align: center; color: white; text-shadow: 2px 2px 4px #000000;'> Ramp-Up: Interactive Intelligence</h1>", unsafe_allow_html=True)

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
#  SIDEBAR (FILTERS + FUNNY IMAGE)
# ==========================================
st.sidebar.header(" Global Slicers")

# 1. The Filters
region_options = ["All Regions", "Region Metropolitana de Santiago", "Region de Valparaiso", "Region del Biobio", "Region de Antofagasta", "Region de La Araucania", "Region de Los Lagos"]
selected_region = st.sidebar.selectbox(" Region", region_options)
selected_keyword = st.sidebar.text_input(" Category/Product", placeholder="e.g. Computacion")

# 2. Spacer to push image down
st.sidebar.markdown("---") 
st.sidebar.markdown("###  Internal Only")

# 3.  THE FUNNY PICTURE (MOVED TO SIDEBAR!)
# REPLACE THIS LINK with your funny picture link!
funny_image_url = "https://drive.google.com/file/d/1EYKQjHeGVMkrpZyRd1n8XE6pQsOCGQ5S/view?usp=drive_link"
st.sidebar.image(funny_image_url, caption="Authorized Personnel Only ", use_container_width=True)

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
tab1, tab2, tab3 = st.tabs([" Super Pivot", " Leaderboards", " Detail Detective"])

# === TAB 1: SUPER PIVOT ===
with tab1:
    st.markdown("### 🔎 At a Glance")
    
    # METRICS BUTTON (Lazy Loading)
    if st.button("🔄 Update Dashboard Metrics", type="primary"):
        sql_metrics = f"SELECT COUNT(*) as TotalTenders FROM {REMOTE_TABLE} WHERE 1=1"
        sql_metrics = apply_filters(sql_metrics)
        
        with st.spinner("Calculating metrics..."):
            df_metrics = con.execute(sql_metrics).df()
            met_col1, met_col2 = st.columns(2)
            met_col1.metric("Total Tenders", f"{df_metrics['TotalTenders'][0]:,}")
            met_col2.metric("Region Scope", selected_region if selected_region != "All Regions" else "Global")
    else:
        st.info(" Click the button above to calculate the latest numbers.")

    st.divider()

    st.markdown("###  Slice & Dice Volume")
    col_group, col_viz = st.columns([1, 3])
    
    with col_group:
        st.write("Group Data By:")
        dimension = st.radio("Axis:", 
                             ["RegionUnidadCompra", "Institucion", "Proveedor", "RubroN1"],
                             index=3) 
    
    with col_viz:
        if st.button(" Render Chart"):
            base_query = f"SELECT {dimension} as GroupName, COUNT(*) as Total FROM {REMOTE_TABLE} WHERE 1=1"
            filtered_query = apply_filters(base_query)
            final_query = filtered_query + " GROUP BY GroupName ORDER BY Total DESC LIMIT 15"
            
            with st.spinner("Pivoting chart..."):
                df_pivot = con.execute(final_query).df()
                fig = px.bar(df_pivot, x='Total', y='GroupName', 
                             title=f"Top 15 by {dimension}",
                             color='Total', orientation='h', text_auto=True)
                # Force Dark Theme Chart
                fig.update_layout(template="plotly_dark", 
                                  paper_bgcolor='rgba(0,0,0,0)', 
                                  plot_bgcolor='rgba(0,0,0,0)', 
                                  font=dict(color="white"), 
                                  yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig, use_container_width=True)

# === TAB 2: LEADERBOARDS ===
with tab2:
    st.markdown(f"###  Top Players ({selected_region})")
    if st.button(" Load Leaderboards"):
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
    st.markdown("###  Deep Dive Data")
    limit_slider = st.slider("Rows to show", 10, 500, 50)
    
    if st.button(" Fetch Details"):
        sql_raw = f"SELECT codigoOC, NombreOC, DescripcionOC, RegionUnidadCompra, Proveedor FROM {REMOTE_TABLE} WHERE 1=1"
        sql_raw = apply_filters(sql_raw) + f" LIMIT {limit_slider}"
        with st.spinner("Retrieving records..."):
            df_raw = con.execute(sql_raw).df()
            st.dataframe(df_raw, use_container_width=True)
