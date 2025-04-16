import streamlit as st
from app.stremlit_colour_pallet import MAGENTA, LIGHT_GRAY, DARK_GRAY, WHITE

def render_hierarchy_benchmarking():
    st.title("Road Hierarchy Traffic Benchmarking")
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

    st.subheader("Volume Distribution by Road Hierarchy")
    st.write("Chart Placeholder")

    st.subheader("Typical Weekday Hourly Profile by Road Hierarchy")
    st.write("Chart Placeholder")

if __name__ == '__main__':
    render_hierarchy_benchmarking()