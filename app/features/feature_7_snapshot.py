import streamlit as st
from app.stremlit_colour_pallet import MAGENTA, LIGHT_GRAY, DARK_GRAY, WHITE

def render_lga_suburb_snapshot():
    st.title("LGA/Suburb Traffic Snapshot")
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

    st.subheader("Traffic Stations in [LGA/Suburb]")
    st.write("Map Placeholder")

    st.subheader("Area Summary")
    st.write("Summary Statistics Placeholder")

    st.subheader("Top 5 Busiest Stations")
    st.write("Table Placeholder")

    st.subheader("Distribution of Station Road Types")
    st.write("Chart Placeholder")

if __name__ == '__main__':
    render_lga_suburb_snapshot()