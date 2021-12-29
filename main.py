"""
Route Weather

Author: Andrew Eilertson
Created: May 21st 2021
URL: https://github.com/adeilertson/route_weather

Icons by Icons8
Routing by Open Route Service
Weather data by National Weather Service API

    Usage:

    Add config.py file with the following:
        api_key = KEY
        local_run = True

    Start the flask server by running:
        $ python main.py

    Open web browser and go to the sample route:
        http://127.0.0.1:5000/?sz=55118&ez=57105

"""
from flask import Flask
from flask import request
import folium

from support import (
    coords_to_city,
    find_checkpoints,
    get_forecast,
    get_hourly_url,
    get_zip_data,
    get_zip_data,
    get_route,
    popup_builder,
    set_rw_icon,
    set_hourly_forecast,
    zip_to_coords,
)

from config import local_run

# Primary process
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
    route_data = get_route(depart_coords, destination_coords)

    # Get checkpoint locations
    checkpoints = find_checkpoints(route_data)

    # Get hourly url
    for cp in checkpoints:
        hourly_url = get_hourly_url(cp['lat'], cp['lon'], True)
        cp['hourly_url'] = hourly_url

    # Get forecast
    for cp in checkpoints:
        forecast = get_forecast(cp['hourly_url'])
        cp['forecast'] = forecast

    # Set checkpoint cites
    for cp in checkpoints:
        cp['city'] = coords_to_city(cp['lat'], cp['lon'], zip_locs)

    return(route_data, checkpoints)

app = Flask(__name__)

@app.route('/')
def run_rw():
    # Get start and end zip codes from URL arguments
    depart_zip = request.args.get('sz')
    destination_zip = request.args.get('ez')

    # Get zip codes and locations
    zip_codes, zip_locs = get_zip_data()

    depart_coords = zip_to_coords(depart_zip, zip_codes)
    destination_coords = zip_to_coords(destination_zip, zip_codes)

    # Get route data and checkpoints
    route, checkpoints = get_route_weather(depart_coords, destination_coords)

    # Get midpoint of route to focus map
    midpoint = find_checkpoints(route, midpoint=True)[0]

    # Create map, focused on midpoint
    map = folium.Map(location=[midpoint['lat'],midpoint['lon']], zoom_start=8)

    # Add route to map
    folium.GeoJson(route, name='route').add_to(map)

    # Add layer control to map
    folium.LayerControl().add_to(map)

    # Add checkpoints to map
    for hour, cp in enumerate(checkpoints):
        loc_report = set_hourly_forecast(cp['city'], cp['forecast'], hour)
        icon = set_rw_icon(cp['forecast'], hour)
        cp_popup = popup_builder(cp, loc_report, icon)
        cp_popup.add_to(map)

    return map._repr_html_()

if local_run is True:
    if __name__ == '__main__':
        app.run(debug=True)