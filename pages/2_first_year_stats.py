# pages/first_year_casualties.py

import streamlit as st
import pandas as pd
import plotly.express as px

from utils import load_all_data, show_banner

def app():
    show_banner()
    st.title("🆕 First-Year License Casualties")
    st.markdown(
        """
        **Dataset Description:**  
        This dataset provides detailed statistics on deaths and injuries in traffic accidents during the first year after obtaining a driver's license.  
        Columns:
        - **year**: Accident year  
        - **age_groups**: Age group of license holder (e.g. Less than 10, 10 - 19, 20 - 29, 30 - 39, 40 - 49, 50 - 59, 50 +, 60+)  
        - **statement**: Outcome (`Death`, `Severe injury`, `Slight injury`)  
        - **injured**: Role of injured (`Driver`, `Passenger`, `Pedestrians`)  
        - **gender**: Gender of injured person (`Male`, `Female`)  
        - **no_of_people**: Count of people
        """
    )

    # --- Data Loading & Cleaning ---
    data = load_all_data()
    df = data["first_year"].copy()
    # Harmonize the 20-29 bucket
    df["age_groups"] = df["age_groups"].replace({"20 -": "20 - 29", '50 +': '50 - 59'})

    # --- Sidebar Filters ---
    st.sidebar.header("Filters")
    years = st.sidebar.multiselect("Year", sorted(df["year"].unique()), sorted(df["year"].unique()))
    age_groups = st.sidebar.multiselect("Age Group", sorted(df["age_groups"].unique()), sorted(df["age_groups"].unique()))
    outcomes = st.sidebar.multiselect("Outcome", sorted(df["statement"].unique()), sorted(df["statement"].unique()))
    roles = st.sidebar.multiselect("Role of Injured", sorted(df["injured"].unique()), sorted(df["injured"].unique()))
    genders = st.sidebar.multiselect("Gender", sorted(df["gender"].unique()), sorted(df["gender"].unique()))

    filtered = df[
        df["year"].isin(years) &
        df["age_groups"].isin(age_groups) &
        df["statement"].isin(outcomes) &
        df["injured"].isin(roles) &
        df["gender"].isin(genders)
    ].copy()

    # --- Key Metrics ---
    total_records = int(filtered["no_of_people"].sum())
    total_deaths   = int(filtered.loc[filtered["statement"] == "Death", "no_of_people"].sum())
    total_severe   = int(filtered.loc[filtered["statement"] == "Severe injury", "no_of_people"].sum())
    total_slight   = int(filtered.loc[filtered["statement"] == "Slight injury", "no_of_people"].sum())

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Records",    f"{total_records:,}")
    c2.metric("Total Deaths",     f"{total_deaths:,}")
    c3.metric("Severe Injuries",  f"{total_severe:,}")
    c4.metric("Slight Injuries",  f"{total_slight:,}")

    st.markdown("---")

    # --- 1) Year-Over-Year Comparison ---
    st.subheader("Yearly Outcomes Comparison")
    year_outcome = (
        filtered.groupby(["year", "statement"])["no_of_people"]
        .sum()
        .reset_index()
    )
    fig_yearly = px.bar(
        year_outcome,
        x="year",
        y="no_of_people",
        color="statement",
        # change the color sequence if needed
        color_discrete_sequence=["#FF6347", "#FFFF00", "#90EE90"],  # Red, Gold, Light Green
        barmode="group",
        labels={"year": "Year", "no_of_people": "Number of People", "statement": "Outcome"},
        title="Yearly Outcomes (Death, Severe, Slight)"
    )
    st.plotly_chart(fig_yearly, use_container_width=True)

    # --- 2) Age-Group Breakdown ---
    st.subheader("Casualties by Age Group")
    age_order = [
        "Less than 10", "10 - 19", "20 - 29", "30 - 39",
        "40 - 49", "50 - 59", "60+"
    ]
    age_df = (
        filtered.groupby("age_groups")["no_of_people"]
        .sum()
        .reindex(age_order, fill_value=0)
        .reset_index()
    )
    fig_age = px.bar(
        age_df,
        x="age_groups",
        y="no_of_people",
        labels={"age_groups": "Age Group", "no_of_people": "Number of People"},
        title="First-Year Casualties by Age Group"
    )
    st.plotly_chart(fig_age, use_container_width=True)

    # --- 3) Role & Gender Insights (with Outcome) ---
    st.subheader("Casualties by Role and by Gender (with Outcomes)")
    col1, col2 = st.columns(2)

    # Role & Outcome breakdown
    role_outcome = (
        filtered
        .groupby(["injured", "statement"])["no_of_people"]
        .sum()
        .reset_index()
    )
    fig_role = px.bar(
        role_outcome,
        x="injured",
        y="no_of_people",
        color="statement",
        barmode="group",
        color_discrete_sequence=["#FF6347", "#FFFF00", "#90EE90"],  # Red, Gold, Light Green
        labels={
            "injured": "Role",
            "no_of_people": "Number of People",
            "statement": "Outcome"
        },
        title="By Role of Injured and Outcome"
    )
    col1.plotly_chart(fig_role, use_container_width=True)

    # Gender & Outcome breakdown
    gender_outcome = (
        filtered
        .groupby(["gender", "statement"])["no_of_people"]
        .sum()
        .reset_index()
    )
    fig_gender = px.bar(
        gender_outcome,
        x="gender",
        y="no_of_people",
        color="statement",
        barmode="group",
        color_discrete_sequence=["#FF6347", "#FFFF00", "#90EE90"],
        labels={
            "gender": "Gender",
            "no_of_people": "Number of People",
            "statement": "Outcome"
        },
        title="By Gender and Outcome"
    )
    col2.plotly_chart(fig_gender, use_container_width=True)


    # --- 4) Age × Outcome Heatmap ---
    st.subheader("Outcome Heatmap by Age Group (% of Age Group)")
    # First create the pivot table with raw counts
    pivot_raw = (
        filtered
        .pivot_table(
            index="age_groups",
            columns="statement",
            values="no_of_people",
            aggfunc="sum",
            fill_value=0
        )
        .reindex(index=age_order, columns=["Death", "Severe injury", "Slight injury"], fill_value=0)
    )
    
    # Calculate row totals (total per age group)
    row_totals = pivot_raw.sum(axis=1)
    
    # Create percentage pivot table (handle divide by zero)
    pivot = pivot_raw.div(row_totals, axis=0).fillna(0) * 100
    
    fig_heat = px.imshow(
        pivot,
        labels={"x": "Outcome", "y": "Age Group", "color": "Percentage (%)"},
        text_auto='.1f',  # Format to 1 decimal place
        aspect="auto",
        title="Heatmap of Outcomes by Age Group (% within each age group)"
    )
    st.plotly_chart(fig_heat, use_container_width=True)

    # --- 5) Age × Outcome Heatmap ---
    st.subheader("Role Distribution by Age Group (% within each age group)")
    # First create the pivot table with raw counts
    pivot_raw = (
        filtered
        .pivot_table(
            index="age_groups",
            columns="injured",
            values="no_of_people",
            aggfunc="sum",
            fill_value=0
        )
        .reindex(index=age_order, columns=['Driver', 'Passenger', 'Pedestrians'], fill_value=0)
    )

    # Calculate row totals (total per age group)
    row_totals = pivot_raw.sum(axis=1)

    # Create percentage pivot table (handle divide by zero)
    pivot = pivot_raw.div(row_totals, axis=0).fillna(0) * 100

    fig_heat = px.imshow(
        pivot,
        labels={"x": "Role", "y": "Age Group", "color": "Percentage (%)"},
        text_auto='.1f',  # Format to 1 decimal place
        aspect="auto",
        title="Heatmap of Roles by Age Group (% within each age group)"
    )
    st.plotly_chart(fig_heat, use_container_width=True)

    # --- 5) Drill-Down Data Table ---
    with st.expander("Show Filtered Data"):
        st.dataframe(filtered)
        st.download_button(
            "Download CSV",
            data=filtered.to_csv(index=False).encode("utf-8"),
            file_name="first_year_casualties_filtered.csv",
            mime="text/csv"
        )

# Ensure this page runs when selected
app()
