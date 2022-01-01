"""
Route Weather API Call Functions

Author: Andrew Eilertson
Created: May 21st 2021
URL: https://github.com/adeilertson/route_weather
"""
import time
import requests
from json.decoder import JSONDecodeError
from data_loaders import add_gridpoints, load_gridpoints
from config import api_key

def get_nws_forecast(hourly_url):
    """
    Runs NWS API call to get hourly weather forecast for provided URL

    Args:
        hourly_url (str): NWS hourly forecast URL

    Returns:
        dict: Hourly forecast data converted from json
    """
    headers = {
        'User-Agent': 'adeilertson@gmail.com',
        'From': 'adeilertson@gmail.com'
        }
    attempts = 0
    # Inter-checkpoint pause
    time.sleep(.5)
    collecting = True
    while collecting is True:
        res = requests.get(hourly_url, headers=headers)
        if res.json()['type'] != 'Feature':
            if attempts > 2:
                try:
                    error = {res.json()['title']}
                except IndexError:
                    error = "Unexpected Error (No NWS response title)"
                print(f"Unable to get forcast - {error} {hourly_url}")
                collecting = False
                return(None)
            else:
                time.sleep(10)
                attempts += 1
        else:
            forecast = res.json()
            collecting = False
            return(forecast)


def get_nws_hourly_url(lat, lon, printing=False):
    """
    Gets NWS API hourly forecast URL from provided coordinates

    Args:
        lat (float): Latatude as float
        lon (float): Longitude as float

    Returns:
        str: NWS API hourly URL
    """
    # Check if coords have known gridpoint
    gridpoints = load_gridpoints()

    for point in gridpoints:
        if point['lat'] == f"{lat:.3f}" and point['lon'] == f"{lon:.3f}":
            forecast_url = point['hourly_forecast_url']
            if printing is True:
                print(f"Known Entry - Coords: {lat:.3f},{lon:.3f} - URL: {forecast_url}")
            return(forecast_url)
    else:
        headers = {
            'User-Agent': 'adeilertson@gmail.com',
            'From': 'adeilertson@gmail.com'
            }
        url = f"https://api.weather.gov/points/{lat:.3f},{lon:.3f}"
        res = requests.get(url, headers=headers)
        res_data = res.json()
        forecast_url = res_data['properties']['forecastHourly']
        if printing is True:
            print(f"New Entry - Coords: {lat:.3f},{lon:.3f} - URL: {forecast_url}")

        # Update gridpoint reference
        new_entry = {
            'lat': f"{lat:.3f}",
            'lon': f"{lon:.3f}",
            'hourly_forecast_url': forecast_url
        }
        gridpoints.append(new_entry)
        add_gridpoints(gridpoints)

        return(forecast_url)


def get_ors_route(depart_coords, destination_coords):
    """Runs Open Route Service API call to get route information between two sets of coordinates

    Args:
        depart_coords (list):
        destination_coords (list):

    Returns:
        route_data: Dict from json with route data from api call
    """
    # Sample generated code from Open Route Service
    # Body of request
    # coordinates is list of lon/lat formatted coords in separate lists
    body = {
        "coordinates": [depart_coords,destination_coords],
        "radiuses": [-1,-1]
    }
    # Headers
    # authorization is personal API key
    headers = {
        'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
        'Authorization': api_key,
        'Content-Type': 'application/json; charset=utf-8'
    }

    # Call
    # Returns geojson object
    call = requests.post('https://api.openrouteservice.org/v2/directions/driving-car/geojson', json=body, headers=headers)
    try:
        route_data = call.json()
    except JSONDecodeError:
        route_data = call.content
        print(f"Error getting route for {depart_coords} - {destination_coords}")

    return route_data