import streamlit as st
from datetime import datetime, timedelta
import toml
import time
import pandas as pd
from flight_search import get_access_token, get_cheapest_flight

# Load API credentials
try:
    # Attempt to load credentials from Streamlit secrets (Streamlit Cloud)
    api_key = st.secrets["api"]["key"]
    api_secret = st.secrets["api"]["secret"]
except AttributeError:
    # Fallback to loading secrets locally from 'secrets.toml'
    secrets = toml.load('config/secrets.toml')
    api_key = secrets['api']['key']
    api_secret = secrets['api']['secret']

# Load search parameters from parameters.toml
params_config = toml.load('config/parameters.toml')
origin_default = params_config['search']['origin']
destination_default = params_config['search']['destination']
departure_day_default = params_config['search']['departure_day'].capitalize()
number_of_nights_default = params_config['search']['number_of_nights']
direct_flight_default = params_config['search']['direct_flight']
travel_class_default = params_config['search']['travel_class'].upper()

# Streamlit UI
st.title("Fly Me Away")

# Set default values in input widgets
origin = st.text_input("Enter the origin airport code (e.g., ZRH)", value=origin_default).upper()
destination = st.text_input("Enter the destination airport code (e.g., LHR)", value=destination_default).upper()
start_date = st.date_input("Enter the start date for the range", datetime.now() + timedelta(days=1))  # Default to tomorrow's date
end_date = st.date_input("Enter the end date for the range", datetime.now() + timedelta(days=90))  # Default to three months from tomorrow
departure_day = st.selectbox("Enter the day of departure", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], index=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"].index(departure_day_default))
number_of_nights = st.number_input("Enter the number of nights to stay", min_value=1, value=number_of_nights_default)
direct_flight = st.checkbox("Direct flight only?", value=direct_flight_default)
travel_class = st.selectbox("Select travel class", ["ECONOMY", "PREMIUM_ECONOMY", "BUSINESS", "FIRST"], index=["ECONOMY", "PREMIUM_ECONOMY", "BUSINESS", "FIRST"].index(travel_class_default))

# Search button to execute flight search
if st.button("Search Flights"):
    try:
        # Get access token
        access_token = get_access_token(api_key, api_secret)
        
        # Map departure day to weekday number
        day_mapping = {
            'Monday': 0,
            'Tuesday': 1,
            'Wednesday': 2,
            'Thursday': 3,
            'Friday': 4,
            'Saturday': 5,
            'Sunday': 6
        }
        departure_day_num = day_mapping[departure_day]

        current_date = start_date
        flight_prices = []  # Collect data for table and plotting

        # Initialize progress bar
        total_days = (end_date - start_date).days + 1  # Including the end date in the count
        progress_bar = st.progress(0)
        progress_counter = 0

        while current_date <= end_date:
            if current_date.weekday() == departure_day_num:
                departure_date_str = current_date.strftime('%Y-%m-%d')
                return_date = current_date + timedelta(days=number_of_nights)
                return_date_str = return_date.strftime('%Y-%m-%d')

                rate_limit_counter = 0
                try:
                    # Fetch cheapest flight
                    flight_data = get_cheapest_flight(
                        access_token, origin, destination,
                        departure_date_str, return_date_str,
                        direct_flight, travel_class
                    )

                    # Store results for table and plotting
                    if flight_data['data']:
                        cheapest_flight = min(flight_data['data'], key=lambda x: float(x['price']['total']))

                        # Extract departure flight details (all segments)
                        departure_segments = cheapest_flight['itineraries'][0]['segments']
                        departure_flights = ", ".join([seg['carrierCode'] + " " + seg['number'] for seg in departure_segments])

                        # Extract return flight details (all segments)
                        return_segments = cheapest_flight['itineraries'][1]['segments']
                        return_flights = ", ".join([seg['carrierCode'] + " " + seg['number'] for seg in return_segments])

                        # Store data for the table with price and currency
                        flight_prices.append({
                            "departure_date": departure_date_str,
                            "departure_flight": departure_flights,
                            "return_date": return_date_str,
                            "return_flight": return_flights,
                            "price": f"{cheapest_flight['price']['total']} {cheapest_flight['price']['currency']}"
                        })

                except Exception as e:
                    if '429' in str(e):
                        rate_limit_counter += 1
                        if rate_limit_counter >= 3:
                            st.warning("Rate limit reached. Waiting for 60 seconds...")
                            time.sleep(60)
                            rate_limit_counter = 0
                    else:
                        st.error(f"An error occurred while fetching flight data: {e}")
                        break

                # Pause to respect rate limit
                time.sleep(0.5)

            # Update progress
            progress_counter += 1
            progress_bar.progress(min(progress_counter / total_days, 1.0))  # Ensure the progress value does not exceed 1.0

            current_date += timedelta(days=1)

        # Plot the data if available
        if flight_prices:
            df = pd.DataFrame(flight_prices)
            df['departure_date'] = pd.to_datetime(df['departure_date']).dt.date
            df['return_date'] = pd.to_datetime(df['return_date']).dt.date

            # Display table of flight data
            st.write("### Flight Price Details")
            st.dataframe(df)

        else:
            st.write("No flight data available for the selected date range.")

    except Exception as e:
        st.error(f"An error occurred: {e}")