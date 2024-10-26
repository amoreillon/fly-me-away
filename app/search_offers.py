import requests
from datetime import datetime, timedelta, time
import re

# All functions required to identify cheapest offers on a given day and route

# Function to get an access token from the Amadeus API
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


# Function to get offers from the Amadeus API
def get_offers(access_token, origin, destination, departure_date, return_date, non_stop, travel_class, api_url):
    params = {
        'originLocationCode': origin,
        'destinationLocationCode': destination,
        'departureDate': departure_date,
        'returnDate': return_date,
        'adults': 1,
        'max': 50,  
        'nonStop': non_stop,
        'travelClass': travel_class

    }
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(f"{api_url}/v2/shopping/flight-offers", headers=headers, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Error: {response.status_code} - {response.text}")


# Function to parse offers data into a more readable format
def parse_offers(offers_data):
    parsed_offers = []
    
    for offer in offers_data.get('data', []):
        parsed_offer = {
            'price': float(offer['price']['total']),
            'currency': offer['price']['currency'],
            'itineraries': []
        }
        
        for itinerary in offer['itineraries']:
            parsed_itinerary = {
                'segments': [],
                'total_duration': itinerary['duration']
            }
            
            for segment in itinerary['segments']:
                parsed_itinerary['segments'].append({
                    'departure': {
                        'iataCode': segment['departure']['iataCode'],
                        'at': datetime.fromisoformat(segment['departure']['at']),
                    },
                    'arrival': {
                        'iataCode': segment['arrival']['iataCode'],
                        'at': datetime.fromisoformat(segment['arrival']['at']),
                    },
                    'carrierCode': segment['carrierCode'],
                    'number': segment['number'],
                    'duration': segment['duration']
                })
            
            parsed_offer['itineraries'].append(parsed_itinerary)
        
        parsed_offers.append(parsed_offer)
    
    return parsed_offers


# Function to filter offers based on departure and return time options 
def filter_offers_by_time(parsed_offers, departure_time_option, return_time_option):
    if departure_time_option == 0 and return_time_option == 0:  # "Any" for both
        return parsed_offers
    
    filtered_offers = []
    
    def time_match(t, option):
        if option == 0:  # Any
            return True
        elif option == 1:  # Morning (midnight to noon)
            return time(0, 0) <= t < time(12, 0)
        elif option == 2:  # Afternoon and evening (noon to midnight)
            return time(12, 0) <= t <= time(23, 59, 59)
        elif option == 3:  # Evening (6pm to midnight)
            return time(18, 0) <= t <= time(23, 59, 59)
    
    for offer in parsed_offers:
        outbound_departure_time = offer['itineraries'][0]['segments'][0]['departure']['at'].time()
        return_departure_time = offer['itineraries'][1]['segments'][0]['departure']['at'].time()
        
        outbound_match = time_match(outbound_departure_time, departure_time_option)
        return_match = time_match(return_departure_time, return_time_option)
        
        #print(f"Offer price: {offer['price']}")
        #print(f"Outbound departure time: {outbound_departure_time}, Match: {outbound_match}")
        #print(f"Return departure time: {return_departure_time}, Match: {return_match}")
        
        if outbound_match and return_match:
            filtered_offers.append(offer)
        #else:
        #    print("Offer filtered out")
        
        #print("---")
    
    return filtered_offers

def get_cheapest_offer(offers):
    if not offers:
        return None
    return min(offers, key=lambda x: float(x['price']))

def format_flight_details(itinerary, is_outbound):
    journey_type = "Outbound Journey" if is_outbound else "Return Journey"
    first_segment = itinerary['segments'][0]
    last_segment = itinerary['segments'][-1]
    
    journey_date = first_segment['departure']['at'].strftime("%A %d.%m.%Y")
    departure_time = first_segment['departure']['at'].strftime("%H:%M")
    
    details = [f"<strong>{journey_type}</strong>"]
    details.append(f"{journey_date} at {departure_time}")
    
    flight_info = []
    for segment in itinerary['segments']:
        flight_number = f"{segment['carrierCode']} {segment['number']}"
        flight_info.append(f"{flight_number} from {segment['departure']['iataCode']} to {segment['arrival']['iataCode']}")
    
    details.append(" → ".join(flight_info))
    
    # Convert total travel time to a more readable format
    total_duration = itinerary['total_duration']
    hours = re.search(r'(\d+)H', total_duration)
    minutes = re.search(r'(\d+)M', total_duration)
    
    formatted_duration = ""
    if hours:
        formatted_duration += f"{hours.group(1)}H"
    if minutes:
        formatted_duration += f"{minutes.group(1)}M"
    
    details.append(f"Total travel time: {formatted_duration}")
    
    return "<br>".join(details)
