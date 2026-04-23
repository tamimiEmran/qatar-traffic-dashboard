# pages/accident_trends.py

import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
from utils import load_all_data, show_banner

def app():
    show_banner()
    st.title("🚗 Accident Trends & Characteristics")
    st.markdown(
        """
        **Dataset Description:**  
        This dataset provides detailed records of traffic accidents in Qatar, capturing the timing, environmental conditions, location, classification, and outcomes of each incident. It also includes demographic information for the at-fault driver.

        **Columns:**
        - **accident_year**: Year when the accident occurred (e.g. 2020, 2021, …, 2025)  
        - **accident_time**: Time of day of the accident in 12-hour format (e.g. “12PM”, “3AM”)  
        - **weather**: Weather conditions at the time (e.g. CLEAR, RAINY, FOGGY, HOT SUNNY)  
        - **road_status**: Surface or lighting status of the road (e.g. PAVED, WET, LIGHTED, WIDE)  
        - **road_type**: Type of roadway (INTERNAL vs. EXTERNAL)  
        - **accident_classification**: High-level category (e.g. COLLISION, RUN OVER, COUP)  
        - **accident_nature**: Detailed nature of the accident (e.g. COLLISION WITH PEDESTRIANS, OVERTURN)  
        - **accident_reason**: Primary cause flag (e.g. DRUNK, OTHER, COST)  
        - **city**: Numeric city code where the accident took place  
        - **zone**: Numeric zone code within the city  
        - **street**: Numeric street identifier (-1 indicates unknown)  
        - **accident_severity**: Severity level (e.g. SIMPLE, LIGHT INJURY, HEAVY INJURY, DEATH INJURY)  
        - **death_count**: Number of fatalities in this accident  
        - **birth_year_of_accident_perpetr**: Birth year of the at-fault driver  
        - **nationality_group_of_accident**: Nationality group of the at-fault driver (e.g. QATAR, ASIA, ARABI)  
        - **total**: Total number of people involved or injured in the accident  
        """
    )

    # --- Data Loading ---
    data = load_all_data()
    df = data["accident"]
    print(f"Loaded {len(df):,} accident records.")

    # --- Sidebar Filters ---
    st.sidebar.header("Filter Accidents")

    # Fill missing values before filtering to ensure consistency
    df["weather"] = df["weather"].fillna("unknown")
    df["road_status"] = df["road_status"].fillna("unknown")

    years = st.sidebar.multiselect(
        "Year",
        options=sorted(df["accident_year"].unique()),
        default=sorted(df["accident_year"].unique())
    )
    cities = st.sidebar.multiselect(
        "City",
        options=sorted(df["city"].unique()),
        default=sorted(df["city"].unique())
    )
    weather_opts = st.sidebar.multiselect(
        "Weather",
        options=sorted(df["weather"].unique()),
        default=sorted(df["weather"].unique())
    )
    road_status_opts = st.sidebar.multiselect(
        "Road Status",
        options=sorted(df["road_status"].unique()),
        default=sorted(df["road_status"].unique())
    )

    # Apply filters
    filtered = df[
        df["accident_year"].isin(years) &
        df["city"].isin(cities) &
        df["weather"].isin(weather_opts) &
        df["road_status"].isin(road_status_opts)
    ].copy()
    print(f"Filtered to {len(filtered):,} records based on user selections.")
    # --- Key Metrics ---
    total_accidents = len(filtered)
    total_deaths = int(filtered["death_count"].sum())
    avg_accidents_per_year = (
        filtered.groupby("accident_year").size().mean()
        if total_accidents > 0 else 0
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Accidents", f"{total_accidents:,}")
    col2.metric("Total Deaths", f"{total_deaths:,}")
    col3.metric("Avg Accidents / Year", f"{avg_accidents_per_year:.1f}")

    st.markdown("---")




    # --- Visualization: Yearly Accident Counts by Severity (Raw Counts, % Annotation, Ordered & Customized Colors) ---
    st.subheader("Accidents per Year by Severity")

    # 1) Prepare counts of each severity per year
    severity_yearly = (
        filtered
        .groupby(['accident_year', 'accident_severity'])
        .size()
        .reset_index(name='count')
    )

    # 2) Compute total accidents per year for percentage annotation
    total_per_year = severity_yearly.groupby('accident_year')['count'].transform('sum')
    severity_yearly['pct'] = severity_yearly['count'] / total_per_year * 100

    # 3) Define severity order (least to most severe) and color mapping
    severity_order = ['SIMPLE','LIGHT INJURY','HEAVY INJURY','DEATH INJURY']
    color_map = {
        'DEATH INJURY':'#8B0000','HEAVY INJURY':'#FF0000','LIGHT INJURY':'#FFA07A','SIMPLE':'#90EE90'
    }

    # 4) Build stacked bar chart of raw counts per year
    fig_severity = px.bar(
        severity_yearly,x='accident_year',y='count',color='accident_severity',
        category_orders={'accident_severity':severity_order},color_discrete_map=color_map,
        text=severity_yearly['pct'].round(1).astype(str)+'%',
        labels={'accident_year':'Year','count':'Number of Accidents','accident_severity':'Severity'},
        title='Accidents per Year by Severity (with % of Yearly Total)'
    )
    fig_severity.update_layout(barmode='stack',uniformtext_minsize=8,uniformtext_mode='hide')
    fig_severity.update_traces(textposition='inside')
    st.plotly_chart(fig_severity,use_container_width=True,key='chart_severity_yearly')
# ————————————————————————————————————————————————
    # Place this right after your yearly stacked‐bar block

    # 0) (Re)define once, up above both bar & heatmap sections
    severity_order = ['SIMPLE','LIGHT INJURY','HEAVY INJURY','DEATH INJURY']
    color_map = {
        'DEATH INJURY': '#8B0000',
        'HEAVY INJURY': '#FF0000',
        'LIGHT INJURY': '#FFA07A',
        'SIMPLE': '#90EE90'
    }

    # 1) Pivot your yearly counts into a matrix
    pivot_year = (
        severity_yearly
        .pivot(index='accident_severity', columns='accident_year', values='count')
        .reindex(severity_order)
        .fillna(0)
    )

    # 2a) Heatmap #1: % of Severity Total (rows sum to 100%)
    matrix_row_pct_year = pivot_year.div(pivot_year.sum(axis=1), axis=0) * 100
    fig_year_row = px.imshow(
        matrix_row_pct_year,
        labels={
            'x': 'Year',
            'y': 'Severity',
            'color': '% of Severity Total'
        },
        x=pivot_year.columns,
        y=pivot_year.index,
        aspect='auto',
        color_continuous_scale='Reds',
        text_auto='.1f'
    )
    st.subheader("Heatmap: % of Severity Total by Year")
    st.plotly_chart(fig_year_row, use_container_width=True, key='heatmap_year_by_severity')

    # 2b) Heatmap #2: % of Yearly Total (columns sum to 100%)
    matrix_col_pct_year = pivot_year.div(pivot_year.sum(axis=0), axis=1) * 100
    fig_year_col = px.imshow(
        matrix_col_pct_year,
        labels={
            'x': 'Year',
            'y': 'Severity',
            'color': '% of Yearly Total'
        },
        x=pivot_year.columns,
        y=pivot_year.index,
        aspect='auto',
        color_continuous_scale='Reds',
        text_auto='.1f'
    )
    st.subheader("Heatmap: % of Yearly Total by Severity")
    st.plotly_chart(fig_year_col, use_container_width=True, key='heatmap_year_by_year')

# ————————————————————————————————————————————————


    # --- Visualization: Hourly Accident Counts by Severity (Raw Counts, % Annotation, Ordered & Customized Colors) ---
    st.subheader("Accidents by Hour of Day by Severity")

    # 1) Prepare counts of each severity per hour
    severity_hourly = (
        filtered
        .dropna(subset=["accident_hour"])
        .loc[lambda df: df["accident_hour"].between(0, 23)]
        .assign(accident_hour=lambda df: df["accident_hour"].astype(int))
        .groupby(["accident_hour", "accident_severity"])  
        .size()
        .reset_index(name="count")
    )

    # 2) Compute percentage within each hour
    total_per_hour = severity_hourly.groupby("accident_hour")["count"].transform("sum")
    severity_hourly["pct"] = severity_hourly["count"] / total_per_hour * 100

    # 3) Reuse the same severity order and color mapping
    # (defined above) for consistent colors and stacking

    # 4) Plot raw-count stacked bar per hour
    fig_hour_severity = px.bar(
        severity_hourly,
        x="accident_hour",
        y="count",
        color="accident_severity",
        category_orders={
            "accident_severity": severity_order,
            "accident_hour": list(range(24))
        },
        color_discrete_map=color_map,
        text=severity_hourly["pct"].round(1).astype(str) + "%",
        labels={
            "accident_hour": "Hour of Day",
            "count": "Number of Accidents",
            "accident_severity": "Severity"
        },
        title="Accidents by Hour (0-23) by Severity (with % of Hourly Total)"
    )
    fig_hour_severity.update_layout(
        barmode="stack",
        uniformtext_minsize=8,
        uniformtext_mode="hide"
    )
    fig_hour_severity.update_traces(textposition="inside")
    fig_hour_severity.update_xaxes(dtick=1)
    st.plotly_chart(
        fig_hour_severity,
        use_container_width=True,
        key="chart_severity_hourly"
    )









    # … assume you’ve already loaded and filtered your `filtered` DataFrame …

    st.subheader("Accident Counts by Birth-Year Decade, Nationality & Severity")

    # 1) Filter out missing birth years and convert to int
    df_birth = (
        filtered
        .dropna(subset=["birth_year_of_accident_perpetr"])
        .copy()
    )
    df_birth["birth_year_of_accident_perpetr"] = df_birth["birth_year_of_accident_perpetr"].astype(int)

    # 2) Clamp to a realistic range: 1900 → current year
    current_year = datetime.datetime.now().year
    df_birth = df_birth.loc[
        (df_birth["birth_year_of_accident_perpetr"] >= 1900) &
        (df_birth["birth_year_of_accident_perpetr"] <= current_year)
    ]

    # 3) Compute decade-based bins from the cleaned data
    min_year = (df_birth["birth_year_of_accident_perpetr"].min() // 10) * 10
    max_year = ((df_birth["birth_year_of_accident_perpetr"].max() // 10) + 1) * 10
    bins = list(range(min_year, max_year + 1, 10))
    labels = [f"{b}-{b+9}" for b in bins[:-1]]
    df_birth["birth_bin"] = pd.cut(
        df_birth["birth_year_of_accident_perpetr"],
        bins=bins,
        labels=labels,
        right=False
    )

    # 4) Ensure nationality is a string (no NaNs)
    df_birth["nationality_group_of_accident"] = (
        df_birth["nationality_group_of_accident"]
        .fillna("Unknown")
        .astype(str)
    )

    # 5) Aggregate accident counts by (birth_bin, nationality, severity)
    agg = (
        df_birth
        .groupby(["birth_bin", "nationality_group_of_accident", "accident_severity"])
        .size()
        .reset_index(name="count")
    )
    # normalize by the nationality group to get percentages
    agg["pct"] = agg.groupby("birth_bin")["count"].transform(lambda x: x / x.sum() * 100)
    # 6) Define severity order and color mapping
    severity_order = ["SIMPLE", "LIGHT INJURY", "HEAVY INJURY", "DEATH INJURY"]
    color_map = {
        "DEATH INJURY": "#8B0000",
        "HEAVY INJURY": "#FF0000",
        "LIGHT INJURY": "#FFA07A",
        "SIMPLE": "#90EE90",
    }

    # 7) Build the bubble chart
    fig = px.scatter(
        agg,
        x="birth_bin",
        y="nationality_group_of_accident",
        size="pct",
        color="accident_severity",
        category_orders={
            "birth_bin": labels,
            "accident_severity": severity_order
        },
        color_discrete_map=color_map,
        size_max=30,
        labels={
            "birth_bin": "Birth-Year Bin",
            "nationality_group_of_accident": "Nationality",
            "count": "Accident Count",
            "accident_severity": "Severity"
        },
        title="Accident Counts by Birth-Year Decade, Nationality & Severity"
    )

    # 8) Tidy up axes
    fig.update_xaxes(tickangle=45)
    fig.update_yaxes(
        categoryorder="array",
        categoryarray=sorted(agg["nationality_group_of_accident"].unique())
    )

    # 9) Render
    st.plotly_chart(fig, use_container_width=True)
























    # 1) Choose which field to analyze
    category_cols = [
        "road_status",
        "road_type",
        "weather",
        "accident_classification",
        "accident_nature",
        "accident_severity",
        "accident_reason",
        "nationality_group_of_accident"
    ]
    field = st.selectbox(
        "Select categorical field",
        options=category_cols,
        index=category_cols.index("road_status")
    )

    # 2) Compute unknown / missing
    mask_unknown = (
        filtered[field].isna() |
        (filtered[field].astype(str).str.lower() == "unknown")
    )
    unknown_count = int(mask_unknown.sum())
    total_count = len(filtered)
    unknown_pct = (unknown_count / total_count * 100) if total_count else 0

    # 3) Display unknowns
    st.subheader(
        f"Unknown {field.replace('_',' ').title()}: "
        f"{unknown_count:,} ({unknown_pct:.1f}%)"
    )

    # 4) Build counts for the rest
    counts_df = (
        filtered.loc[~mask_unknown, field]
        .value_counts()
        .reset_index(name="total_accidents")
        .rename(columns={"index": field})
    )

    # 4a) If not severity field, compute SIMPLE % per category
    if field != "accident_severity":
        # count SIMPLE within each category
        simple_counts = (
            filtered.loc[~mask_unknown]
            .assign(is_simple=lambda df: df["accident_severity"] == "SIMPLE")
            .groupby(field)["is_simple"]
            .sum()
            .reindex(counts_df[field])
            .fillna(0)
            .astype(int)
            .values
        )
        counts_df["simple_accidents"] = simple_counts
        counts_df["pct_simple"] = counts_df["simple_accidents"] / counts_df["total_accidents"] * 100

    # 5) Plot if there’s data
    if not counts_df.empty:
        fig = px.bar(
            counts_df,
            x=field,
            y="total_accidents",
            labels={
                field: field.replace("_"," ").title(),
                "total_accidents": "Number of Accidents"
            },
            title=f"Accidents by {field.replace('_',' ').title()}"
        )

        # 6) Annotate % SIMPLE when appropriate
        if field != "accident_severity":
            fig.update_traces(
                text=counts_df["pct_simple"].round(1).astype(str) + " %",
                textposition="outside"
            )
            fig.update_layout(uniformtext_minsize=8, uniformtext_mode="hide")

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(f"No data available for '{field}' (excluding unknown/missing).")


    # --- (Optional) Data Table Download ---
    with st.expander("Show filtered raw data"):
        st.write(f"{len(filtered):,} rows")
        st.dataframe(filtered)
        st.download_button(
            label="Download CSV",
            data=filtered.to_csv(index=False).encode("utf-8"),
            file_name="filtered_accidents.csv",
            mime="text/csv"
        )

# Streamlit will pick up this file automatically in the /pages/ folder.
app()  # Call the app function to run the page