import streamlit as st
import pandas as pd
import geopandas as gpd
import json
import plotly.express as px
from pathlib import Path
from utils import load_all_data,show_banner

_GEOJSON_PATH = Path(__file__).resolve().parent.parent / "qatar_zones.geojson"


def app():
    show_banner()
    st.title("🗺️ Accidents by Zone & Severity")
    st.markdown(
        """
        This page visualizes how many traffic accidents occurred in each zone of Qatar,
        and lets you drill into severity levels.  
        Zones come from `qatar_zones.geojson` (GeoJSON FeatureCollection with
        `properties.zone_number` & `properties.zone_name`).
        """
    )

    # --- Load accident data ---
    data = load_all_data()
    df = data["accident"].copy()

    # Fill missing zone and ensure int
    df["zone"] = df["zone"].fillna(-1).astype(int)

    # --- Sidebar filters ---
    st.sidebar.header("Filters")
    years = sorted(df["accident_year"].unique())
    sel_years = st.sidebar.multiselect("Year", years, default=years)
    df = df[df["accident_year"].isin(sel_years)]

    severity_order = ["SIMPLE", "LIGHT INJURY", "HEAVY INJURY", "DEATH INJURY"]

    # --- Compute total accidents per zone ---
    total_counts = (
        df.groupby("zone").size()
         .reset_index(name="total")
    )
    total_counts["zone"] = total_counts["zone"].astype(str)

    # --- Load Qatar zones GeoJSON ---
    gdf = gpd.read_file(str(_GEOJSON_PATH))
    with open(str(_GEOJSON_PATH), "r", encoding="utf-8") as f:
        zones_geo = json.load(f)

    # Prepare GeoDataFrame
    gdf["zone"] = gdf["zone_number"].astype(str)
    merged_total = gdf.merge(total_counts, on="zone", how="left")
    merged_total["total"] = merged_total["total"].fillna(0).astype(int)

    # --- Map: Total Accidents per Zone ---
    st.subheader("🗺️ Map: Total Accidents per Zone")
    fig_map = px.choropleth_mapbox(
        merged_total,
        geojson=zones_geo,
        locations="zone",
        featureidkey="properties.zone_number",
        color="total",
        color_continuous_scale="OrRd",
        range_color=(0, merged_total["total"].max()),
        mapbox_style="carto-positron",
        zoom=9,
        center={"lat": 25.2854, "lon": 51.5310},
        opacity=0.6,
        labels={"total": "Accident Count"}
    )
    fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    st.plotly_chart(fig_map, use_container_width=True)

    # --- Bar chart: Total by Zone ---
    st.subheader("📊 Total Accidents by Zone")
    bar_df = (
        merged_total[["zone_name", "total"]]
         .sort_values("total", ascending=False)
         .rename(columns={"zone_name": "Zone", "total": "Accident Count"})
    )
    fig_bar = px.bar(
        bar_df,
        x="Zone",
        y="Accident Count",
        text="Accident Count",
        title="Total Accidents per Zone"
    )
    fig_bar.update_traces(textposition="outside")
    fig_bar.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_bar, use_container_width=True)

    # --- Percentage maps by severity (normalized by global severity totals) ---
    st.markdown("---")
    st.subheader("🗺️ Accident Severity Distribution Across Zones")

    # Compute counts per zone & severity
    zone_sev = (
        df.groupby(["zone", "accident_severity"]).size()
         .reset_index(name="count")
    )
    zone_sev["zone"] = zone_sev["zone"].astype(str)

    # Compute global totals per severity
    global_totals = (
        zone_sev.groupby("accident_severity")["count"].sum()
         .rename("global_total")
         .reset_index()
    )

    # Merge global totals to zone-level
    pct_df = zone_sev.merge(global_totals, on="accident_severity", how="left")
    pct_df["pct_of_severity"] = pct_df["count"] / pct_df["global_total"] * 100

    tabs = st.tabs(severity_order)
    for tab, sev in zip(tabs, severity_order):
        with tab:
            tmp = pct_df[pct_df["accident_severity"] == sev][["zone", "pct_of_severity"]]
            gdf_sev = gdf.merge(tmp, on="zone", how="left")
            gdf_sev["pct_of_severity"] = gdf_sev["pct_of_severity"].fillna(0)

            fig = px.choropleth_mapbox(
                gdf_sev,
                geojson=zones_geo,
                locations="zone",
                featureidkey="properties.zone_number",
                color="pct_of_severity",
                color_continuous_scale="Viridis",
                range_color=(0, 100),
                mapbox_style="carto-positron",
                zoom=9,
                center={"lat": 25.2854, "lon": 51.5310},
                opacity=0.6,
                labels={"pct_of_severity": f"% of {sev}"}
            )
            fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
            st.plotly_chart(fig, use_container_width=True)

    # --- Raw table & download ---
    with st.expander("Show raw distributions by zone"):  
        out = (
            pct_df.pivot(index="zone", columns="accident_severity", values="pct_of_severity")
             .fillna(0)
             .reset_index()
        )
        out = out.merge(
            gdf[["zone", "zone_name"]], on="zone"
        ).set_index("zone_name")
        st.dataframe(out)
        st.download_button(
            "Download distributions as CSV",
            data=out.to_csv().encode("utf-8"),
            file_name="zone_severity_distribution.csv",
            mime="text/csv"
        )

app()
