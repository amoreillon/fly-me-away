import streamlit as st
import hmac

def set_page_style():
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #40E0D0;
        }
        div[data-testid="stExpander"] {
            background-color: white;
            border: 1px solid #000080;
            border-radius: 4px;
            margin-bottom: 1rem;
        }
        .streamlit-expanderHeader {
            background-color: white !important;
            color: #000080 !important;
            border-bottom: 1px solid #000080;
            border-radius: 4px 4px 0 0;
            padding: 10px;
            font-weight: bold;
        }
        .streamlit-expanderContent {
            background-color: white !important;
            border-top: none;
            border-radius: 0 0 4px 4px;
            padding: 10px;
        }
        .stButton > button {
            background-color: #FFA500;
            color: white;
            border: 2px solid #000080;
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
            color: white;
        }
        p {
            color: #000080;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def render_input_page(origin_default, destination_default, departure_day_default, number_of_nights_default, 
                      direct_flight_default, travel_class_default, departure_time_option_default, 
                      return_time_option_default):
    st.title("Fly Me Away")

    st.markdown(
        """
        <p style='color: white;'>
        Find the cheapest holiday or weekend flights to your favorite destinations over a range of dates. 
        <span style='color: #FFA500; font-style: italic;'>Fly Me Away</span> looks up the best weekly prices.
        </p>
        """,
        unsafe_allow_html=True
    )

    # Flight Details Expander
    with st.expander("**Flight Details**", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            origin = st.text_input("Origin Airport Code (e.g., ZRH)", value=origin_default).upper()
            departure_day = st.selectbox("Day of Departure", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], index=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"].index(departure_day_default))
            departure_time_option = st.selectbox(
                "Select preferred departure time for outbound flight",
                ["Any", "Morning (midnight to noon)", "Afternoon and evening (noon to midnight)", "Evening (6pm to midnight)"],
                index=["Any", "Morning (midnight to noon)", "Afternoon and evening (noon to midnight)", "Evening (6pm to midnight)"].index(departure_time_option_default)
            )

        with col2:
            destination = st.text_input("Destination Airport Code (e.g., LHR)", value=destination_default).upper()
            number_of_nights = st.number_input("Nights to Stay", min_value=1, value=number_of_nights_default)
            return_time_option = st.selectbox(
                "Select preferred departure time for return flight",
                ["Any", "Morning (midnight to noon)", "Afternoon and evening (noon to midnight)", "Evening (6pm to midnight)"],
                index=["Any", "Morning (midnight to noon)", "Afternoon and evening (noon to midnight)", "Evening (6pm to midnight)"].index(return_time_option_default)
            )

    # Range of Travel Dates Expander
    with st.expander("**Range of Travel Dates**", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            start_date = st.date_input("Start Date", datetime.now() + timedelta(days=1))
        
        with col2:
            end_date = st.date_input("End Date", datetime.now() + timedelta(days=90))

    # Preferences Expander
    with st.expander("**Preferences**", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            flight_type = st.selectbox("Flight Type", ["Direct only", "Including stopovers"], index=0 if direct_flight_default else 1)
        
        with col2:
            travel_class = st.selectbox("Select travel class", ["ECONOMY", "PREMIUM_ECONOMY", "BUSINESS", "FIRST"], index=["ECONOMY", "PREMIUM_ECONOMY", "BUSINESS", "FIRST"].index(travel_class_default))

    return origin, destination, departure_day, number_of_nights, departure_time_option, return_time_option, start_date, end_date, flight_type, travel_class

def render_results_page(df):
    st.title("Flight Price Details")
    
    # Highlight the best price in the results table
    best_price_index = df['price'].idxmin()
    if '🔥' not in df.columns:
        df.insert(0, '🔥', ['🔥' if i == best_price_index else '' for i in df.index])

    def highlight_best_price(row):
        return ['background-color: lightgreen' if row.name == best_price_index else '' for _ in row]

    # Tabs for different views
    tab1, tab2 = st.tabs(["Table", "Chart"])

    with tab1:
        st.write("### Detailed Flight Information")
        styled_df = df.style.format({"price": "{:.2f}"}).apply(highlight_best_price, axis=1)
        st.dataframe(styled_df)

    with tab2:
        st.write("### Price Trend Chart")
        df_chart = df.set_index('departure_date')['price']
        st.scatter_chart(df_chart)

    if st.button("Back to Search"):
        st.session_state['page'] = 'input'
        st.rerun()
