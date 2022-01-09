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
    # Inter-checkpoint pause
    time.sleep(.5)
    res = requests.get(hourly_url, headers=headers)
    forecast = res.json()
    if 'type' in forecast.keys():
        forecast['error'] = False
        return(forecast)
    elif 'title' in forecast.keys():
        forecast['error'] = True
        forecast['error_msg'] = forecast['title']
    else:
        forecast['error'] = True
        forecast['error_message'] = 'Unknown NWS API Error'



def get_nws_hourly_url(lat, lon):
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
            return(forecast_url)
    else:
        headers = {
            'User-Agent': 'adeilertson@gmail.com',
            'From': 'adeilertson@gmail.com'
            }
        url = f"https://api.weather.gov/points/{lat:.3f},{lon:.3f}"
        res = requests.get(url, headers=headers)
        res_data = res.json()
        if 'properties' in res_data.keys():
            forecast_url = res_data['properties']['forecastHourly']
            # Update gridpoint reference
            new_entry = {
                'lat': f"{lat:.3f}",
                'lon': f"{lon:.3f}",
                'hourly_forecast_url': forecast_url
            }
            gridpoints.append(new_entry)
            add_gridpoints(gridpoints)
            return(forecast_url)
        elif 'title' in res_data.keys():
            return(None)
        else:
            return(None)


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
        route_data['error'] = False
        route_data['error_msg'] = ''
    except JSONDecodeError:
        route_data = {
            'error': True,
            'error_msg': 'ORS Routing Error'
        }

    return(route_data)