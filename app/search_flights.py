import requests
from datetime import datetime, timedelta

def get_access_token(api_key, api_secret, api_url):
    url = f"{api_url}/v1/security/oauth2/token"
    payload = {
        'grant_type': 'client_credentials',
        'client_id': api_key,
        'client_secret': api_secret
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    response = requests.post(url, data=payload, headers=headers)

    if response.status_code == 200:
        return response.json()['access_token']
    else:
        raise Exception(f"Error: {response.status_code} - {response.text}")

def get_cheapest_flight(access_token, origin, destination, departure_date, return_date, direct_flight, travel_class, api_url):
    params = {
        'originLocationCode': origin,
        'destinationLocationCode': destination,
        'departureDate': departure_date,
        'returnDate': return_date,
        'adults': 1,
        'max': 50,  
        'nonStop': str(direct_flight).lower(),
        'travelClass': travel_class
    }
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(f"{api_url}/v2/shopping/flight-offers", headers=headers, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Error: {response.status_code} - {response.text}")

def filter_flights_by_time(flights, departure_time_option, return_time_option, direct_flight=False):
    #Filters flight segments based on the selected departure and return time options and direct flight preference.
    filtered_flights = []
    for flight in flights:
        # Check if the flight is direct when direct_flight is True
        if direct_flight:
            outbound_segments = flight['itineraries'][0]['segments']
            return_segments = flight['itineraries'][1]['segments']
            if len(outbound_segments) > 1 or len(return_segments) > 1:
                continue  # Skip this flight if it's not direct

        departure_time = flight['itineraries'][0]['segments'][0]['departure']['at'].split('T')[1]
        return_time = flight['itineraries'][1]['segments'][0]['departure']['at'].split('T')[1]

        dep_hour = int(departure_time.split(':')[0])
        ret_hour = int(return_time.split(':')[0])

        # Filter based on both departure and return time options
        if (
            (departure_time_option == "Morning (midnight to noon)" and 0 <= dep_hour < 12 or
             departure_time_option == "Afternoon and evening (noon to midnight)" and 12 <= dep_hour < 24 or
             departure_time_option == "Evening (6pm to midnight)" and 18 <= dep_hour < 24 or
             departure_time_option == "Any")
        ) and (
            (return_time_option == "Morning (midnight to noon)" and 0 <= ret_hour < 12 or
             return_time_option == "Afternoon and evening (noon to midnight)" and 12 <= ret_hour < 24 or
             return_time_option == "Evening (6pm to midnight)" and 18 <= ret_hour < 24 or
             return_time_option == "Any")
        ):
            filtered_flights.append(flight)

    return filtered_flights