import os
from dotenv import load_dotenv
import streamlit as st
from datetime import datetime, timedelta
import toml
import time
import hmac
import pandas as pd
import psycopg2

from search_offers import get_access_token, get_offers, parse_offers, filter_offers_by_time, get_cheapest_offer
from lookup_airports import search_airport
from auth import check_password 
from db_operations import insert_data, create_tables

from streamlit_extras.buy_me_a_coffee import button
from streamlit_searchbox import st_searchbox

import sys

# Load environment variables from .env file
load_dotenv()

# Get environment
environment = os.getenv('ENVIRONMENT', 'production')

# Set API endpoint based on the environment
API_URL = "https://test.api.amadeus.com" if environment == "test" else "https://api.amadeus.com"

# Load API credentials
if environment == "test":
    api_key = os.getenv('TEST_API_KEY')
    api_secret = os.getenv('TEST_API_SECRET')
else:
    api_key = os.getenv('PROD_API_KEY')
    api_secret = os.getenv('PROD_API_SECRET')

if not api_key or not api_secret:
    raise ValueError(f"API credentials not found for {environment} environment.")

# Load default search parameters from parameters.toml
params_config = toml.load('config/parameters.toml')
origin_default = params_config['search']['origin']
destination_default = params_config['search']['destination']
departure_day_default = params_config['search']['departure_day'].capitalize()
number_of_nights_default = params_config['search']['number_of_nights']
direct_flight_default = params_config['search']['direct_flight']
travel_class_default = params_config['search']['travel_class'].upper()
departure_time_option_default = params_config['search'].get('departure_time_option', 'Any')
return_time_option_default = params_config['search'].get('return_time_option', 'Any')

# Read the airlines CSV file
airlines_df = pd.read_csv('data/airlines.csv')

# Create a dictionary for quick lookup of both name and URL
airlines_dict = {
    iata: {'name': name, 'url': url} 
    for iata, name, url in zip(airlines_df['IATA'], airlines_df['Name'], airlines_df['url'])
}


