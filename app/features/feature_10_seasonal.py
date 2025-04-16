import streamlit as st
from app.stremlit_colour_pallet import MAGENTA, LIGHT_GRAY, DARK_GRAY, WHITE

def render_seasonal_trend_analyzer():
    st.title("Monthly/Seasonal Trend Analyzer")
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

    st.subheader("Average Daily Traffic Volume by Month")
    st.write("Chart Placeholder")

    st.subheader("School Holiday vs Term Time Comparison")
    st.write("Chart Placeholder")

if __name__ == '__main__':
    render_seasonal_trend_analyzer()