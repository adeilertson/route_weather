"""
Route Weather Support Functions

Author: Andrew Eilertson
Created: May 21st 2021
URL: https://github.com/adeilertson/route_weather
"""
import folium
from folium.map import Popup
from api_callers import get_ors_route, get_nws_hourly_url, get_nws_forecast
from converters import coords_to_city
from data_loaders import get_zip_data


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


def get_route_weather(depart_coords, destination_coords):
    """
    Get weather for route between depart and destination coordinates

    Args:
        depart_coords (float): Coordinates for starting location
        destination_coords (float): Coordinates for ending location
        printing (bool): Controls if status updates are printed. Defaults to True

    Returns:
        dict: Route data from Open Route Service
        list: List of dicts containing checkpoints with location and weather data
    """

    # Get zip codes and locations
    zip_codes, zip_locs = get_zip_data()

    # Get route data
    route_data = get_ors_route(depart_coords, destination_coords)

    # Get checkpoint locations
    checkpoints = find_checkpoints(route_data)

    # Get hourly url
    for cp in checkpoints:
        hourly_url = get_nws_hourly_url(cp['lat'], cp['lon'], True)
        cp['hourly_url'] = hourly_url

    # Get forecast
    for cp in checkpoints:
        forecast = get_nws_forecast(cp['hourly_url'])
        cp['forecast'] = forecast

    # Set checkpoint cites
    for cp in checkpoints:
        cp['city'] = coords_to_city(cp['lat'], cp['lon'], zip_locs)

    return(route_data, checkpoints)


def popup_builder(checkpoint, loc_report, icon):
    """
    Builds Folium map marker and popup with provided weather data and icon

    Args:
        checkpoint(dict): Dict with checkpoint 'lat' and 'lon' for marker placement
        loc_report(str): Short weather report string for popup
        icon(str): File path to icon

    Returns:
        list: List of dicts with lat/lon, city, state, zip code data (and extranously dst, geopoint, and timezone)
    """
    popup = folium.Marker(
    location=[checkpoint['lat'], checkpoint['lon']],
    popup=Popup(loc_report, min_width=100, max_width=300),
    icon=icon)
    return(popup)


def set_hourly_forecast(city, hourly_data, hour):
    """
    Builds short weather report at specified hour

    Args:
        city(str): Dict with checkpoint 'lat' and 'lon' for marker placement
        hourly_data(dict): NWS API hourly forecast data for location
        hour(int): Hour of forecast to get (0 based)

    Returns:
        str: Short weather report with expected arrival time, city, forecast, temp and wind
    """
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
    """
    Determine icon to use based on NWS icon for specified hour of forecast

    Args:
        forecast(dict): NWS API hourly forecast data for location
        hour(int): Hour of forecast to get (0 based)

    Returns:
        str: File path to icon
    """
    # Conversion dict
    icon_convert = {
        'skc-day': 'icons8-sun-50.png',
        'sct-day': 'icons8-partly-cloudy-day-50.png',
        'bkn-day': 'icons8-partly-cloudy-day-50.png',
        'few-day': 'icons8-partly-cloudy-day-50.png',
        'wind_skc-day': 'icons8-sun-50.png',
        'wind_few-day': 'icons8-sun-50.png',
        'wind_sct-day': 'icons8-partly-cloudy-day-50.png',
        'wind_bkn-day': 'icons8-partly-cloudy-day-50.png',
        'skc-night': 'icons8-moon-and-stars-50.png',
        'sct-night': 'icons8-partly-cloudy-night-50.png',
        'bkn-night': 'icons8-partly-cloudy-night-50.png',
        'few-night': 'icons8-partly-cloudy-night-50.png',
        'wind_skc-night': 'icons8-moon-and-stars-50.png',
        'wind_few-night': 'icons8-moon-and-stars-50.png',
        'wind_sct-night': 'icons8-partly-cloudy-night-50.png',
        'wind_bkn-night': 'icons8-partly-cloudy-night-50.png',
        'ovc': 'icons8-clouds-50.png',
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
        'hot': 'icons8-box-important-red-50.png',
        'cold': 'icons8-box-important-blue-50.png',
        'blizzard': 'icons8-box-important-50.png',
        'fog': 'icons8-haze-50.png',
    }

    # Built in FA icon selection
    icon_url = forecast['properties']['periods'][hour]['icon']
    is_day = forecast['properties']['periods'][hour]['isDaytime']

    icon_code = icon_url.split('/')[6].split('?')[0].split(',')[0]

    time_sensitive_icon_codes = [
        'skc',
        'sct',
        'bkn',
        'few',
        'wind_skc',
        'wind_few',
        'wind_sct',
        'wind_bkn',
    ]

    if icon_code in time_sensitive_icon_codes:
        if is_day is True:
            icon_code = f"{icon_code}-day"
        else:
            icon_code = f"{icon_code}-night"

    icon_name = icon_convert[icon_code]

    # Local icon selection
    i8_icon = folium.features.CustomIcon(f'weather_data/icons/{icon_name}', icon_size=(24, 24), icon_anchor=(10,30))

    return(i8_icon)
