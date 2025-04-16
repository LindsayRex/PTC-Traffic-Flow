import streamlit as st
from app.stremlit_colour_pallet import MAGENTA, LIGHT_GRAY, DARK_GRAY, WHITE

def render_station_profile():
    st.title("Traffic Station Profile Dashboard")
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

    st.markdown(f"<h3 style='color:{MAGENTA};'>Station Metadata: [Station ID]</h3>", unsafe_allow_html=True)
    st.write("Road Name: [Road Name]")
    st.write("LGA: [LGA]")
    st.write("Suburb: [Suburb]")
    st.write("Road Functional Hierarchy: [Hierarchy]")
    st.write("Device Type: [Device Type]")
    st.write("Vehicle Classifier Status: [Yes/No]")
    st.write("Permanent Station Status: [Yes/No]")
    st.write("Quality Rating: [Rating]")

    st.subheader("Location: [Station ID]")
    st.write("Map Placeholder")

    st.subheader("Typical Hourly Traffic Profile")
    st.write("Chart Placeholder")

    st.subheader("Recent Daily Volume Trend")
    st.write("Chart Placeholder")

if __name__ == '__main__':
    render_station_profile()