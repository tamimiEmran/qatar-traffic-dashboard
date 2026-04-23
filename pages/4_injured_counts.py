# pages/accident_cause_casualties.py

import streamlit as st
import pandas as pd
import plotly.express as px

from utils import load_all_data,show_banner

def app():
    show_banner()
    st.title("💥 Accident Cause & Casualties")
    st.markdown(
        """
        **Dataset Description:**  
        This dataset provides detailed statistics on traffic accident casualties in Qatar, categorized by the primary cause of the accident, the gender of the driver, and the role of the affected person (e.g., driver, passenger, pedestrian).

        **Columns:**
        - **year**: The year of the data (2022, 2023).
        - **accident_cause**: The main cause of the traffic accident (e.g., 'Two-vehicle Collision', 'Vehicle-pedestrian Collision').
        - **gender**: Gender of the driver involved ('Male', 'Female').
        - **affected_person_location**: Role of the casualty ('Driver', 'Passenger', 'Pedestrians').
        - **result_of_the_accident**: The outcome of the accident ('Death', 'Severe Injury', 'Slight Injury').
        - **number_of_people**: The count of individuals for that specific combination of categories.
        """
    )

    # --- Data Loading & Preparation ---
    data = load_all_data()
    # Use a short, descriptive key for the dataset
    df = data["by_cause"].copy()
    
    # --- Data Cleaning & Preparation ---
    # Define a logical order for plotting. Reversing the order to have 'Slight Injury' at the bottom of stacked bars.
    result_order = ['Death', 'Severe Injury', 'Slight Injury'][::-1]
    
    # Get a sorted list of unique accident causes for the filter and charts
    cause_order = sorted(df["accident_cause"].unique())

    # --- Sidebar Filters ---
    st.sidebar.header("Filter Casualties")

    years = st.sidebar.multiselect(
        "Year",
        options=sorted(df["year"].unique()),
        default=sorted(df["year"].unique())
    )
    causes = st.sidebar.multiselect(
        "Accident Cause",
        options=cause_order,
        default=cause_order
    )
    genders = st.sidebar.multiselect(
        "Gender of Driver",
        options=sorted(df["gender"].unique()),
        default=sorted(df["gender"].unique())
    )
    locations = st.sidebar.multiselect(
        "Affected Person's Location",
        options=sorted(df["affected_person_location"].unique()),
        default=sorted(df["affected_person_location"].unique())
    )
    results = st.sidebar.multiselect(
        "Result of Accident",
        options=result_order,
        default=result_order
    )

    # --- Apply Filters ---
    filtered = df[
        df["year"].isin(years) &
        df["accident_cause"].isin(causes) &
        df["gender"].isin(genders) &
        df["affected_person_location"].isin(locations) &
        df["result_of_the_accident"].isin(results)
    ].copy()

    # --- Key Metrics ---
    if not filtered.empty:
        total_people = int(filtered['number_of_people'].sum())
        total_deaths = int(filtered.loc[filtered['result_of_the_accident'] == 'Death', 'number_of_people'].sum())
        total_severe = int(filtered.loc[filtered['result_of_the_accident'] == 'Severe Injury', 'number_of_people'].sum())
        total_slight = int(filtered.loc[filtered['result_of_the_accident'] == 'Slight Injury', 'number_of_people'].sum())
    else:
        total_people, total_deaths, total_severe, total_slight = 0, 0, 0, 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Casualties", f"{total_people:,}")
    c2.metric("Deaths", f"{total_deaths:,}")
    c3.metric("Severe Injuries", f"{total_severe:,}")
    c4.metric("Slight Injuries", f"{total_slight:,}")

    st.markdown("---")

    # --- Visualizations ---
    if not filtered.empty:
        # 1. Accident Outcome by Cause (Stacked Bar Chart)
        st.subheader("Accident Outcome by Cause")
        cause_outcome_agg = (
            filtered.groupby(["accident_cause", "result_of_the_accident"])["number_of_people"]
            .sum()
            .reset_index()
        )
        fig_cause_outcome = px.bar(
            cause_outcome_agg,
            x="accident_cause",
            y="number_of_people",
            color="result_of_the_accident",
            barmode="stack",
            labels={
                "accident_cause": "Accident Cause",
                "number_of_people": "Number of Casualties",
                "result_of_the_accident": "Accident Outcome"
            },
            title="Breakdown of Accident Outcomes by Cause",
            category_orders={
                "accident_cause": cause_order,
                "result_of_the_accident": result_order
            }
        )
        st.plotly_chart(fig_cause_outcome, use_container_width=True)

        # 2. Heatmap Breakdowns by Accident Cause
        st.subheader("Breakdowns by Gender and Location for Each Accident Cause")

        # Calculate total casualties per accident cause for normalization
        cause_totals = filtered.groupby("accident_cause")["number_of_people"].sum().to_dict()

        # -- Heatmap 1: Cause vs. Gender --
        st.write("#### Distribution by Accident Cause per Gender (%)")
        gender_heatmap_df = filtered.groupby(["accident_cause", "gender"])["number_of_people"].sum().reset_index()
        
        # Calculate total casualties per gender for normalization
        gender_totals = filtered.groupby("gender")["number_of_people"].sum().to_dict()
        
        gender_heatmap_df["percentage"] = gender_heatmap_df.apply(
            lambda row: (row["number_of_people"] / gender_totals.get(row["gender"], 0)) * 100 
            if gender_totals.get(row["gender"], 0) > 0 else 0,
            axis=1
        )
        
        gender_pivot = gender_heatmap_df.pivot_table(
            index="accident_cause", columns="gender", values="percentage", fill_value=0
        ).reindex(index=cause_order, fill_value=0)
        
        fig_gender_heatmap = px.imshow(
            gender_pivot,
            labels={"x": "Driver's Gender", "y": "Accident Cause", "color": "% of Gender Total"},
            text_auto=".1f",
            aspect="auto",
            title="Accident Cause Distribution within each Gender"
        )
        st.plotly_chart(fig_gender_heatmap, use_container_width=True)

        # -- Heatmap 2: Cause vs. Location --
        st.write("#### Distribution by Affected Person's Location (%)")
        location_heatmap_df = filtered.groupby(["accident_cause", "affected_person_location"])["number_of_people"].sum().reset_index()
        location_heatmap_df["percentage"] = location_heatmap_df.apply(
            lambda row: (row["number_of_people"] / cause_totals.get(row["accident_cause"], 0)) * 100 
            if cause_totals.get(row["accident_cause"], 0) > 0 else 0,
            axis=1
        )
        location_pivot = location_heatmap_df.pivot_table(
            index="accident_cause", columns="affected_person_location", values="percentage", fill_value=0
        ).reindex(index=cause_order, fill_value=0)
        fig_location_heatmap = px.imshow(
            location_pivot,
            labels={"x": "Affected Person's Location", "y": "Accident Cause", "color": "% of Cause Total"},
            text_auto=".1f",
            aspect="auto",
            title="Location Distribution of Casualties within each Accident Cause"
        )
        st.plotly_chart(fig_location_heatmap, use_container_width=True)
        
    else:
        st.warning("No data available for the selected filters. Please adjust your selections.")

    # --- Data Table Expander ---
    with st.expander("Show Filtered Raw Data"):
        st.write(f"Displaying {len(filtered):,} rows of aggregated data")
        st.dataframe(filtered)
        st.download_button(
            label="Download Filtered Data as CSV",
            data=filtered.to_csv(index=False).encode("utf-8"),
            file_name="accident_cause_casualties_filtered.csv",
            mime="text/csv"
        )

app()