import streamlit as st
import pandas as pd

@st.cache_data
def load_airports_data():
    return pd.read_csv('data/airports.csv', usecols=['name', 'city', 'country', 'code'])

def search_airports(query, airports_df):
    """
    Search for airports based on the input query.
    Returns a list of dictionaries containing matching airports.
    """
    query = query.lower()
    mask = (
        airports_df['name'].str.lower().str.contains(query) |
        airports_df['city'].str.lower().str.contains(query) |
        airports_df['country'].str.lower().str.contains(query) |
        airports_df['code'].str.lower().str.contains(query)
    )
    results = airports_df[mask].to_dict('records')
    return results[:10]  # Limit to top 10 results

def format_airport(airport):
    return f"{airport['city']} ({airport['code']}) - {airport['name']}, {airport['country']}"

# Load airport data
airports_df = load_airports_data()

st.title("Airport Search Experiment")

# Custom CSS to make the selectbox look like part of the text input
st.markdown("""
    <style>
    div[data-baseweb="select"] > div {
        border-top: none;
        border-top-left-radius: 0;
        border-top-right-radius: 0;
    }
    div[data-baseweb="select"] {
        margin-top: -1px;
    }
    </style>
    """, unsafe_allow_html=True)

# Create a text input for search
search_query = st.text_input("Search for an airport (by name, city, country, or code)")

# Search for airports based on the query
if search_query:
    airport_options = search_airports(search_query, airports_df)
else:
    airport_options = []

# Use selectbox to display search results
if airport_options:
    selected_airport = st.selectbox(
        "",
        options=airport_options,
        format_func=format_airport,
        key="airport_select"
    )

    # Display selected airport code
    if selected_airport:
        selected_airport_code = selected_airport['code']
        st.text_input("Selected Airport Code", value=selected_airport_code, disabled=True)
else:
    st.info("Enter a search query to find airports.")

# Update search query when an airport is selected
if 'airport_select' in st.session_state and st.session_state.airport_select:
    selected = st.session_state.airport_select
    st.session_state.search_query = format_airport(selected)
