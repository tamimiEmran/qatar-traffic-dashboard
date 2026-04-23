import streamlit as st
from utils import load_all_data, show_banner
show_banner()

# --- App Configuration ---
st.set_page_config(
    page_title="Qatar Traffic Analysis Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Load Data ---
data = load_all_data()

# --- Home Content ---
st.title("Qatar Traffic Analysis Dashboard")
st.markdown(
    """
    ---
    ### 📊 Available Datasets & Pages

    1. **Traffic Accidents Dataset**  
       📄 **Page:** `accident trends`  
       A comprehensive record of traffic accidents including accident time, weather conditions, road types, causes, severity, and detailed location data. This dataset helps identify patterns and hotspots for traffic incidents.

    2. **Deaths & Injuries During First Year of License Issuance**  
       📄 **Page:** `first year stats`  
       Statistics on deaths and injuries occurring during the first year after license issuance, categorized by age group, gender, and role of the injured person (driver, passenger, pedestrian).

    3. **Deaths & Injuries by Driver Experience**  
       📄 **Page:** `driver experience`  
       Analysis of how driver experience levels (from “Without A License” up to “20 Years and Above”) affect accident outcomes, broken down by gender and whether the injured was a driver, passenger, or pedestrian.

    4. **Deaths & Injuries by Accident Cause**  
       📄 **Page:** `injured counts`  
       Detailed casualty counts for each accident cause (e.g., two-vehicle collisions, vehicle-pedestrian collisions, overturning), with filters for affected person location and gender.

    ---
    ### 📌 How to Use This Dashboard
    - Select a page from the sidebar to jump into that dataset's analysis view.  
    - Each page offers interactive filters and charts for deep dives.  
    - Explore trends in accident severity, causes, demographics, and more.
    """
)
