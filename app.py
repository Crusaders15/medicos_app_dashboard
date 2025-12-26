import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px

# --- PAGE CONFIG ---
st.set_page_config(page_title="Ramp-Up: Intelligence Dashboard", layout="wide")
st.title("🚀 Ramp-Up: Market Intelligence")

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

# --- SOURCE DEFINITION ---
CSV_FILE = "s3://compra-agil-data/CA_2025.csv"
REMOTE_TABLE = f"read_csv('{CSV_FILE}', delim=';', header=True, encoding='cp1252', ignore_errors=True)"

try:
    con = get_connection()
except Exception as e:
    st.error(f"Connection Failed: {e}")

# --- TABS ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 Market Overview", "🏆 Top Winners", "🕵️ Profile Detective", "📥 Data Extractor"])

# === TAB 1: MARKET OVERVIEW (The Big Picture) ===
with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🌎 Tenders by Region")
        if st.button("🔄 Load Regional Data"):
            query_geo = f"""
                SELECT RegionUnidadCompra as Region, COUNT(*) as Total 
                FROM {REMOTE_TABLE} 
                GROUP BY Region ORDER BY Total DESC
            """
            with st.spinner("Crunching numbers..."):
                df_geo = con.execute(query_geo).df()
                fig = px.bar(df_geo, x='Region', y='Total', color='Total')
                st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("### 🛠️ Top Specialties (Rubros)")
        if st.button("🔄 Load Specialties"):
            # We look at 'RubroN1' (Broad Category) or 'RubroN3' (Specific)
            query_rubro = f"""
                SELECT RubroN1 as Specialty, COUNT(*) as Total 
                FROM {REMOTE_TABLE} 
                GROUP BY Specialty ORDER BY Total DESC LIMIT 10
            """
            with st.spinner("Analyzing specialties..."):
                df_rubro = con.execute(query_rubro).df()
                fig2 = px.pie(df_rubro, values='Total', names='Specialty', title="Top 10 Categories")
                st.plotly_chart(fig2, use_container_width=True)

# === TAB 2: TOP WINNERS (What Felipe Asked For) ===
with tab2:
    st.markdown("### 🏆 Who is winning the contracts?")
    st.info("This list shows the suppliers with the most won tenders.")
    
    if st.button("Show Leaderboard"):
        query_winners = f"""
            SELECT Proveedor, RegionProveedor, COUNT(*) as Wins 
            FROM {REMOTE_TABLE} 
            GROUP BY Proveedor, RegionProveedor
            ORDER BY Wins DESC LIMIT 20
        """
        with st.spinner("Calculating leaderboard..."):
            df_winners = con.execute(query_winners).df()
            st.dataframe(df_winners, use_container_width=True)

# === TAB 3: THE DETECTIVE (Text Search) ===
with tab3:
    st.markdown("### 🕵️ Find Hidden Professionals")
    st.info("Find 'Psicologos' or 'TENS' hidden in descriptions.")
    
    search_term = st.text_input("Search Keyword", placeholder="e.g., Salud Mental")
    
    if search_term:
        detective_query = f"""
            SELECT codigoOC, NombreOC, DescripcionOC, MontoTotalOC, RegionUnidadCompra
            FROM {REMOTE_TABLE} 
            WHERE DescripcionOC ILIKE '%{search_term}%' 
            OR NombreOC ILIKE '%{search_term}%'
            LIMIT 50
        """
        with st.spinner(f"Hunting for '{search_term}'..."):
            results = con.execute(detective_query).df()
            st.dataframe(results)

# === TAB 4: DATA EXTRACTOR (No Code!) ===
with tab4:
    st.markdown("### 📥 Easy Data Downloader")
    st.write("Filter the data and download it for Excel.")

    # 1. THE FILTERS (UI Controls)
    col_reg, col_rubro = st.columns(2)
    
    with col_reg:
        # Hardcoded list is faster than querying the DB
        region_filter = st.selectbox("Select Region", 
            ["All Regions", "Region Metropolitana de Santiago", "Region de Valparaiso", "Region del Biobio", "Region de Antofagasta"])
    
    with col_rubro:
        rubro_keyword = st.text_input("Filter by Category (Rubro)", placeholder="e.g., Computacion")

    # 2. BUILD THE QUERY AUTOMATICALLY
    limit_rows = st.slider("Max Rows to Download", 10, 5000, 100)
    
    if st.button("🚀 Find Data"):
        # Base Query
        sql = f"SELECT * FROM {REMOTE_TABLE} WHERE 1=1"
        
        # Add filters dynamically
        if region_filter != "All Regions":
            sql += f" AND RegionUnidadCompra = '{region_filter}'"
        
        if rubro_keyword:
            sql += f" AND (RubroN1 ILIKE '%{rubro_keyword}%' OR RubroN2 ILIKE '%{rubro_keyword}%')"
        
        sql += f" LIMIT {limit_rows}"
        
        # Run It
        with st.spinner("Fetching data..."):
            df_extract = con.execute(sql).df()
            st.dataframe(df_extract)
            
            # DOWNLOAD BUTTON
            csv = df_extract.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Download as CSV",
                csv,
                "licitakiller_data.csv",
                "text/csv"
            )
