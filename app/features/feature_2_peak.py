import streamlit as st
from app.stremlit_colour_pallet import MAGENTA, LIGHT_GRAY, DARK_GRAY, WHITE

def render_peak_analysis():
    st.title("Peak Hour Analysis View")
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

    st.subheader("Average Weekday Hourly Profile")
    st.write("Chart Placeholder")

    st.subheader("Average Peak Period Volumes")
    st.write("Table Placeholder")

if __name__ == '__main__':
    render_peak_analysis()