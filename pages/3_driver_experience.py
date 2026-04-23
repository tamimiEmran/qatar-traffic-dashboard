# pages/driver_experience_casualties.py

import streamlit as st
import pandas as pd
import plotly.express as px

from utils import load_all_data,show_banner

def app():
    show_banner()
    st.title("👨‍✈️ Driver Experience & Casualties")
    st.markdown(
        """
        **Dataset Description:**  
        This dataset provides detailed statistics on traffic accident casualties in Qatar, categorized by the driver's experience level, gender, and the role of the affected person (e.g., driver, passenger, pedestrian).

        **Columns:**
        - **year**: The year of the data (2022, 2023).
        - **driver_s_experience**: Driving experience level of the person at fault (e.g., 'Without A License', '1 Year to 2 Years').
        - **gender**: Gender of the driver ('Male', 'Female').
        - **affected_person_location**: Role of the casualty ('Driver', 'Passenger', 'Pedestrians').
        - **result_of_the_accident**: Outcome of the accident ('Death', 'Severe Injury', 'Slight Injury').
        - **number_of_people**: The count of individuals for that specific combination of categories.
        """
    )

    # --- Data Loading & Preparation ---
    data = load_all_data()
    # Assuming the dataset ID in the loading utility is 'driver_experience_casualties'
    df = data["by_experience"].copy()
    
    # --- Data Cleaning & Preparation ---
    # Correcting typo in the dataset
    df['result_of_the_accident'] = df['result_of_the_accident'].replace({'Sever Injury': 'Severe Injury'})

    # Defining a logical order for categorical columns to ensure plots are sorted meaningfully
    experience_order = [
        'Without A License', 'Less than One Year', '1 Year to 2 Years',
        '2 Years to 4 Years', '4 Years to 6 Years', '6 Years to 8 Years',
        '8 Years to 10 Years', '10 Years to 15 Years', '15 Years to 20 Years',
        '20 Years and Above'
    ]
    result_order = ['Death', 'Severe Injury', 'Slight Injury'][::-1]

    # --- Sidebar Filters ---
    st.sidebar.header("Filter Casualties")

    years = st.sidebar.multiselect(
        "Year",
        options=sorted(df["year"].unique()),
        default=sorted(df["year"].unique())
    )
    experiences = st.sidebar.multiselect(
        "Driver's Experience",
        options=experience_order, # Use the defined order for the filter
        default=experience_order
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
        options=result_order, # Use the defined order
        default=result_order
    )

    # --- Apply Filters ---
    filtered = df[
        df["year"].isin(years) &
        df["driver_s_experience"].isin(experiences) &
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
        # 1. Heatmap: Driver's Experience vs. Gender (Percentage of Gender Total)

        # 2. Driver Experience vs. Accident Outcome (Stacked Bar Chart)
        st.subheader("Accident Outcome by Driver's Experience")
        exp_outcome_agg = (
            filtered.groupby(["driver_s_experience", "result_of_the_accident"])["number_of_people"]
            .sum()
            .reset_index()
        )
        fig_exp_outcome = px.bar(
            exp_outcome_agg,
            x="driver_s_experience",
            y="number_of_people",
            color="result_of_the_accident",
            barmode="stack",
            labels={
                "driver_s_experience": "Driver's Experience",
                "number_of_people": "Number of Casualties",
                "result_of_the_accident": "Accident Outcome"
            },
            title="Breakdown of Accident Outcomes by Driver Experience",
            category_orders={
                "driver_s_experience": experience_order,
                "result_of_the_accident": result_order
            }
        )
        st.plotly_chart(fig_exp_outcome, use_container_width=True)
        st.subheader("Driver's Experience vs. Gender (Percentage of Gender Total)")
        # Aggregate number of people by experience and gender
        exp_gender_agg = (
            filtered.groupby(["driver_s_experience", "gender"])["number_of_people"]
            .sum()
            .reset_index()
        )
        # Calculate total casualties per gender
        gender_totals = exp_gender_agg.groupby("gender")["number_of_people"].sum().to_dict()
        # Calculate percentage for each cell
        exp_gender_agg["percentage"] = exp_gender_agg.apply(
            lambda row: (row["number_of_people"] / gender_totals[row["gender"]]) * 100 if gender_totals[row["gender"]] > 0 else 0,
            axis=1
        )
        # Pivot for heatmap
        heatmap_data = exp_gender_agg.pivot(
            index="driver_s_experience",
            columns="gender",
            values="percentage"
        ).reindex(index=experience_order, fill_value=0)
        fig_exp_gender = px.imshow(
            heatmap_data,
            labels={"x": "Gender", "y": "Driver's Experience", "color": "% of Gender Total"},
            text_auto=".1f",
            aspect="auto",
            title="Percentage of Casualties by Driver's Experience and Gender"
        )
        st.plotly_chart(fig_exp_gender, use_container_width=True)

        # 3. Breakdown by Gender and Affected Person Location (Side-by-side charts)

        # 4. Heatmap: Driver Experience vs. Affected Person Location
        st.subheader("Heatmap: Driver Experience vs. Affected Person's Location")

        # Calculate total casualties by driver experience
        exp_totals = filtered.groupby("driver_s_experience")["number_of_people"].sum().to_dict()

        # Create a DataFrame for the percentage calculation
        heatmap_df = filtered.groupby(["driver_s_experience", "affected_person_location"])["number_of_people"].sum().reset_index()

        # Calculate percentage of each affected person location within each driver experience level
        heatmap_df["percentage"] = heatmap_df.apply(
            lambda row: (row["number_of_people"] / exp_totals[row["driver_s_experience"]]) * 100 
            if exp_totals[row["driver_s_experience"]] > 0 else 0,
            axis=1
        )

        # Create pivot table for the heatmap with percentages
        heatmap_pivot = heatmap_df.pivot_table(
            index="driver_s_experience",
            columns="affected_person_location",
            values="percentage",
            fill_value=0
        ).reindex(index=experience_order, fill_value=0)

        # Create the heatmap visualization
        fig_heatmap = px.imshow(
            heatmap_pivot,
            labels={"x": "Affected Person's Location", "y": "Driver's Experience", "color": "% of Driver Experience Total"},
            text_auto=".1f",  # Show one decimal place for percentages
            aspect="auto",
            title="Distribution of Casualties by Location for Each Driver Experience Level (%)"
        )

        st.plotly_chart(fig_heatmap, use_container_width=True)

    else:
        st.warning("No data available for the selected filters. Please adjust your selections.")

    # --- Data Table Expander ---
    with st.expander("Show Filtered Raw Data"):
        st.write(f"Displaying {len(filtered):,} rows of aggregated data")
        st.dataframe(filtered)
        st.download_button(
            label="Download Filtered Data as CSV",
            data=filtered.to_csv(index=False).encode("utf-8"),
            file_name="driver_experience_casualties_filtered.csv",
            mime="text/csv"
        )

app()