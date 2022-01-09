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
        api_key = Open Route Service API key
        flask_key = KEY
        local_run = True

    Start the flask server by running:
        $ python main.py

    Open web browser and go to the sample route:
        http://127.0.0.1:5000/?sz=55118&ez=57105

"""
from flask import Flask, render_template, request, flash, redirect, url_for
import folium

from converters import zip_to_coords
from data_loaders import get_zip_data

from support import (
    find_checkpoints,
    get_route_weather,
    popup_builder,
    set_rw_icon,
    set_hourly_forecast,
)

from config import local_run, flask_key, version

app = Flask(__name__)
app.config['SECRET_KEY'] = flask_key
routes = []


@app.route('/', methods=('GET', 'POST'))
def index():
    if request.method == 'POST':
        start_zip = request.form['start_zip_code']
        end_zip = request.form['end_zip_code']
        delay = request.form['delay']

        if not start_zip:
            flash('Start zip code required')
        elif not end_zip:
            flash('End zip code required')
        elif not delay:
            flash('Delay required')
        else:
            routes.append({'start_zip': start_zip, 'end_zip': end_zip, 'delay': delay})
            route_url = f"/map/?sz={start_zip}&ez={end_zip}&d={delay}"
            return redirect(route_url)

    return render_template('index.html')


@app.route('/about/')
def about():
    return render_template('about.html', version=version)

@app.route('/error/<error>')
def error_page(error):
    error_list = {
        'depart_zip': 'Unable to map depart zip. Please verify the zip or try a zip closer to larger city',
        'destination_zip': 'Unable to map destination zip. Please verify the zip or try a zip closer to larger city',
        'delay_type': 'Delay required to be number',
        'ors_routing': 'Error getting route from OpenRouteService',
    }

    if error in error_list.keys():
        error_msg = error_list[error]
    else:
        error_msg = 'Unknown error'
    return render_template('error.html', error_msg=error_msg)

@app.route('/map/')
def run_rw():
    depart_zip = request.args.get('sz')
    destination_zip = request.args.get('ez')
    delay = request.args.get('d')

    # Get zip codes and locations
    zip_codes, zip_locs = get_zip_data()

    depart_coords = zip_to_coords(depart_zip, zip_codes)
    destination_coords = zip_to_coords(destination_zip, zip_codes)

    # Data verification
    if depart_coords is None:
        error = 'depart_zip'
        return redirect(url_for('error_page', error=error))
    elif destination_coords is None:
        error = 'destination_zip'
        return redirect(url_for('error_page', error=error))
    
    try:
        delay = int(delay)
    except ValueError:
        error = 'delay_type'
        return redirect(url_for('error_page', error=error))

    # Get route data and checkpoints
    route, checkpoints = get_route_weather(depart_coords, destination_coords)
    # Error check
    if route['error'] is True:
        error = 'ors_routing'
        return redirect(url_for('error_page', error=error))

    # Get midpoint of route to focus map
    midpoint = find_checkpoints(route, midpoint=True)[0]

    # Create map, focused on midpoint
    map = folium.Map(location=[midpoint['lat'],midpoint['lon']], zoom_start=8)

    # Add route to map
    folium.GeoJson(route, name='route').add_to(map)

    # Add layer control to map
    folium.LayerControl().add_to(map)

    # Add checkpoints to map
    for hour, cp in enumerate(checkpoints, start=delay):
        # Time in forecast check
        if hour > 155:
            cp['error'] = True
            cp['error_msg'] = 'No weather data for time period'
        if cp['error'] is False:
            loc_report = set_hourly_forecast(cp['city'], cp['forecast'], hour)
            icon = set_rw_icon(cp['forecast'], hour)
        else:
            loc_report = cp['error_msg']
            icon = set_rw_icon('error', 0)
        cp_popup = popup_builder(cp, loc_report, icon)
        cp_popup.add_to(map)

    return map._repr_html_()

if local_run is True:
    if __name__ == '__main__':
        app.run(debug=True)