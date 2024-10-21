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
from db_operations import insert_search_data, create_tables, get_db_connection

from streamlit_extras.buy_me_a_coffee import button
from streamlit_searchbox import st_searchbox


# Determine if we are running in test or production
environment = st.secrets.get("environment", "production")  # Defaults to production if not set

# Set API endpoint based on the environment
if environment == "test":
    API_URL = "https://test.api.amadeus.com"
else:
    API_URL = "https://api.amadeus.com"

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


#  Styling
st.markdown(
    """
    <style>
    /* Overall Style */
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
            # Create tables if they don't exist
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

            departure_time_option_num = time_mapping[departure_time_option]
            return_time_option_num = time_mapping[return_time_option]

            current_date = start_date
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
                                "currency": cheapest_offer['currency']
                            })

                    except Exception as e:
                        if '429' in str(e):
                            st.warning("Rate limit reached. Waiting for 60 seconds...")
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

                print("Search Inputs:", search_inputs)
                print("Flight Prices:", flight_prices)
                print("All Parsed Offers:", parsed_offers)

                # Insert data into the database
                #search_id = insert_search_data(search_inputs, flight_prices, parsed_offers)
                #st.session_state['search_id'] = search_id

                st.session_state['page'] = 'results'
                st.rerun()  # Redirect to results page if available
            else:
                st.markdown('<p style="color: white;">No flight data available for the selected date range.</p>', unsafe_allow_html=True)

        except Exception as e:
            st.error(f"An error occurred: {e}")

    # Add space before the button
    st.write("")
    col1, col2, col3 = st.columns(3)
    with col3:
        button(username="flymeaway", floating=False, width=221)
    
# Results Page
elif st.session_state['page'] == 'results' and 'flight_prices' in st.session_state:
    st.markdown('<h1 class="output-text">Flight Price Details</h1>', unsafe_allow_html=True)
    
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

    df = st.session_state['flight_prices']
    
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

    # Detailed Flight Information Expander
    with st.expander("**Detailed Flight Information**", expanded=True):
        styled_df = df.style.apply(highlight_best_price, axis=1)
        st.dataframe(styled_df)

    # Price Trend Chart Expander
    with st.expander("**Price Trend Chart**", expanded=True):
        # Extract numeric price for charting
        df['numeric_price'] = df['Price'].apply(lambda x: float(x.split()[0]))
        df_chart = df.set_index('departure_date')['numeric_price']
        st.scatter_chart(df_chart)

    if st.button("Back to Search"):
        st.session_state['page'] = 'input'
        st.rerun()
    col1, col2, col3 = st.columns(3)
    with col3:
        button(username="flymeaway", floating=False, width=221)


