import streamlit as st
from datetime import datetime, timedelta
import toml
import time
import hmac
import pandas as pd
from flight_search import get_access_token, get_cheapest_flight, filter_flights_by_time
from auth import check_password 


# Determine if we are running in test or production
environment = st.secrets.get("environment", "production")  # Defaults to production if not set

# Set API endpoint based on the environment
if environment == "test":
    API_URL = "https://test.api.amadeus.com"
    print("Running in test mode")
else:
    API_URL = "https://api.amadeus.com"
    print("Running in production mode")

# Load API credentials
if "api" in st.secrets:
    # Load credentials from Streamlit secrets (Streamlit Cloud)
    if environment == "test":
        api_key = st.secrets["test_api"]["key"]
        api_secret = st.secrets["test_api"]["secret"]
    else:
        api_key = st.secrets["api"]["key"]
        api_secret = st.secrets["api"]["secret"]
else:
    raise FileNotFoundError("Secrets file not found and no Streamlit secrets available.")

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

# Apply custom styling
st.markdown(
    """
    <style>
    .stApp {
        background-color: #13133D;
    }
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
    .stTextInput > div > div {
        border-radius: 8px;
    }
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
    .stSelectbox > div > div, .stTextInput > div > div {
        background-color: white;
    }
    h1, h2, h3 {
        color: #000080;  # Changed from white to #000080
    }
    p {
        color: #000080;
    }
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
    .logo-title-container {
        display: flex;
        align-items: center;
        gap: 20px;
    }
    .title-text h1 {
        color: white;
        margin-top: 0;
        margin-bottom: 10px;
    }
    .title-text p {
        color: white;
        margin-top: 0;
    }
    /* Styles for the output page */
    .output-text {
        color: white;
    }
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
    /* Style for tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #1E1E5A;
        border-radius: 4px;
        color: white;
        font-size: 14px;
        font-weight: 400;
        align-items: center;
        justify-content: center;
        margin-top: 2px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FFA500;
    }
    /* New styles for white containers */
    .white-container {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .white-container h3 {
        color: #000080;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Password check upon loading the page
if not check_password():
    st.stop()


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
                <div class="title-text">
                    <h1>Fly Me Away</h1>
                    <p>
                    Find the cheapest holiday or weekend flights to your favorite destinations over a range of dates. 
                    <span class="orange-text">Fly Me Away</span> looks up the best weekly prices.
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

    # Flight Details Expander
    with st.expander("**Desired Flight**", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            origin = st.text_input("Origin Airport Code (e.g., ZRH)", value=origin_default).upper()
            departure_day = st.selectbox("Day of Departure", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], index=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"].index(departure_day_default))
            departure_time_option = st.selectbox(
                "Preferred time of departure flight",
                ["Any", "Morning (midnight to noon)", "Afternoon and evening (noon to midnight)", "Evening (6pm to midnight)"],
                index=["Any", "Morning (midnight to noon)", "Afternoon and evening (noon to midnight)", "Evening (6pm to midnight)"].index(departure_time_option_default)
            )

        with col2:
            destination = st.text_input("Destination Airport Code (e.g., LHR)", value=destination_default).upper()
            number_of_nights = st.number_input("Number of Nights", min_value=1, value=number_of_nights_default)
            return_time_option = st.selectbox(
                "Preferred time of the return flight",
                ["Any", "Morning (midnight to noon)", "Afternoon and evening (noon to midnight)", "Evening (6pm to midnight)"],
                index=["Any", "Morning (midnight to noon)", "Afternoon and evening (noon to midnight)", "Evening (6pm to midnight)"].index(return_time_option_default)
            )

    # Range of Travel Dates Expander
    with st.expander("**Possible Travel Time**", expanded=True):
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

    # Main search button
    if st.button("Search Flights"):
        try:
            # Get access token
            access_token = get_access_token(api_key, api_secret, API_URL)

            # Convert flight_type to boolean for the API call
            direct_flight = (flight_type == "Direct only")

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
                            direct_flight, travel_class, API_URL
                        )

                        # Filter flights based on preferred departure and return times
                        if flight_data['data']:
                            filtered_flights = filter_flights_by_time(flight_data['data'], departure_time_option, return_time_option)
                            
                            # Continue with the cheapest flight among filtered flights
                            if filtered_flights:
                                cheapest_flight = min(filtered_flights, key=lambda x: float(x['price']['total']))

                                # Extract departure flight details (all segments)
                                departure_segments = cheapest_flight['itineraries'][0]['segments']
                                departure_flights = ", ".join([seg['carrierCode'] + " " + seg['number'] for seg in departure_segments])
                                departure_time = departure_segments[0]['departure']['at']

                                # Extract return flight details (all segments)
                                return_segments = cheapest_flight['itineraries'][1]['segments']
                                return_flights = ", ".join([seg['carrierCode'] + " " + seg['number'] for seg in return_segments])
                                return_time = return_segments[0]['departure']['at']

                                # Store data for the table with price and currency
                                flight_prices.append({
                                    "departure_date": departure_date_str,
                                    "departure_time": departure_time.split('T')[1][:5],
                                    "departure_flight": departure_flights,
                                    "return_date": return_date_str,
                                    "return_time": return_time.split('T')[1][:5],
                                    "return_flight": return_flights,
                                    "price": round(float(cheapest_flight['price']['total']), 2),
                                    "currency": cheapest_flight['price']['currency']
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

            # Store flight data in session state for the results page
            if flight_prices:
                st.session_state['flight_prices'] = pd.DataFrame(flight_prices)
                st.session_state['page'] = 'results'
                st.rerun()  # Redirect to results page if available
            else:
                st.write("No flight data available for the selected date range.")

        except Exception as e:
            st.error(f"An error occurred: {e}")

# Results Page
elif st.session_state['page'] == 'results' and 'flight_prices' in st.session_state:
    st.markdown('<h1 class="output-text">Flight Price Details</h1>', unsafe_allow_html=True)
    
    df = st.session_state['flight_prices']
    
    # Highlight the best price in the results table
    best_price_index = df['price'].idxmin()
    if '🔥' not in df.columns:
        df.insert(0, '🔥', ['🔥' if i == best_price_index else '' for i in df.index])

    def highlight_best_price(row):
        return ['background-color: lightgreen' if row.name == best_price_index else '' for _ in row]

    # Detailed Flight Information Expander
    with st.expander("**Detailed Flight Information**", expanded=True):
        styled_df = df.style.format({"price": "{:.2f}"}).apply(highlight_best_price, axis=1)
        st.dataframe(styled_df)

    # Price Trend Chart Expander
    with st.expander("**Price Trend Chart**", expanded=True):
        df_chart = df.set_index('departure_date')['price']
        st.scatter_chart(df_chart)

    if st.button("Back to Search"):
        st.session_state['page'] = 'input'
        st.rerun()