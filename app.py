import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import random
import io
import boto3
from datetime import datetime
from pydantic import BaseModel, Field

# --- 1. CONFIGURATION (Pydantic Fix) ---
class R2Config(BaseModel):
    account_id: str = Field(..., alias="ACCOUNT_ID")
    access_key: str = Field(..., alias="ACCESS_KEY")
    secret_key: str = Field(..., alias="SECRET_KEY")
    endpoint: str = Field(..., alias="R2_ENDPOINT")
    bucket: str = Field(..., alias="R2_BUCKET_NAME")

# --- 2. PAGE CONFIG ---
st.set_page_config(
    page_title="Ramp Up: Intelligence Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 3. PROFESSIONAL UI DESIGN (THE NUCLEAR FIX) ---
def set_design():
    bg_url = "https://images.unsplash.com/photo-1451187588459-43490779c0fa?q=80&w=2072&auto=format&fit=crop"
    st.markdown(f"""
        <style>
        .stApp {{
            background-image: url("{bg_url}");
            background-size: cover;
        }}
        [data-testid="stSidebar"] {{
            background-color: rgba(0,0,0,0.7) !important;
        }}
        </style>
    """, unsafe_allow_html=True)

set_design()

# --- 4. SECURITY SYSTEM (Fixes Line 76/78 API Exception) ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
    if st.session_state.password_correct:
        return True

    st.markdown("<h1 style='text-align: center;'>Ramp-Up Intelligence</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Changed type to "password" to stop the StreamlitAPIException crash
        pwd_input = st.text_input("Access Code", type="password")
        if pwd_input:
            secret_pwd = st.secrets["GENERAL"]["APP_PASSWORD"]
            if pwd_input == secret_pwd:
                st.session_state.password_correct = True
                st.rerun()
            else:
                st.error("Access Denied")
    return False

# --- 5. MAIN DASHBOARD LOGIC ---
if check_password():
    try:
        # Load verified R2 Settings from st.secrets["R2"]
        settings = R2Config(**st.secrets["R2"])
        
        # Initialize R2 Connection
        s3 = boto3.client(
            service_name="s3",
            endpoint_url=settings.endpoint,
            aws_access_key_id=settings.access_key,
            aws_secret_access_key=settings.secret_key,
            region_name="auto"
        )
        
        # --- GLOBAL SLICERS ---
        st.sidebar.title("Global Slicers")
        date_range = st.sidebar.date_input("Analysis Period", [])
        
        st.title("Ramp-Up: Interactive Intelligence")
        
        # --- DATA PROCESSING & DUCKDB FIX (Line 167) ---
        # 1. Fetch data from R2
        response = s3.get_object(Bucket=settings.bucket, Key='data.csv') # Ensure Key is correct
        df_final = pd.read_csv(io.BytesIO(response['Body'].read()))
        
        # 2. Fix for DuckDB BinderException: Create Connection and Register Table
        con = duckdb.connect(database=':memory:')
        con.register('df_table', df_final) 
        
        # 3. Line 167 Execution
        sql = "SELECT * FROM df_table"
        df = con.execute(sql).df() 
        
        # --- TABS & VISUALS ---
        tab1, tab2, tab3 = st.tabs(["Market Summary", "Performance", "Detail View"])
        
        with tab1:
            st.write("Data successfully linked through DuckDB.")
            st.dataframe(df.head())
            
            # (Your specific Chart logic here)
            # Example: fig = px.bar(df, x="Region", y="Total")
            # st.plotly_chart(fig)

    except Exception as e:
        st.error(f"System Error: {e}")
