# get_location.py

import geocoder


def get_location():
    """
    Get approximate latitude and longitude using IP geolocation.
    Returns (-1, -1) if location cannot be determined.
    """

    try:
        g = geocoder.ip("me")

        if g.ok and g.latlng:
            lat, lon = g.latlng
            return lat, lon

        else:
            return -1, -1

    except Exception as e:
        print("Location detection failed:", e)
        return -1, -1