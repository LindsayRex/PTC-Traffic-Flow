import streamlit as st
from app.stremlit_colour_pallet import MAGENTA, LIGHT_GRAY, DARK_GRAY, WHITE

def render_corridor_comparison():
    st.title("Corridor Traffic Flow Comparison")
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

    st.subheader("Stations along [Road Name]")
    st.write("Map Placeholder")

    st.subheader("Comparative Hourly Profiles")
    st.write("Chart Placeholder")

    st.subheader("Average Daily Volumes")
    st.write("Table Placeholder")

if __name__ == '__main__':
    render_corridor_comparison()