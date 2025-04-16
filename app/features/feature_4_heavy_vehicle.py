import streamlit as st
from app.stremlit_colour_pallet import MAGENTA, LIGHT_GRAY, DARK_GRAY, WHITE

def render_heavy_vehicle_explorer():
    st.title("Heavy Vehicle Pattern Explorer")
    st.markdown(
        f"""
        <style>
        .reportview-container .main .stApp {{
            background-color: {LIGHT_GRAY};
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

    st.subheader("HV Hourly Profile")
    st.write("Chart Placeholder")

    st.subheader("HV Percentage Profile")
    st.write("Chart Placeholder")

    st.subheader("Top Heavy Vehicle Stations")
    st.write("Table Placeholder")

if __name__ == '__main__':
    render_heavy_vehicle_explorer()