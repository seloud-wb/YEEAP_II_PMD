import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go

# ---------------------------------------------------------------
# Cached data loaders
# ---------------------------------------------------------------
@st.cache_data
def load_yemen_boundaries():
    """Load GeoJSON and prepare a dataframe with IDs and governorate names."""
    path = "data/boundaries_adm1.geojson"
    with open(path, "r") as f:
        geojson_data = json.load(f)

    # Extract governorate names
    features = []
    for i, ftr in enumerate(geojson_data["features"]):
        gov_name = ftr["properties"].get("adm1_en", f"Unknown_{i}")
        ftr["id"] = gov_name  # Set feature 'id' for Plotly to match
        features.append({"governorate": gov_name})

    df = pd.DataFrame(features)
    return df, geojson_data


@st.cache_data
def load_facility_sites():
    df = pd.read_csv("data/facilities_sites_latest.csv")
    return df.dropna(subset=["latitude", "longitude"])


@st.cache_data
def load_governorate_summary():
    df = pd.read_csv("data/facilities_governorate_summary.csv")
    return df


# ---------------------------------------------------------------
# Main rendering function
# ---------------------------------------------------------------
def render_yemen_facility_map():
    geo_df, geojson_data = load_yemen_boundaries()
    df_sites = load_facility_sites()
    df_gov = load_governorate_summary()

    # Normalize names between sources
    manual_name_map = {
        "Ad Dali": "Ad Dale'",
        "Amanat Al Asimah": "Sana'a City",
        "Ma'rib": "Marib",
        "Taiz": "Ta'iz",
    }
    df_gov["governorate"] = df_gov["governorate"].str.strip().replace(manual_name_map)

    # Merge
    geo = geo_df.merge(df_gov, on="governorate", how="left")

    # -----------------------------------------------------------
    # User controls
    # -----------------------------------------------------------
    metric = st.selectbox(
        "Select metric for governorate color:",
        ["total_facilities", "energized_facilities", "percent_energized"],
        index=2,
    )
    show_facilities = st.toggle("Show facility markers", value=True)

    # -----------------------------------------------------------
    # Color and symbol maps
    # -----------------------------------------------------------
    status_colors = {
        "Under Design": "red",
        "Tender launched": "orange",
        "Contract awarded": "yellow",
        "Energized": "green",
    }
    type_symbols = {
        "School": "circle",
        "Clinic": "square",
        "Well": "triangle-up",
        "Vaccine": "diamond",
    }

    # -----------------------------------------------------------
    # Plot Yemen map
    # -----------------------------------------------------------
    fig = px.choropleth(
        geo,
        geojson=geojson_data,
        locations="governorate",        # must match 'id' field in GeoJSON
        featureidkey="properties.adm1_en",  # tells Plotly which key to match
        color=metric,
        color_continuous_scale="GnBu",
        hover_name="governorate",
        hover_data={
            "total_facilities": True,
            "energized_facilities": True,
            "percent_energized": True,
        },
    )

    fig.update_geos(
        fitbounds="locations",
        visible=False,
        showland=True,
        showcountries=True,
        showframe=True,
    )

    # -----------------------------------------------------------
    # Add facility markers
    # -----------------------------------------------------------
    if show_facilities:
        for facility_type, symbol in type_symbols.items():
            subset = df_sites[df_sites["type"] == facility_type]
            hover_text = (
                "<b>Type:</b> " + subset["type"].astype(str) + "<br>"
                "<b>Status:</b> " + subset["status"].astype(str)
            )
            fig.add_trace(
                go.Scattergeo(
                    lon=subset["longitude"],
                    lat=subset["latitude"],
                    text=hover_text,
                    mode="markers",
                    marker=dict(
                        size=5,
                        color=subset["status"].map(status_colors).fillna("gray"),
                        symbol=symbol,
                        line=dict(width=0.5, color="black"),
                    ),
                    hoverinfo="text",
                    hoverlabel=dict(bgcolor="black", font_size=12, font_family="Arial"),
                    showlegend=False,   # 🔹 ensures NO legend entry
                )
            )

    # -----------------------------------------------------------
    # Layout and style
    # -----------------------------------------------------------
    fig.update_layout(
        showlegend=False,  # 🔹 disables all legends globally
        geo=dict(
            projection_scale=6,
            center=dict(lat=15, lon=47.5),
            showland=True,
            landcolor="black",
            bgcolor="black",
            showocean=True,
            oceancolor="black",
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="black",
        plot_bgcolor="black",
        font=dict(color="white"),
        coloraxis_colorbar=dict(
            title=metric.replace("_", " ").capitalize(),
            orientation="h",
            yanchor="bottom",
            y=-0.25,
            xanchor="center",
            x=0.5,
            thickness=10,
            len=0.6,
        ),
    )

    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Legend (Status & Type)"):
        col1, col2 = st.columns(2)

        # Status colors (left column)
        col1.markdown("**Project Status:**")
        with col1.container(border=True):
            for status, color in status_colors.items():
                st.markdown(
                    f"<span style='color:{color}; font-weight:700;'>●</span> {status}",
                    unsafe_allow_html=True,
                )

        # Facility types (right column)
        col2.markdown("**Facility Type:**")
        with col2.container(border=True):
            symbol_map = {
                "circle": "●",
                "square": "■",
                "triangle-up": "▲",
                "diamond": "◆",
            }
            for facility_type, symbol in type_symbols.items():
                st.markdown(
                    f"<span style='color:white;'>{symbol_map.get(symbol, '?')}</span> {facility_type}",
                    unsafe_allow_html=True,
                )
    # -----------------------------------------------------------
    # Debugging: data comparison
    # -----------------------------------------------------------
    with st.expander("Data Debugger"):
        st.markdown("#### Governorate Merge Status")
        missing = geo[geo["total_facilities"].isna()][["governorate"]]
        if missing.empty:
            st.success("✅ All governorates merged successfully.")
        else:
            st.warning(f"⚠️ {len(missing)} missing in summary file.")
            st.dataframe(missing)

        st.markdown("#### Unmatched Names")
        geo_names = set(geo["governorate"].dropna().str.lower())
        data_names = set(df_gov["governorate"].dropna().str.lower())
        st.write("Only in GeoJSON:", sorted(geo_names - data_names))
        st.write("Only in Summary Data:", sorted(data_names - geo_names))


# ---------------------------------------------------------------
# Run it
# ---------------------------------------------------------------
if __name__ == "__main__":
    render_yemen_facility_map()
