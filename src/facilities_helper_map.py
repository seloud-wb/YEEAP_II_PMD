import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.graph_objects as go
import plotly.express as px

# ---------------------------------------------------------------
# Cached data loaders
# ---------------------------------------------------------------
@st.cache_data
def load_yemen_boundaries():
    gdf = gpd.read_file("data/boundaries_adm1.geojson")
    gdf = gdf.rename(columns={"adm1_en": "governorate"})
    return gdf[["governorate", "geometry"]]

@st.cache_data
def load_facility_sites():
    df = pd.read_csv("data/facilities_sites_latest.csv")
    return df.dropna(subset=["latitude", "longitude"])

@st.cache_data
def load_governorate_summary():
    return pd.read_csv("data/facilities_governorate_summary.csv")

# ---------------------------------------------------------------
# Main rendering function
# ---------------------------------------------------------------
def render_yemen_facility_map():
    geo = load_yemen_boundaries()
    df_sites = load_facility_sites()
    df_gov = load_governorate_summary()

    # Normalize names
    manual_name_map = {
        "Ad Dali": "Ad Dale'",
        "Amanat Al Asimah": "Sana'a City",
        "Ma'rib": "Marib",
        "Taiz": "Ta'iz",
    }
    df_gov["governorate"] = df_gov["governorate"].str.strip().replace(manual_name_map)

    # Merge
    geo = geo.merge(df_gov, on="governorate", how="left")

    # User selections
    metric = st.selectbox(
        "Select metric for governorate color:",
        options=["total_facilities", "energized_facilities", "percent_energized"],
        index=2,
    )
    show_facilities = st.toggle("Show facility markers", value=True)

    # Colors and symbols
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

    # Map base
    fig = px.choropleth(
        geo,
        geojson=geo.geometry,
        locations=geo.index,
        color=metric,
        color_continuous_scale="GnBu",
        hover_name="governorate",
        custom_data=["total_facilities", "energized_facilities", "percent_energized"],
    )

    fig.update_geos(
        fitbounds="locations",
        visible=False,
        showland=True,
        showcountries=False,
        showframe=False,
    )
    fig.update_traces(marker_line_color="white", marker_line_width=0.8)

    # Overlay markers
    if show_facilities:
        for facility_type, symbol in type_symbols.items():
            subset = df_sites[df_sites["type"] == facility_type]
            hover_text = (
                "<b>Type:</b> " + subset["type"].astype(str) + "<br>" +
                "<b>Status:</b> " + subset["status"].astype(str)
            )
            fig.add_trace(go.Scattergeo(
                lon=subset["longitude"],
                lat=subset["latitude"],
                text=hover_text,
                name=facility_type,
                mode="markers",
                marker=dict(
                    size=5,
                    color=subset["status"].map(status_colors).fillna("gray"),
                    symbol=symbol,
                    line=dict(width=0.5, color="black"),
                ),
                hoverinfo="text",
                hoverlabel=dict(bgcolor="black", font_size=12, font_family="Arial"),
                legendgroup="type",
                showlegend=True,
            ))

        for status, color in status_colors.items():
            fig.add_trace(go.Scattergeo(
                lon=[None], lat=[None],
                mode="markers",
                marker=dict(size=8, color=color, symbol="circle"),
                name=f"Status: {status}",
                legendgroup="status",
                showlegend=True,
            ))

    # Layout
    fig.update_layout(
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
        legend=dict(
            title=dict(text="Facility Type & Status", font=dict(size=14, color="white")),
            orientation="h",
            yanchor="bottom",
            y=1.08,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(20, 20, 20, 0.8)",
            bordercolor="white",
            borderwidth=1.5,
        ),
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

    # Data Explorer
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
