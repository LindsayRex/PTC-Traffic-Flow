import streamlit as st
from app.stremlit_colour_pallet import MAGENTA, LIGHT_GRAY, DARK_GRAY, WHITE

def render_data_quality_overview():
    st.title("Data Quality & Coverage Overview")
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

    st.subheader("Station Data Quality and Type Overview")
    st.write("Map Placeholder")

    st.subheader("Data Coverage Summary by LGA")
    st.write("Table Placeholder")

if __name__ == '__main__':
    render_data_quality_overview()