"""
Route Weather Conversion Functions

Author: Andrew Eilertson
Created: May 21st 2021
URL: https://github.com/adeilertson/route_weather
"""

def coords_to_city(latitude, longitude, zip_locs):
    """
    Converts lat/lon to city (US) in provided zip locations

    Args:
        latitude (float): Latitude for location to convert
        longitude (float): Longitude for location to convert
        zip_locs (list): List of dicts with lat/lon data for cities

    Returns:
        str: Nearest city for coordinates
    """
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
    """
    Converts lat/lon to state (US) in provided zip locations

    Args:
        latitude (float): Latitude for location to convert
        longitude (float): Longitude for location to convert
        zip_locs (list): List of dicts with lat/lon data for states

    Returns:
        str: State for coordinates
    """
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
    """
    Converts lat/lon to zip code (US) in provided zip locations

    Args:
        latitude (float): Latitude for location to convert
        longitude (float): Longitude for location to convert
        zip_locs (list): List of dicts with lat/lon data for zip codes

    Returns:
        str: Zip code for coordinates. Returns blank string ('') if no match found.
    """
    coord_lat = round(latitude, 1)
    coord_lon = round(longitude, 1)

    for loc in zip_locs:
        if round(loc['latitude'], 1) == coord_lat and round(loc['longitude'], 1) == coord_lon:
            zip_code = loc['zip']
            break
    else:
        zip_code = ''

    return(zip_code)


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
