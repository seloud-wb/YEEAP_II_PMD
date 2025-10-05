import streamlit as st
import pandas as pd
from src.facilities_helper_map_2 import render_yemen_facility_map
from src.facilities_helper_rollout import render_facility_rollout_chart
from src.facilities_helper_change_log import render_facility_change_log, load_facility_summary


st.set_page_config(page_title="Facility Progress Over Time", layout="wide")

# ---------------------------------------------------------------
# Load dataset
# ---------------------------------------------------------------
df = load_facility_summary()

# Ensure proper date handling
df["date"] = pd.to_datetime(df["date"], errors="coerce")
df = df.dropna(subset=["date"])

latest_date = df["date"].max()
df_latest = df[df["date"] == latest_date].copy()

# ---------------------------------------------------------------
# Sidebar summary (latest snapshot)
# ---------------------------------------------------------------
with st.sidebar:
    st.markdown("# Summary")
    st.caption(f"as of **{latest_date:%d %B %Y}**")

    # --- Facility summary ---
    total = int(df_latest["n_facilities"].sum()) if "n_facilities" in df_latest.columns else 0
    energized = int(df_latest[df_latest["status"].str.lower() == "energized"]["n_facilities"].sum()) if "status" in df_latest.columns else 0
    percent_energized = (energized / total * 100) if total > 0 else 0

    st.metric("Percent Energized", f"{percent_energized:.1f}%")
    a,b = st.columns(2)
    a.metric("Total Facilities", f"{total:,}")
    b.metric("Energized", f"{energized:,}")


    st.divider()

    # --- Beneficiary summary (Energized only) ---
    energized_df = df_latest[df_latest["status"].str.lower() == "energized"].copy()

    def safe_sum(df, col):
        """Safely sum numeric columns, coercing non-numeric values if needed."""
        if col not in df.columns:
            return 0
        return int(pd.to_numeric(df[col], errors="coerce").fillna(0).sum())

    total_benef = safe_sum(energized_df, "total_beneficiaries")
    female_benef = safe_sum(energized_df, "female_beneficiaries")
    male_benef = safe_sum(energized_df, "male_beneficiaries")

    female_pct = (female_benef / total_benef * 100) if total_benef > 0 else 0
    male_pct = (male_benef / total_benef * 100) if total_benef > 0 else 0

    st.markdown("### Beneficiaries")
    st.metric("Total Beneficiaries", f"{total_benef:,}")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Female", f"{int(female_pct)}%")
    with col2:
        st.metric("Male", f"{int(male_pct)}%")

    st.divider()
    st.markdown("### Installed Capacity")

    total_kw = safe_sum(energized_df, "solar_capacity_kw")
    total_kwh = safe_sum(energized_df, "storage_capacity_kwh")


    st.metric("Solar Capacity (kW)", f"{total_kw:,.1f}")
    st.metric("Battery Storage (kWh)", f"{total_kwh:,.1f}")


st.title("Facility Data Explorer")
# ---------------------------------------------------------------
# Main dashboard layout
# ---------------------------------------------------------------
A, B = st.columns([4, 5], vertical_alignment="center")

with A.container(border=False):
    st.header("Change Log")

with B.container(border=False):
    st.header("Facility Rollout Progress")

C, D = st.columns([4, 5], vertical_alignment="top")

with C.container(border=True):
    render_facility_change_log()

with D.container(border=True):
    render_facility_rollout_chart()

with st.container(border=True):
    st.header("Map Explorer")
    render_yemen_facility_map()

with st.expander("🔍 View Latest Snapshot Data"):
    st.dataframe(
        df_latest,
        use_container_width=True,
        height=300
    )