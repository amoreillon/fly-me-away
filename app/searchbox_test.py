import streamlit as st
from streamlit_searchbox import st_searchbox

# Import your airport data loading and search functions
from lookup_airports import search_airport#, get_airport_simple_name#, load_airport_data

st.set_page_config(page_title="Search Box Test", layout="wide")

#@st.cache_data
#def cached_load_airport_data():
#    return load_airport_data()

# Load airport data once
#airport_data = cached_load_airport_data()

# Modify search_airport to use the loaded airport_data
def search_airport_wrapper(query: str):
    return search_airport(query)  

st.title("Airport Search Box Test")

col1, col2 = st.columns(2)

with col1:
    origin_full = st_searchbox(
        search_airport_wrapper,
        key="origin_search",
        placeholder="Search origin airport...",
        default='Zürich Airport (ZRH), Zurich, Switzerland',
        label="Origin"
    )
    if origin_full:
        st.write(f"Selected: {origin_full}")
        origin = origin_full.split('(')[1].split(')')[0] if origin_full else ''
        st.write(f"IATA code: {origin}")

with col2:
    destination_full = st_searchbox(
        search_airport_wrapper,
        key="destination_search",
        placeholder="Search destination airport...",
        default='Francisco de Sá Carneiro Airport (OPO), Porto, Portugal',
        label="Destination"
    )
    if destination_full:
        st.write(f"Selected: {destination_full}")
        destination = destination_full.split('(')[1].split(')')[0] if destination_full else ''
        st.write(f"IATA code: {destination}")

st.write("Search box state:")
st.write(st.session_state)
