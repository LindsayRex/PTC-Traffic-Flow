import streamlit as st
from app.stremlit_colour_pallet import MAGENTA, LIGHT_GRAY, DARK_GRAY, WHITE

def render_weekday_weekend_comparison():
    st.title("Weekday vs. Weekend Traffic Comparison")
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

    st.subheader("Hourly Profiles")
    st.write("Chart Placeholder")

    st.subheader("Key Metrics")
    st.write("Table Placeholder")

if __name__ == '__main__':
    render_weekday_weekend_comparison()