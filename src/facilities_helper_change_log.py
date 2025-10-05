import streamlit as st
import pandas as pd

@st.cache_data
def load_facility_summary():
    df = pd.read_csv("data/facilities_summary_by_date_status_type.csv")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df.dropna(subset=["date"])


def render_facility_change_log():
    df = load_facility_summary()

    available_dates = sorted(df["date"].dropna().unique())
    if len(available_dates) < 1:
        st.warning("No valid date entries found in dataset.")
        return

    # --- Friendly labels for dropdowns ---
    date_labels = [pd.to_datetime(d).strftime("%d %B %Y") for d in available_dates]
    date_map = dict(zip(date_labels, available_dates))

    # --- Date selectors ---
    col1, col2 = st.columns(2)
    with col1:
        date_latest_label = st.selectbox(
            "Select latest snapshot:",
            options=date_labels,
            index=len(date_labels) - 1,
        )
        date_latest = date_map[date_latest_label]
    with col2:
        date_before_label = st.selectbox(
            "Compare to previous snapshot:",
            options=date_labels,
            index=max(len(date_labels) - 2, 0),
        )
        date_before = date_map[date_before_label]

    # --- Aggregate by status for both snapshots ---
    latest = (
        df[df["date"] == date_latest]
        .groupby("status")["n_facilities"]
        .sum()
        .rename("Current")
    )
    before = (
        df[df["date"] == date_before]
        .groupby("status")["n_facilities"]
        .sum()
        .rename("Previous")
    )

    # --- Combine and compute change ---
    change_log = pd.concat([before, latest], axis=1).fillna(0)
    change_log["Change"] = change_log["Current"] - change_log["Previous"]
    change_log["% Change"] = (
        change_log["Change"] / change_log["Previous"].replace(0, pd.NA) * 100
    ).round(1)

    # --- Order and color by status ---
    status_order = ["Under Design", "Tender launched", "Contract awarded", "Energized"]
    status_colors = {
        "Under Design": "rgba(231, 76, 60, 0.25)",      # semi-transparent red
        "Tender launched": "rgba(230, 126, 34, 0.25)",   # semi-transparent orange
        "Contract awarded": "rgba(241, 196, 15, 0.25)",  # semi-transparent yellow
        "Energized": "rgba(46, 204, 113, 0.25)",         # semi-transparent green
    }
    change_log = change_log.reindex(status_order)

    # --- Style logic ---
    def color_change(val):
        if pd.isna(val):
            return "color: gray;"
        elif val > 0:
            return "color: lightgreen;"
        elif val < 0:
            return "color: salmon;"
        return ""

    def style_index_color(index):
        """Apply faint background color to the index column (status names)."""
        color = status_colors.get(index, "transparent")
        return f"background-color: {color}; font-weight: 600; color: black;"

    # --- Display styled dataframe ---
    styled = (
        change_log.style
        .format({
            "Previous": "{:.0f}",
            "Current": "{:.0f}",
            "Change": "{:+.0f}",
            "% Change": "{:+.1f}%"
        })
        .applymap(color_change, subset=["Change", "% Change"])
    )

    # Apply faint color to index (status titles)
    styled = styled.set_table_styles([
        {
            "selector": "th.row_heading",
            "props": [
                ("text-align", "left"),
                ("font-weight", "bold"),
            ]
        }
    ])

    # Custom index coloring (loop through statuses)
    for status, color in status_colors.items():
        styled = styled.map_index(lambda v, s=status, c=color:
            f"background-color: {c}; color: black; font-weight: 600;"
            if v == s else None
        )

    st.dataframe(styled, use_container_width=True, height=280)

    # --- Caption ---
    st.caption(
        f"Compared **{date_before_label} → {date_latest_label}**"
    )
