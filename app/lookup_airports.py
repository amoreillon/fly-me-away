import pandas as pd
import streamlit as st

# Load the airport data from CSV
@st.cache_data
def load_airport_data():
    return pd.read_csv('data/airports.csv')

# Modify the search_airport function to use the CSV data
def search_airport(search_term):
    airports_df = load_airport_data()
    filtered_airports = airports_df[
        airports_df['code'].str.contains(search_term.upper()) |
        airports_df['name'].str.contains(search_term, case=False) |
        airports_df['city'].str.contains(search_term, case=False) |
        airports_df['country'].str.contains(search_term, case=False)
    ]
    return [f"{row['name']} ({row['code']}), {row['city']}, {row['country']}" for _, row in filtered_airports.iterrows()]

# Function to get simplified airport name from code
def get_airport_simple_name(code):
    airports_df = load_airport_data()
    matching_airports = airports_df[airports_df['code'] == code]
    if matching_airports.empty:
        return f"Unknown ({code})"
    airport = matching_airports.iloc[0]
    return f"{airport['city']} ({airport['code']})"