import requests
from datetime import datetime, timedelta

def filter_flights_by_time(flights, departure_time_option, return_time_option, direct_flight=False):
    """Filters flight segments based on the selected departure and return time options and direct flight preference."""
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