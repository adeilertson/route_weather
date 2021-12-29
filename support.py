
"""
Route Weather Support Functions

Author: Andrew Eilertson
Created: May 21st 2021
URL: https://github.com/adeilertson/route_weather
"""

from json.decoder import JSONDecodeError
import requests
import time
import pickle
import folium
from folium.map import Popup

from config import api_key

def add_gridpoints(data):
    with open(f'weather_data/gridpoint_coords.pkl', 'wb') as file:
        pickle.dump(data, file)


def coords_to_city(latitude, longitude, zip_locs):
    coord_lat = round(latitude, 1)
    coord_lon = round(longitude, 1)
    nearest_diff = 5

    for loc in zip_locs:
        if round(loc['latitude'], 1) == coord_lat and round(loc['longitude'], 1) == coord_lon:
            city = loc['city']
            break
    else:
        for loc in zip_locs:
            # Find distance between checkpoint coords and city coords
            la_diff = abs(round(loc['latitude'], 1) - coord_lat)
            lo_diff = abs(round(loc['longitude'], 1) - coord_lon)
            coord_diff = la_diff + lo_diff
            # Check if city is closer than current nearest city
            if nearest_diff > coord_diff:
                city = loc['city']
                nearest_diff = coord_diff

    return(city)


def coords_to_state(latitude, longitude, zip_locs):
    coord_lat = round(latitude, 1)
    coord_lon = round(longitude, 1)

    for loc in zip_locs:
        if round(loc['latitude'], 1) == coord_lat and round(loc['longitude'], 1) == coord_lon:
            state = loc['state']
            break
    else:
        state = ''

    return(state)


def coords_to_zip(latitude, longitude, zip_locs):
    coord_lat = round(latitude, 1)
    coord_lon = round(longitude, 1)

    for loc in zip_locs:
        if round(loc['latitude'], 1) == coord_lat and round(loc['longitude'], 1) == coord_lon:
            zip_code = loc['zip']
            break
    else:
        zip_code = ''

    return(zip_code)


def find_checkpoints(route_data, interval=3600, midpoint=False):
    """
    Finds checkpoints at specified duration from Open Route Service route data

    Args:
        route_data (dict): Open Route Service route data object
        interval (int): Interval between checkpoints in seconds. Default is 3600 (1 hour)

    Returns:
        list: List of dicts with checkpoint data
    """
    # Distance and duration
    route_duration = route_data['features'][0]['properties']['summary']['duration']
    route_distance = route_data['features'][0]['properties']['summary']['distance']

    if midpoint is True:
        checkpoint_count = 2
    else:
        # Set number of checkpoints as number of hours in route duration
        # int does not round up - consider other option
        checkpoint_count = int(route_duration/interval)

        # Set distance between checkpoints
        checkpoint_distance = route_distance/checkpoint_count

    # Set list of route point coordinates
    route_points = route_data['features'][0]['geometry']['coordinates']

    # Get difference between depart and destination lon and lat coords
    route_lon_diff = abs(route_points[0][0] - route_points[-1][0])
    route_lat_diff = abs(route_points[0][1] - route_points[-1][1])

    # Set route coordinate distance from route lon and lat distances
    route_coord_distance = route_lon_diff + route_lat_diff

    # Set coordinate distance between checkpoints
    coord_check_point_distance = abs(route_coord_distance / checkpoint_count)

    # New list for checkpoint data
    checkpoints = []

    # Build first checkpoint
    if midpoint is False:
        new_checkpoint = {
            'lat': route_points[0][1],
            'lon': route_points[0][0],
        }
        checkpoints.append(new_checkpoint)

    # Set locations of checkpoints
    current_coord_distance = 0
    current_coord_target = abs(coord_check_point_distance)

    prev_coord = route_points[0]

    for coord in route_points[1:]:
        # Determine distance traveled from previous point
        lon_diff = abs(coord[0] - prev_coord[0])
        lat_diff = abs(coord[1] - prev_coord[1])
        coord_distance = lon_diff + lat_diff

        # Increase current distance with additional point distance
        current_coord_distance += coord_distance

        # Check if at current target distance
        if current_coord_distance >= current_coord_target:
            # Add current coordinate to list of checkpoint
            new_checkpoint = {
                'lat': coord[1],
                'lon': coord[0],
                }
            checkpoints.append(new_checkpoint)
            if midpoint is True:
                return(checkpoints)
            # Increase target distance
            current_coord_target += coord_check_point_distance

        # Set current coord to previous coord for next point check
        prev_coord = coord

    # Ensure last checkpoint is last point
    new_checkpoint = {
        'lat': route_points[-1][1],
        'lon': route_points[-1][0],
    }
    checkpoints[-1] = new_checkpoint

    return(checkpoints)


def get_forecast(hourly_url):
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
                print(f"Unable to get forcast - {hourly_url}")
                collecting = False
            else:
                time.sleep(10)
                attempts += 1
        else:
            forecast = res.json()
            collecting = False
            return(forecast)


