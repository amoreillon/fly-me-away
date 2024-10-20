import requests
import json
import toml
from pprint import pprint
import os
from datetime import datetime, time
import csv
import time

from search_offers import get_access_token, get_offers, parse_offers, filter_offers_by_time

# Load secrets from TOML file in .streamlit folder
secrets_path = os.path.join(os.path.dirname(__file__), '..', '.streamlit', 'secrets.toml')
with open(secrets_path, 'r') as f:
    secrets = toml.load(f)

# Determine if we are running in test or production
environment = secrets.get("environment", "production")  

# Set API endpoint based on the environment
if environment == "test":
    API_URL = "https://test.api.amadeus.com"
    print("Running in test mode")
else:
    API_URL = "https://api.amadeus.com"
    print("Running in production mode")

# Load API credentials
if environment == "test":
    API_KEY = secrets["test_api"]["key"]
    API_SECRET = secrets["test_api"]["secret"]
else:
    API_KEY = secrets["api"]["key"]
    API_SECRET = secrets["api"]["secret"]

# Hardcoded search parameters for API call 
ORIGIN = "ZRH"
DESTINATION = "JFK"
DEPARTURE_DATE = "2024-11-15"
RETURN_DATE = "2024-11-22"
ADULTS = 1
MAX_RESULTS = 30
NON_STOP = "true"
TRAVEL_CLASS = "ECONOMY"

# Hardcoded search parameters for flight filtering 
DEPARTURE_TIME_OPTION = 2
RETURN_TIME_OPTION = 2


def save_offers_to_csv(offers, filename):
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['price', 'currency', 
                          'outbound_departure_iata', 'outbound_departure_date', 'outbound_departure_time',
                          'outbound_arrival_iata', 'outbound_carrier_code', 'outbound_flight_number',
                          'return_departure_iata', 'return_departure_date', 'return_departure_time',
                          'return_arrival_iata', 'return_carrier_code', 'return_flight_number']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for offer in offers:
                outbound = offer['itineraries'][0]['segments'][0]  # First segment of outbound itinerary
                return_flight = offer['itineraries'][-1]['segments'][0]  # First segment of return itinerary
                
                writer.writerow({
                    'price': offer['price'],
                    'currency': offer['currency'],
                    'outbound_departure_iata': outbound['departure']['iataCode'],
                    'outbound_departure_date': outbound['departure']['at'].date().isoformat(),
                    'outbound_departure_time': outbound['departure']['at'].time().isoformat(),
                    'outbound_arrival_iata': outbound['arrival']['iataCode'],
                    'outbound_carrier_code': outbound['carrierCode'],
                    'outbound_flight_number': outbound['number'],
                    'return_departure_iata': return_flight['departure']['iataCode'],
                    'return_departure_date': return_flight['departure']['at'].date().isoformat(),
                    'return_departure_time': return_flight['departure']['at'].time().isoformat(),
                    'return_arrival_iata': return_flight['arrival']['iataCode'],
                    'return_carrier_code': return_flight['carrierCode'],
                    'return_flight_number': return_flight['number']
                })
        #print(f"Successfully saved {len(offers)} offers to {filename}")
        #print(f"File path: {os.path.abspath(filename)}")
    except Exception as e:
        print(f"An error occurred while saving to CSV: {e}")
        print(f"Current working directory: {os.getcwd()}")
        if offers:
            print(f"First offer structure: {offers[0]}")
        else:
            print("The offers list is empty.")


def get_cheapest_offer(offers):
    if not offers:
        return None
    return min(offers, key=lambda x: float(x['price']))

def main():
    start_time = time.time()
    try:
        print(f"Script started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")

        t1 = time.time()
        access_token = get_access_token(API_KEY, API_SECRET, API_URL)
        print(f"Access token obtained successfully. Time taken: {time.time() - t1:.2f} seconds")

        t2 = time.time()
        offers_data = get_offers(access_token, ORIGIN, DESTINATION, DEPARTURE_DATE, RETURN_DATE, NON_STOP, TRAVEL_CLASS, API_URL)
        print(f"\nNumber of offers returned by the API: {len(offers_data.get('data', []))}")
        print(f"Time taken to get offers: {time.time() - t2:.2f} seconds")

        t3 = time.time()
        parsed_offers = parse_offers(offers_data)
        print(f"\nNumber of offers in parsed_offers: {len(parsed_offers)}")
        print(f"Time taken to parse offers: {time.time() - t3:.2f} seconds")

        t4 = time.time()
        save_offers_to_csv(parsed_offers, 'parsed_offers.csv')
        print(f"Time taken to save parsed offers to CSV: {time.time() - t4:.2f} seconds")

        t5 = time.time()
        filtered_offers = filter_offers_by_time(parsed_offers, DEPARTURE_TIME_OPTION, RETURN_TIME_OPTION)
        print(f"Number of offers in filtered_offers: {len(filtered_offers)}")
        print(f"Time taken to filter offers: {time.time() - t5:.2f} seconds")

        t6 = time.time()
        cheapest_offer = get_cheapest_offer(filtered_offers)
        print(f"Cheapest offer found: {cheapest_offer['price']} {cheapest_offer['currency']}")
        print(f"Time taken to find cheapest offer: {time.time() - t6:.2f} seconds")

        t7 = time.time()
        save_offers_to_csv([cheapest_offer], 'cheapest_offer.csv')
        print(f"Time taken to save cheapest offer to CSV: {time.time() - t7:.2f} seconds")

    except Exception as e:
        print(f"An error occurred in main: {e}")

    finally:
        end_time = time.time()
        print(f"\nScript ended at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total execution time: {end_time - start_time:.2f} seconds")

if __name__ == "__main__":
    main()
