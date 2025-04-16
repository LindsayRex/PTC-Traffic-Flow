import streamlit as st
from app.stremlit_colour_pallet import MAGENTA, LIGHT_GRAY, DARK_GRAY, WHITE

def render_directional_flow_analysis():
    st.title("Directional Flow Analysis Dashboard")
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

    st.subheader("Average Hourly Volume by Direction")
    st.write("Chart Placeholder")

    st.subheader("Hourly Directional Split Percentage")
    st.write("Chart Placeholder")

    st.subheader("Peak Period Directional Dominance")
    st.write("Dominance Metrics Placeholder")

if __name__ == '__main__':
    render_directional_flow_analysis()