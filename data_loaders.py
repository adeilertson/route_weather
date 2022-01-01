"""
Route Weather Data Loading and Writing Functions

Author: Andrew Eilertson
Created: May 21st 2021
URL: https://github.com/adeilertson/route_weather
"""

import pickle

def add_gridpoints(data):
    """
    Adds new gridpoints to known gridpoints for future reference.

    Args:
        data (dict): Gridpoint reference dict with keys 'lat', 'lon', and 'hourly_url'

    Returns:
        none
    """
    with open(f'weather_data/gridpoint_coords.pkl', 'wb') as file:
        pickle.dump(data, file)


def get_zip_data():
    """
    Convienient loader for zip_codes and zip_locs references

    Args:
        none

    Returns:
        dict: Dict of zip codes with city, state, lat, and lon data
        list: List of dicts with lat/lon, city, state, zip code data (and extranously dst, geopoint, and timezone)
    """
    zip_codes = load_zip_codes()
    zip_locs = load_zip_locs()

    return(zip_codes, zip_locs)


def load_gridpoints():
    """
    Loads known gridpoints from pickle file for easier conversion to NWS API hourly URL

    Args:
        none

    Returns:
        dict: Gridpoint reference dict with keys 'lat', 'lon', and 'hourly_url'
    """
    with open(f'weather_data/gridpoint_coords.pkl', 'rb') as file:
        data = pickle.load(file)
    return data


def load_zip_codes():
    """
    Loads zip code data from pickle file

    Args:
        none

    Returns:
        dict: Dict of zip codes with city, state, lat, and lon data
    """
    with open(f'weather_data/zip_codes.pkl', 'rb') as file:
        data = pickle.load(file)
    return data


def load_zip_locs():
    """
    Loads zip location data from pickle file

    Args:
        none

    Returns:
        list: List of dicts with lat/lon, city, state, zip code data (and extranously dst, geopoint, and timezone)
    """
    with open(f'weather_data/zip_locs.pkl', 'rb') as file:
        data = pickle.load(file)
    return data


def reset_gridpoints():
    """
    Reset known gridpoint reference list, overwriting current list with blank list.

    Args:
        none

    Returns:
        none
    """
    blank_set = []
    add_gridpoints(blank_set)
