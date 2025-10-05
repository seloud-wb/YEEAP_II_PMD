import pandas as pd
import plotly.express as px
import streamlit as st

@st.cache_data
def load_facility_summary(path="data/facilities_summary_by_date_status_type.csv"):
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df


FACILITY_TITLE_MAP = {
    "Total": "All Facility Types",
    "School": "Educational Facilities",
    "Clinic": "Health Facilities",
    "Well": "Water Facilities",
    "Vaccine": "Vaccination Facilities",
}


def render_facility_rollout_chart():
    # ----------------------------------------------------------------
    # Ensure targets exist in session
    # ----------------------------------------------------------------
    if "targets" not in st.session_state:
        st.session_state.targets = {
            "Total": 700,
            "School": 100,
            "Clinic": 350,
            "Well": 200,
            "Vaccine": 50,
        }

    df = load_facility_summary()

    # ----------------------------------------------------------------
    # Facility Type Selector
    # ----------------------------------------------------------------
    facility_types = ["Total"] + sorted(df["type"].dropna().unique().tolist())
    selected_type = st.selectbox("Select Facility Type:", facility_types, index=0)

    # Filter if not total
    if selected_type != "Total":
        df = df[df["type"] == selected_type]

    # ----------------------------------------------------------------
    # Aggregate by date & status
    # ----------------------------------------------------------------
    grouped = (
        df.groupby(["date", "status"], dropna=False)
          .agg(n_facilities=("n_facilities", "sum"))
          .reset_index()
          .dropna(subset=["date"])
    )

    # ----------------------------------------------------------------
    # Define color map and stacking order
    # ----------------------------------------------------------------
    status_order = ["Under Design", "Tender launched", "Contract awarded", "Energized"]
    status_colors = {
        "Under Design": "red",
        "Tender launched": "orange",
        "Contract awarded": "yellow",
        "Energized": "green",
    }

    grouped["status"] = pd.Categorical(grouped["status"], categories=status_order, ordered=True)
    grouped = grouped.sort_values(["date", "status"])

    # ----------------------------------------------------------------
    # Get target from session
    # ----------------------------------------------------------------
    target_value = st.session_state.targets.get(selected_type, st.session_state.targets["Total"])
    title_text = FACILITY_TITLE_MAP.get(selected_type, selected_type)

    # ----------------------------------------------------------------
    # Plot the chart
    # ----------------------------------------------------------------
    fig = px.area(
        grouped,
        x="date",
        y="n_facilities",
        color="status",
        category_orders={"status": status_order},
        color_discrete_map=status_colors,
        title=f"Facility Rollout Progress — {title_text}",
    )

    # --- Hover styling ---
    hovertemplate = (
        "<b>%{x|%d %B %Y}</b><br>"
        "Status: %{fullData.name}<br>"
        "Facilities: %{y:,}<extra></extra>"
    )
    fig.update_traces(
        mode="lines+markers",
        hovertemplate=hovertemplate,
        marker=dict(size=5, line=dict(width=0.5, color="black")),
    )

    # ----------------------------------------------------------------
    # Add target line + annotation
    # ----------------------------------------------------------------
    fig.add_hline(y=target_value, line_dash="dash", line_color="white")
    fig.add_annotation(
        xref="paper", x=0,
        y=target_value,
        text=f"<b>Target ({target_value})</b>",
        xanchor="left",
        yanchor="bottom",
        font=dict(color="white", size=12),
        showarrow=False,
        bgcolor="rgba(255,255,255,0.05)",
        bordercolor="rgba(255,255,255,0.2)",
        borderwidth=0.5,
    )

    # ----------------------------------------------------------------
    # Layout and styling
    # ----------------------------------------------------------------
    x_min, x_max = grouped["date"].min(), grouped["date"].max()
    padding_days = pd.Timedelta(days=5)

    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Number of Facilities",
        plot_bgcolor="#2a2a2c",
        paper_bgcolor="#121214",
        font=dict(color="white"),
        hovermode="x unified",
        legend=dict(
            title_text="",
            orientation="h",
            yanchor="top",
            y=-0.3,
            xanchor="center",
            x=0.51,
            valign="top",
            tracegroupgap=0,
            entrywidth=100,
            entrywidthmode="pixels",
            bgcolor="rgba(255, 255, 255, 0.2)",
        )
    )

    fig.update_xaxes(
        dtick="M1",
        tickformat="%b %Y",
        showgrid=True,
        gridcolor="rgba(255,255,255,0.15)",
        linecolor="rgba(255,255,255,0.3)",
        zeroline=False,
        range=[x_min, x_max + padding_days],
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor="rgba(255,255,255,0.1)",
        tickfont=dict(color="white"),
        ticks="outside",
        showline=True,
        linecolor="rgba(255,255,255,0.4)",
    )

    # ----------------------------------------------------------------
    # Render
    # ----------------------------------------------------------------
    st.plotly_chart(fig, use_container_width=True)