#  Styling
st.markdown(
    """
    <style>
    /* Remove top padding and white bar */
    .stApp {
        padding-top: 0;
    }
    header[data-testid="stHeader"] {
        display: none;
    }

    /* Existing styles */
    .stApp {
        background-color: #13133D;
    }
    h1, h2, h3 {
        color: #000080;
    }
    p {
        color: #000080;
    }
    /* Expanders */
    div[data-testid="stExpander"] {
        background-color: white;
        border: none;
        border-radius: 10px;
        margin-bottom: 1rem;
        overflow: hidden;
    }
    .streamlit-expanderHeader {
        background-color: white !important;
        color: #13133D !important;
        border-bottom: none;
        padding: 10px;
        font-weight: bold;
    }
    .streamlit-expanderContent {
        background-color: white !important;
        border-top: none;
        padding: 10px;
    }
    /* Buttons */
    .stButton > button {
        background-color: #FFA500;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px;
        font-weight: bold;
    }
    .stButton > button:hover {
        background-color: #FF8C00;
    }
    /* Custom text for FMA brand */
    .orange-text {
        color: #FFA500;
        font-style: italic;
    }
    /* Specific styles for the login form */
    [data-testid="stForm"] {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
    }
    [data-testid="stForm"] [data-testid="stVerticalBlock"] {
        gap: 20px;
    }
    [data-testid="stForm"] .stTextInput > div > div {
        background-color: white !important;
    }
    [data-testid="stForm"] .stTextInput input {
        background-color: white !important;
        color: #000080 !important;
    }
    /* Title section */
    .logo-title-container {
        display: flex;
        align-items: center;
        gap: 20px;
    }
    .naked-text h1 {
        color: white;
        margin-top: 0;
        margin-bottom: 10px;
    }
    .naked-text p {
        color: white;
        margin-top: 0;
    }
    /* Styles for the output page */
    .output-text {
        color: white;
    }
    /* Style for dataframes */
    .stDataFrame {
        color: white;
    }
    .stDataFrame [data-testid="stTable"] {
        color: white;
    }
    /* Style for charts */
    [data-testid="stScatterChart"] {
        color: white;
    }
    [data-testid="stScatterChart"] text {
        fill: white !important;
    }
    /* Flight option styling */
    .flight-option {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
    }
    .flight-option h3 {
        color: #13133D;
        margin-top: 0;
    }
    .flight-option p {
        margin: 5px 0;
    }
    .book-now-button {
        background-color: #FFA500;
        color: white;
        padding: 10px 20px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        border-radius: 5px;
        margin-top: 10px;
    }
    /* Price styling */
    .price-link {
        font-size: 1.2em;
        font-weight: bold;
        color: #FFA500;  /* Orange color, matching your theme */
        text-decoration: none;
    }
    .price-link:hover {
        text-decoration: underline;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Password check upon loading the page
#if not check_password():
#    st.stop()

# Modify search_airport to use the loaded airport_data
def search_airport_wrapper(query: str):
    return search_airport(query)  

if 'page' not in st.session_state:
    st.session_state['page'] = 'input'

if st.session_state['page'] == 'input':
    # Create a container for the top section
    top_container = st.container()

    # Use columns for layout within the container
    with top_container:
        col1, spacer, col2 = st.columns([1, 0.5, 3])  # Adjust the ratios as needed

        with col1:
            st.image("assets/logo.png", width=200)  # Adjust width as needed

        # The spacer column remains empty, creating horizontal space

        with col2:
            st.markdown(
                """
                <div class="naked-text">
                    <h1>Fly Me Away</h1>
                    <p>
                    Find the cheapest holiday or weekend flights to your favorite destinations over a range of dates. 
                    <span class="orange-text">Fly Me Away</span> looks up the best weekly prices.
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

    # Destination Expander
    with st.expander("**Destination**", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            origin_full = st_searchbox(
            search_airport_wrapper,
            key="origin_search",
            placeholder="Search origin airport...",
            default=origin_default,
            label="Origin"
        )
        if origin_full:
            origin = origin_full.split('(')[1].split(')')[0] if origin_full else ''
            
            
        with col2:
            destination_full = st_searchbox(
                search_airport_wrapper,
                key="destination_search",
                placeholder="Search destination airport...",
                default=destination_default,
                label="Destination"
            )
            if destination_full:
                destination = destination_full.split('(')[1].split(')')[0] if destination_full else ''
        
            
    # Flight Details Expander
    with st.expander("**Departure Day and Duration**", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            departure_day = st.selectbox("Day of Departure", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], index=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"].index(departure_day_default))
            departure_time_option = st.selectbox(
                "Preferred time of departure flight",
                ["Any", "Morning (midnight to noon)", "Afternoon and evening (noon to midnight)", "Evening (6pm to midnight)"],
                index=["Any", "Morning (midnight to noon)", "Afternoon and evening (noon to midnight)", "Evening (6pm to midnight)"].index(departure_time_option_default)
            )

        with col2:
            number_of_nights = st.number_input("Number of Nights", min_value=1, value=number_of_nights_default)
            return_time_option = st.selectbox(
                "Preferred time of the return flight",
                ["Any", "Morning (midnight to noon)", "Afternoon and evening (noon to midnight)", "Evening (6pm to midnight)"],
                index=["Any", "Morning (midnight to noon)", "Afternoon and evening (noon to midnight)", "Evening (6pm to midnight)"].index(return_time_option_default)
            )

    # Range of Travel Dates Expander
    with st.expander("**Possible Travel Period**", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            start_date = st.date_input("Start Date", datetime.now() + timedelta(days=1))  # Default to tomorrow's date
        
        with col2:
            end_date = st.date_input("End Date", datetime.now() + timedelta(days=90))  # Default to three months from tomorrow

    # Preferences Expander
    with st.expander("**Preferences**", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            flight_type = st.selectbox("Flight Type", ["Direct", "Including stopovers"], index=0 if direct_flight_default else 1)
        
        with col2:
            travel_class = st.selectbox("Select travel class", ["ECONOMY", "PREMIUM_ECONOMY", "BUSINESS", "FIRST"], index=["ECONOMY", "PREMIUM_ECONOMY", "BUSINESS", "FIRST"].index(travel_class_default))

    # Results retrieval
    if st.button("Search Flights"):
        try:
            # Ensure tables exist
            create_tables()

            # Store search parameters in session state
            search_inputs = {
                'origin': origin,
                'destination': destination,
                'departure_day': departure_day,
                'number_of_nights': number_of_nights,
                'start_date': str(start_date),
                'end_date': str(end_date),
                'flight_type': flight_type,
                'travel_class': travel_class,
                'departure_time_option': departure_time_option,
                'return_time_option': return_time_option,
                'environment': environment  # Add environment to search inputs
            }
            st.session_state['search_inputs'] = search_inputs

            # Record search inputs
            if search_inputs:
                search_inputs_id = insert_data(search_inputs, 'search_inputs')

            # Get access token
            access_token = get_access_token(api_key, api_secret, API_URL)

            # Convert flight_type to boolean for the API call
            direct_flight = (str(flight_type == "Direct").lower())  

            # Map departure day to weekday number
            day_mapping = {
                'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3,
                'Friday': 4, 'Saturday': 5, 'Sunday': 6
            }
            departure_day_num = day_mapping[departure_day]

            # Map time of departure and return to numbers
            time_mapping = {
                "Any": 0,
                "Morning (midnight to noon)": 1,
                "Afternoon and evening (noon to midnight)": 2,
                "Evening (6pm to midnight)": 3
            }

            # Map departure and return time options to numbers
            departure_time_option_num = time_mapping[departure_time_option]
            return_time_option_num = time_mapping[return_time_option]
        
            current_date = start_date # Initialize current date
            flight_prices = []  # Collect data for table and plotting

            # Initialize progress bar
            total_days = (end_date - start_date).days + 1
            progress_bar = st.progress(0)
            progress_counter = 0


            while current_date <= end_date:
                if current_date.weekday() == departure_day_num:
                    departure_date_str = current_date.strftime('%Y-%m-%d')
                    return_date = current_date + timedelta(days=number_of_nights)
                    return_date_str = return_date.strftime('%Y-%m-%d')

                    try:
                        # Fetch offers
                        offers_data = get_offers(
                            access_token, origin, destination,
                            departure_date_str, return_date_str,
                            direct_flight, travel_class, API_URL
                        )

                        # Parse offers data
                        parsed_offers = parse_offers(offers_data)

                        # Record parsed offers in database
                        if parsed_offers:
                            parsed_offers_id = insert_data(parsed_offers, 'parsed_offers', search_inputs_id)

                        # Filter offers based on preferred departure and return times
                        filtered_offers = filter_offers_by_time(parsed_offers, departure_time_option_num, return_time_option_num)

                        # Get the cheapest offer
                        cheapest_offer = get_cheapest_offer(filtered_offers)

                        if cheapest_offer:
                            # Extract departure flight details
                            departure_segments = cheapest_offer['itineraries'][0]['segments']
                            departure_flights = ", ".join([f"{seg['carrierCode']} {seg['number']}" for seg in departure_segments])
                            departure_time = departure_segments[0]['departure']['at']

                            # Extract return flight details
                            return_segments = cheapest_offer['itineraries'][1]['segments']
                            return_flights = ", ".join([f"{seg['carrierCode']} {seg['number']}" for seg in return_segments])
                            return_time = return_segments[0]['departure']['at']

                            # Store data for the table
                            flight_prices.append({
                                "departure_date": departure_date_str,
                                "departure_time": departure_time.strftime('%H:%M'),
                                "departure_flight": departure_flights,
                                "return_date": return_date_str,
                                "return_time": return_time.strftime('%H:%M'),
                                "return_flight": return_flights,
                                "price": round(cheapest_offer['price'], 2),
                                "currency": cheapest_offer['currency'],
                                "origin": origin,
                                "destination": destination
                            })

                    except Exception as e:
                        if '429' in str(e):
                            st.markdown('<div class="naked-text"><p>Rate limit reached. Waiting for 60 seconds...</p></div>', unsafe_allow_html=True)
                            time.sleep(60)
                        else:
                            st.error(f"An error occurred while fetching flight data: {e}")
                            break

                    # Pause to respect rate limit
                    if environment == "test":
                        time.sleep(0.5)
                    else:
                        time.sleep(0.05)

                # Update progress
                progress_counter += 1
                progress_bar.progress(min(progress_counter / total_days, 1.0))

                current_date += timedelta(days=1)

            # Store flight data in session state for the results page
            if flight_prices:
                st.session_state['flight_prices'] = pd.DataFrame(flight_prices)

                # Record flight prices in database
                if search_inputs_id:
                    flight_prices_id = insert_data(flight_prices, 'flight_prices', search_inputs_id)

                st.session_state['page'] = 'results'
                st.rerun()  # Redirect to results page if available
            else:
                st.markdown('<div class="naked-text"><p>No flight data available for the selected date range.</p></div>', unsafe_allow_html=True)

        except Exception as e:
            st.error(f"An error occurred: {e}")
            print(f"Error details: {e}", file=sys.stderr)

    # Add space before the button
    st.write("")
    col1, col2, col3 = st.columns(3)
    with col3:
        button(username="flymeaway", floating=False, width=221)
    
# Results Page
elif st.session_state['page'] == 'results' and 'flight_prices' in st.session_state:
    st.markdown('<h1 class="output-text">Flight Price Details</h1>', unsafe_allow_html=True)
    
    # Create a fresh copy of the DataFrame
    df = st.session_state['flight_prices'].copy()
    
    # New expander for input parameters
    with st.expander("**Search Parameters**", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            # Assuming search_inputs is stored in st.session_state['search_inputs']
            search_inputs = st.session_state.get('search_inputs', {})

            st.write(f"**Origin:** {search_inputs.get('origin', 'N/A')}")
            st.write(f"**Destination:** {search_inputs.get('destination', 'N/A')}")
            st.write(f"**Departure Day:** {search_inputs.get('departure_day', 'N/A')}")
            st.write(f"**Number of Nights:** {search_inputs.get('number_of_nights', 'N/A')}")
            start_date = search_inputs.get('start_date', 'N/A')
            end_date = search_inputs.get('end_date', 'N/A')
            travel_period = f"{start_date} to {end_date}"
            st.write(f"**Search Period:** {travel_period}")
        with col2:
            st.write(f"**Flight Type:** {search_inputs.get('flight_type', 'N/A')}")
            st.write(f"**Travel Class:** {search_inputs.get('travel_class', 'N/A')}")
            st.write(f"**Departure Time:** {search_inputs.get('departure_time_option', 'N/A')}")
            st.write(f"**Return Time:** {search_inputs.get('return_time_option', 'N/A')}")

    # Combine price and currency into a single column
    df['Price'] = df.apply(lambda row: f"{row['price']:.2f} {row['currency']}", axis=1)
    
    # Reorder columns to have Price first, then remove individual price and currency columns
    columns_order = ['Price', 'departure_date', 'departure_time', 'departure_flight', 'return_date', 'return_time', 'return_flight']
    df = df[columns_order]
    
    # Highlight the best price in the results table
    best_price_index = df['Price'].apply(lambda x: float(x.split()[0])).idxmin()
    df.insert(0, '🔥', ['🔥' if i == best_price_index else '' for i in df.index])

    def highlight_best_price(row):
        return ['background-color: lightgreen' if row.name == best_price_index else '' for _ in row]

    # Price Trend Chart Expander
    with st.expander("**Price Trends**", expanded=True):
        # Create a copy of the DataFrame
        df_chart = df.copy()
        # Extract numeric price for charting
        df_chart.loc[:, 'numeric_price'] = df_chart['Price'].apply(lambda x: float(x.split()[0]))
        df_chart = df_chart.set_index('departure_date')['numeric_price']
        st.scatter_chart(df_chart)
    
    # Detailed Flight Information Expander
    with st.expander("**Summary**", expanded=True):
        styled_df = df.style.apply(highlight_best_price, axis=1)
        st.dataframe(styled_df)

    # Sort the DataFrame by price before displaying
    df['numeric_price'] = df['Price'].apply(lambda x: float(x.split()[0]))  # Create a numeric price column
    df = df.sort_values('numeric_price')  # Sort by the numeric price

    with st.expander("**Flight Options**", expanded=True):
        total_rows = len(df)
        for index, (_, row) in enumerate(df.iterrows(), start=1):
            col1, col2, col3 = st.columns([1, 3, 1])
            
            with col1:
                # Center the logo vertically and horizontally
                airline_code = row['departure_flight'].split()[0]
                logo_url = f"https://airlabs.co/img/airline/m/{airline_code}.png"
                airline_info = airlines_dict.get(airline_code, {'name': 'Unknown Airline', 'url': '#'})
                airline_name = airline_info['name']
                airline_url = airline_info['url']
                st.markdown(f"""
                    <div style="display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100%;">
                        <img src="{logo_url}" style="max-width: 100%; max-height: 50px; margin-bottom: 5px;">
                        <p style="font-size: 0.8em; text-align: center; margin: 0;">
                            <a href="{airline_url}" target="_blank" style="text-decoration: none; color: inherit;">
                                {airline_name}
                            </a>
                        </p>
                    </div>
                """, unsafe_allow_html=True)
            
            with col2:
                # Outbound flight
                departure_date = datetime.strptime(row['departure_date'], '%Y-%m-%d')
                departure_day = departure_date.strftime('%A')
                departure_formatted = departure_date.strftime('%d/%m/%Y')
                st.markdown(f"**Departure:**")
                st.markdown(f"{departure_day} {departure_formatted} at {row['departure_time']} on {row['departure_flight']}")
                
                st.markdown("")  # Add a blank line for spacing
                
                # Return flight
                return_date = datetime.strptime(row['return_date'], '%Y-%m-%d')
                return_day = return_date.strftime('%A')
                return_formatted = return_date.strftime('%d/%m/%Y')
                st.markdown(f"**Return:**")
                st.markdown(f"{return_day} {return_formatted} at {row['return_time']} on {row['return_flight']}")
            
            with col3:
                # Center the price vertically and horizontally
                price_parts = row['Price'].split()
                price_value = price_parts[0].split('.')[0]  # Get the integer part before the decimal point
                currency = price_parts[1] if len(price_parts) > 1 else ''  # Get the currency if it exists
                
                # Use the airline_url we defined earlier
                st.markdown(f"""
                    <div style="display: flex; justify-content: center; align-items: center; height: 100%;">
                        <p style="font-size: 1.2em; font-weight: bold; margin: 0;">
                            <a href="{airline_url}" target="_blank" style="text-decoration: none; color: #FFA500;">
                                {price_value} {currency}
                            </a>
                        </p>
                    </div>
                """, unsafe_allow_html=True)
            
            # Only add separator if it's not the last row
            if index < total_rows:
                st.markdown("---")  # Separator between flight options

    if st.button("Back to Search"):
        st.session_state['page'] = 'input'
        st.rerun()
    col1, col2, col3 = st.columns(3)
    with col3:
        button(username="flymeaway", floating=False, width=221)









