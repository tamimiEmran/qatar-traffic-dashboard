import pandas as pd
import streamlit as st
import re


def _validate_schema(df: pd.DataFrame, expected_cols: list[str]) -> None:
    """
    Ensure the DataFrame contains all expected columns.
    """
    missing = set(expected_cols) - set(df.columns)
    if missing:
        raise ValueError(f"Missing expected columns: {missing}")


def _clean_accident_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Perform cleaning and derive new fields for the accident dataset.
    """
    # Replace invalid street/zone codes with NaN
    for col in ['street', 'zone']:
        if col in df.columns:
            df[col] = df[col].replace(-1, pd.NA)

    # Extract accident hour in 24-hour format from time (e.g., '12PM' -> 12, '1AM' -> 1, '1PM' -> 13)
    if 'accident_time' in df.columns:
        # map the accident_time to 24-hour format
        print(len(df['accident_time'].unique()), "unique accident times found.")
        mapping = {
            '12AM': 0, '1AM': 1, '2AM': 2, '3AM': 3, '4AM': 4,
            '5AM': 5, '6AM': 6, '7AM': 7, '8AM': 8, '9AM': 9,
            '10AM': 10, '11AM': 11, '12PM': 12, '1PM': 13,
            '2PM': 14, '3PM': 15, '4PM': 16, '5PM': 17,
            '6PM': 18, '7PM': 19, '8PM': 20, '9PM': 21,
            '10PM': 22, '11PM': 23
        }
        df['accident_hour'] = df['accident_time'].map(mapping)
        print(len(df['accident_hour'].unique()), "uniques after converting.")

    # Compute perpetrator age from birth year
    if 'birth_year_of_accident_perpetr' in df.columns:
        current_year = pd.Timestamp.now().year
        df['perpetrator_age'] = current_year - df['birth_year_of_accident_perpetr']

    return df


@st.cache_data
def load_accident_data(filepath: str) -> pd.DataFrame:
    """
    Load the 'accident' dataset, validate schema, and preprocess.
    """
    # Define expected schema
    expected_cols = [
        'accident_year', 'accident_time', 'weather', 'road_status', 'road_type',
        'accident_classification', 'accident_nature', 'accident_reason',
        'city', 'zone', 'street', 'accident_severity', 'death_count',
        'birth_year_of_accident_perpetr', 'nationality_group_of_accident', 'total'
    ]
    df = pd.read_csv(filepath)
    _validate_schema(df, expected_cols)
    return _clean_accident_data(df)


@st.cache_data
def load_first_year_license_stats(filepath: str) -> pd.DataFrame:
    """
    Load and validate the first-year license injury/fatality stats.
    """
    expected_cols = ['year', 'age_groups', 'statement', 'injured', 'gender', 'no_of_people']
    df = pd.read_csv(filepath)
    _validate_schema(df, expected_cols)
    return df


@st.cache_data
def load_cause_stats(filepath: str) -> pd.DataFrame:
    """
    Load and validate accidents-by-cause stats.
    """
    expected_cols = [
        'year', 'accident_cause', 'affected_person_location',
        'gender', 'result_of_the_accident', 'number_of_people'
    ]
    df = pd.read_csv(filepath)
    _validate_schema(df, expected_cols)
    return df


@st.cache_data
def load_experience_stats(filepath: str) -> pd.DataFrame:
    """
    Load and validate accidents-by-driver-experience stats.
    """
    expected_cols = [
        'year', 'driver_s_experience', 'gender',
        'affected_person_location', 'result_of_the_accident', 'number_of_people'
    ]
    df = pd.read_csv(filepath)
    _validate_schema(df, expected_cols)
    return df


def filter_dataframe(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    """
    Apply a set of global filters to any DataFrame.
    filters: {
      'year': list[int],
      'city': list[int],
      'gender': list[str],
      'age_range': (int, int),
      ...
    }
    """
    filtered = df.copy()
    # Example: year filter
    if 'year' in filters:
        filtered = filtered[filtered['year'].isin(filters['year'])]
    # Additional filters can be applied similarly
    return filtered


@st.cache_data
def load_all_data(
    accident_fp: str = None,
    first_year_fp: str = None,
    cause_fp: str = None,
    experience_fp: str = None
) -> dict[str, pd.DataFrame]:
    _data_dir = Path(__file__).resolve().parent / "data"
    if accident_fp is None:
        accident_fp = str(_data_dir / "accident.csv")
    if first_year_fp is None:
        first_year_fp = str(_data_dir / "deaths-and-injuries-in-traffic-accidents-during-the-first-year-of-license-issuance-by-age-group-gender-and-role-of-injured.csv")
    if cause_fp is None:
        cause_fp = str(_data_dir / "number-of-deaths-and-injuries-from-traffic-accidents-by-accident-cause-affected-person-location-and-gender.csv")
    if experience_fp is None:
        experience_fp = str(_data_dir / "number-of-deaths-and-injuries-from-traffic-accidents-by-driver-experience-gender-and-affected-person-location.csv")
    """
    Load every traffic-safety dataset at once.
    Returns a dict with four DataFrames.
    """
    accident_df     = load_accident_data(accident_fp)
    first_year_df   = load_first_year_license_stats(first_year_fp)
    cause_df        = load_cause_stats(cause_fp)
    experience_df   = load_experience_stats(experience_fp)
    return {
        "accident":     accident_df,
        "first_year":   first_year_df,
        "by_cause":     cause_df,
        "by_experience":experience_df
    }
# utils.py
# utils.py
import streamlit as st, base64, os

# utils.py
import streamlit as st
import base64, os
from pathlib import Path
def show_banner():
    logos = ["MOI.png", "mowasalat.png", "traffic.png"]
    b64s = []
    repo_root = Path(__file__).resolve().parent

    # Load and encode logos
    for fn in logos:
        full_path = repo_root / fn
        if not full_path.exists():
            st.error(f"🚨 Banner logo not found: {full_path}")
            return
        with open(full_path, "rb") as f:
            b64s.append(base64.b64encode(f.read()).decode())

    # HTML + CSS for banner with logos and text
    html = f"""
    <style>
      .banner {{
        position: fixed; top: 0; left: 0;
        width: 100%; background: #fff;
        border-top: 8px solid #8A1538;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        z-index: 9999;
        display: flex; justify-content: space-around; align-items: center;
        height: 160px;
      }}
      .banner .logo-item img {{
        height: 140px; margin: 0 20px;
        filter: grayscale(30%);
        transition: transform 0.2s ease, filter 0.2s ease;
      }}
      .banner .logo-item img:hover {{
        transform: scale(1.15); filter: grayscale(0%);
      }}
      .banner .text-item {{
        text-align: center; margin: 0 40px;
      }}
      .banner .main-text {{
        font-size: 20px; font-weight: 600; color: #333;
        margin-bottom: 4px;
      }}
      .banner .sub-text {{
        font-size: 14px; color: #555;
      }}
      /* Push all Streamlit content down */
      html, body, [data-testid="stAppViewContainer"] {{
        padding-top: 200px !important;
      }}
    </style>

    <div class="banner">
      <div class="logo-item">
        <img src="data:image/png;base64,{b64s[0]}" />
      </div>
      <div class="text-item">
        <div class="main-text">Qatar Traffic Safety Dashboard</div>
        <div class="sub-text">لوحة تحليل السلامة المرورية في قطر</div>
      </div>
      <div class="logo-item">
        <img src="data:image/png;base64,{b64s[1]}" />
      </div>
      <div class="logo-item">
        <img src="data:image/png;base64,{b64s[2]}" />
      </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)