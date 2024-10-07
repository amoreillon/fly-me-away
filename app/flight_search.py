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
    url = f"{api_url}/v2/shopping/flight-offers"
    params = {
        'originLocationCode': origin,
        'destinationLocationCode': destination,
        'departureDate': departure_date,
        'returnDate': return_date,
        'adults': 1,
        'max': 5,
        'nonStop': str(direct_flight).lower(),
        'travelClass': travel_class
    }
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Error: {response.status_code} - {response.text}")