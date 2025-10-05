import streamlit as st
from src.facilities_overview_dashboard_helper import load_data, extract_all_facility_summaries, render_facility_dashboard, render_summary_statistics
import datetime
import pandas as pd

# --------------------------------------
# Page setup (must come first)
# --------------------------------------
st.set_page_config(
    page_title="0_YEEAP_II_Analytics",
    layout="wide",
    initial_sidebar_state="collapsed",  # ✅ hides sidebar initially
)

# --------------------------------------
# Simple password protection
# --------------------------------------
PASSWORD = "yeeap2025"  # fake password for now

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    # Hide sidebar (even if user expands it manually)
    hide_sidebar_style = """
        <style>
            [data-testid="stSidebar"] {display: none;}
            footer {visibility: hidden;}
        </style>
    """
    st.markdown(hide_sidebar_style, unsafe_allow_html=True)

    st.title("🔒 YEEAP II Dashboard Login")
    pwd = st.text_input("Enter password:", type="password")
    if st.button("Login"):
        if pwd == PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password. Please try again.")

    st.stop()  # 🚫 stop app here until logged in
# Main App (after login)
# --------------------------------------

st.set_page_config(
    page_title="0_YEEAP_II_Analytics",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session data
if "df_summary" not in st.session_state:
    st.session_state.df_summary = load_data("data/facilities_summary_by_date_status_type.csv")


if "targets" not in st.session_state:
    st.session_state.targets = {
        "Total": 700,
        "School": 100,
        "Clinic": 350,
        "Well": 200,
        "Vaccine": 50,
    }

# Retrieve
df_summary = st.session_state.df_summary
df_summary["date"] = pd.to_datetime(df_summary["date"], errors="coerce")
targets = st.session_state.targets
summaries = extract_all_facility_summaries(df_summary, targets)
latest_date = df_summary["date"].max()
formatted_date = latest_date.strftime("%B %d, %Y") if pd.notnull(latest_date) else "Unknown"

#-----------------------------------

with st.sidebar:
    st.markdown("## YEEAP II Project Dashboard")
    st.markdown(
        f"**Data as of:**   \t<span style='color:#1f77b4; font-weight:600;'>{formatted_date}</span>",
        unsafe_allow_html=True,
    )
    st.caption("Monitoring off-grid electrification progress in Yemen")

    st.divider()

    st.header("Components")
    st.markdown(
        """
        #### [Energizing Critical Facilities](#energizing-critical-facilities)
        Under Sub-components **1.2** and **1.3**, the project scales up off-grid electricity access to health, education, and water facilities, and supports COVID-19 isolation and vaccine cold-chain units through reliable solar power systems.

        #### [Electrifying Households](#electrifying-households)
        Under Sub-component **1.1**, the project expands access to off-grid solar systems for rural and peri-urban households by empowering microfinance institutions and scaling household electrification across Yemen.
        """,
        unsafe_allow_html=True,
    )

    st.divider()

#-----------------------------------

st.title("YEEAP II Project Monitoring Dashboard")

# ----------------------------------

with st.container(border=True):

    a, b = st.columns([0.8, 0.2], vertical_alignment="bottom")
    a.header("Electrifying Households")
    with b.container():
        if st.button("Open MFI Dashboard", use_container_width=True,  type='primary'):
            st.switch_page("")


# ----------------------------------


with st.container(border=True):

    a, b = st.columns([0.8, 0.2], vertical_alignment="bottom")
    a.header("Energizing Critical Facilities")
    with b.container():
        if st.button("Open Facilities Dashboard", use_container_width=True, type='primary'):
            st.switch_page("pages/0_Facilities_Data_Explorer.py")

    # --- Summary statistics ---
    st.markdown("<a name='summary-statistics'></a>", unsafe_allow_html=True)
    render_summary_statistics(df_summary)

    # --- Facility dashboard ---
    st.markdown("<a name='facility-breakdown'></a>", unsafe_allow_html=True)
    render_facility_dashboard(summaries)

# -----------------------------------

