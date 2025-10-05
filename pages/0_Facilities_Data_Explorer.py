import streamlit as st
from src.facilities_helper_map import render_yemen_facility_map

# ---------------------------------------------------------------
# Streamlit setup
# ---------------------------------------------------------------
st.set_page_config(page_title="Yemen Facility Map", layout="wide")
st.title("Facilities Data Explorer")

# ---------------------------------------------------------------
# Main Map Rendering
# ---------------------------------------------------------------
A,B = st.columns([1,2])

with B.container(border =True):
    st.header("Yemen Facility Map")
    render_yemen_facility_map()
