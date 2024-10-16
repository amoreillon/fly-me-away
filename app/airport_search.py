import pandas as pd

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

def get_airport_code(airport_dict):
    """
    Extract the airport code from the airport dictionary.
    """
    return airport_dict['code'] if airport_dict else None
