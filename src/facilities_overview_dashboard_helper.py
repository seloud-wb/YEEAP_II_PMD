import streamlit as st
import pandas as pd
from pathlib import Path
from src.facilities_helper_summary_statistics import extract_facility_summary


# ----------------------------------------------------------
# Cached Data Loader
@st.cache_data
def load_data(path: str):
    path = Path(path)
    if not path.exists():
        st.error(f"File not found: {path}")
        return None
    if path.suffix == ".csv":
        return pd.read_csv(path)
    elif path.suffix in [".xlsx", ".xls"]:
        return pd.read_excel(path)
    else:
        st.error(f"Unsupported file type: {path.suffix}")
        return None


# ----------------------------------------------------------
# Summaries Extractor
@st.cache_data
def extract_all_facility_summaries(df, targets):
    facility_types = ["School", "Clinic", "Well", "Vaccine"]
    FACILITY_TITLE_MAP = {
        "School": "Educational Facilities",
        "Clinic": "Health Facilities",
        "Well": "Water Facilities",
        "Vaccine": "Vaccination Facilities",
    }

    summaries = {}
    for ftype in facility_types:
        s = extract_facility_summary(df, ftype, targets)
        s["title"] = FACILITY_TITLE_MAP.get(ftype, ftype)
        summaries[ftype] = s

    return summaries


# ----------------------------------------------------------
# Dashboard Rendering Logic
def render_facility_dashboard(summaries):
    """Render facilities dashboard layout dynamically with 2 columns per row."""
    facility_types = list(summaries.keys())
    cols_per_row = 2

    with st.container(border=True):
        for i in range(0, len(facility_types), cols_per_row):
            # --- Header Row ---
            header_cols = st.columns(cols_per_row, vertical_alignment="center")
            for j in range(cols_per_row):
                if i + j < len(facility_types):
                    ftype = facility_types[i + j]
                    s = summaries[ftype]
                    with header_cols[j]:
                        st.markdown(
                            f"<h4 style='text-align:center; margin-bottom:0;'>{s['title']}</h4>",
                            unsafe_allow_html=True,
                        )

            # --- Metrics Row ---
            body_cols = st.columns(cols_per_row, vertical_alignment="center")
            for j in range(cols_per_row):
                if i + j < len(facility_types):
                    ftype = facility_types[i + j]
                    s = summaries[ftype]
                    with body_cols[j]:
                        with st.container(border=True):
                            A, B = st.columns([1, 3], vertical_alignment="center")
                            A.metric(
                                label="Target Achieved",
                                value=f"{s['percent']:.1%}",
                                chart_data=s["energized_trend"],
                                chart_type="line",
                            )
                            B.progress(s["percent"])

                            with B.container(border=True):
                                a, b, c = st.columns(3)
                                a.metric(label="Energized", value=s["energized"], delta=f"{s['increase']}")
                                b.metric(label="Target", value=s["target"])
                                c.metric(label="Planned", value=s["planned"])


# ----------------------------------------------------------
# Dashboard Rendering Logic
def render_summary_statistics(df):
    """Display total summary statistics for latest date."""
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    latest_date = df["date"].max()

    # Filter latest and energized
    latest_df = df[df["date"] == latest_date]
    energized_df = latest_df[latest_df["status"].str.lower() == "energized"]

    # Totals
    total_facilities = energized_df["n_facilities"].sum()
    total_beneficiaries = energized_df["total_beneficiaries"].sum()
    total_solar_kw = energized_df["solar_capacity_kw"].sum()
    total_storage_kwh = energized_df["storage_capacity_kwh"].sum()

    # Render metrics
    with st.container(border=True):
        a, b, c, d = st.columns(4)
        a.metric(label="Facilities Energized / Target", value=f"{int(total_facilities):,} / {int(700)}")
        b.metric(label="Total Beneficiaries", value=f"{int(total_beneficiaries):,}")
        c.metric(label="Installed Solar Capacity (kW)", value=f"{total_solar_kw:,.1f}")
        d.metric(label="Installed Battery Capacity (kWh)", value=f"{total_storage_kwh:,.1f}")