def get_hourly_url(lat, lon, printing=False):
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


def get_route(depart_coords, destination_coords):
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
        print(f"Error getting route. Call returned {call.content}")

    return route_data


def get_zip_data():
    zip_codes = load_zip_codes()
    zip_locs = load_zip_locs()

    return(zip_codes, zip_locs)


def load_gridpoints():
    with open(f'weather_data/gridpoint_coords.pkl', 'rb') as file:
        data = pickle.load(file)
    return data


def load_zip_codes():
    with open(f'weather_data/zip_codes.pkl', 'rb') as file:
        data = pickle.load(file)
    return data


def load_zip_locs():
    with open(f'weather_data/zip_locs.pkl', 'rb') as file:
        data = pickle.load(file)
    return data


def popup_builder(checkpoint, loc_report, icon):
    popup = folium.Marker(
    location=[checkpoint['lat'], checkpoint['lon']],
    popup=Popup(loc_report, min_width=100, max_width=300),
    icon=icon)
    return(popup)


def reset_gridpoints():
    blank_set = []
    add_gridpoints(blank_set)


def set_hourly_forecast(city, hourly_data, hour):
    # Set time
    city_time = hourly_data['properties']['periods'][hour]['startTime'][11:16]
    # Set forecast, temp, and wind for specified hour index
    forecast = hourly_data['properties']['periods'][hour]['shortForecast']
    temp = hourly_data['properties']['periods'][hour]['temperature']
    wind = hourly_data['properties']['periods'][hour]['windSpeed']

    if int(city_time[0:2]) > 12:
        # Adjust to 12 hour times
        city_time = f"{int(city_time[0:2]) - 12}{city_time[2:]}"

    return(f"{city_time} - {city} - {forecast} {temp}F Wind: {wind}")


def set_rw_icon(forecast, hour):

    icon_convert = {
        'skc': 'icons8-sun-50.png',
        'sct': 'icons8-partly-cloudy-day-50.png',
        'bkn': 'icons8-partly-cloudy-day-50.png',
        'ovc': 'icons8-clouds-50.png',
        'few': 'icons8-partly-cloudy-day-50.png',
        'wind_skc': 'icons8-sun-50.png',
        'wind_few': 'icons8-sun-50.png',
        'wind_sct': 'icons8-partly-cloudy-day-50.png',
        'wink_bkn': 'icons8-partly-cloudy-day-50.png',
        'wind_ovc': 'icons8-clouds-50.png',
        'snow': 'icons8-snow-50.png',
        'rain_snow': 'icons8-sleet-50.png',
        'rain_sleet': 'icons8-sleet-50.png',
        'snow_sleet': 'icons8-sleet-50.png',
        'fzra': 'icons8-sleet-50.png',
        'rain_fzra': 'icons8-sleet-50.png',
        'snow_fzra': 'icons8-sleet-50.png',
        'sleet': 'icons8-sleet-50.png',
        'rain': 'icons8-rain-50.png',
        'rain_showers': 'icons8-rain-50.png',
        'rain_showers_hi': 'icons8-rain-50.png',
        'tsra': 'icons8-storm-50.png',
        'tsra_sct': 'icons8-storm-50.png',
        'tsra-hi': 'icons8-storm-50.png',
        'tornado': 'icons8-box-important-50.png',
        'hurricane': 'icons8-box-important-50.png',
        'tropical_storm': 'icons8-box-important-50.png',
        'dust': 'icons8-dust-50.png',
        'smoke': 'icons8-dust-50.png',
        'haze': 'icons8-haze-50.png',
        'hot': 'icons8-box-important-50.png',
        'cold': 'icons8-box-important-50.png',
        'blizzard': 'icons8-box-important-50.png',
        'fog': 'icons8-haze-50.png',
    }

    # Built in FA icon selection
    icon_url = forecast['properties']['periods'][hour]['icon']
    is_day = forecast['properties']['periods'][hour]['isDaytime']

    icon_code = icon_url.split('/')[6].split('?')[0].split(',')[0]

    icon_name = icon_convert[icon_code]

    # Local icon selection
    i8_icon = folium.features.CustomIcon(f'weather_data/icons/{icon_name}', icon_size=(24, 24), icon_anchor=(10,30))

    return(i8_icon)


def zip_to_coords(zip_code, zip_code_refs):
    """Attempts to convert zip code to coordinates

    Args:
        zip_code (str): Zip code to be converted
        zip_code_refs (dict): Zip code reference dictionary

    Returns:
        zip_coords: None if not in dict or List of two integers representing coordniates
    """
    try:
        zip_data = zip_code_refs[zip_code]
        zip_coords = [zip_data['longitude'], zip_data['latitude']]
    except KeyError:
        zip_coords = None

    return zip_coords
