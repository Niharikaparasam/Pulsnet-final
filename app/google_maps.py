# app/google_maps.py
import requests

# 🔐 Your OpenRouteService basic key
ORS_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjQ5OTI0ZDVkYTM2NzQzYmQ4NWJmMjZjYzU2OGI3NjI1IiwiaCI6Im11cm11cjY0In0="

def distance_matrix(origins: list, destinations: list, mode: str = "driving"):
    """
    Compatible wrapper for existing main.py code.

    main.py passes:
        origins:      ["lat,lon"]
        destinations: ["lat,lon", "lat,lon", ...]

    This function:
    - parses those strings
    - calls OpenRouteService Matrix API
    - returns ORS JSON
    """

    url = "https://api.openrouteservice.org/v2/matrix/driving-car"

    # origins + destinations come as strings "lat,lon"
    coord_strings = origins + destinations

    coords = []
    for s in coord_strings:
        if not s:
            # keep placeholder for invalid ones
            coords.append([0.0, 0.0])
            continue
        try:
            lat_str, lon_str = s.split(",")
            lat = float(lat_str)
            lon = float(lon_str)
            # ORS expects [lon, lat]
            coords.append([lon, lat])
        except Exception:
            # fallback if parsing fails
            coords.append([0.0, 0.0])

    payload = {
        "locations": coords,
        "metrics": ["distance", "duration"]
    }

    headers = {
        "Authorization": ORS_KEY,
        "Content-Type": "application/json"
    }

    resp = requests.post(url, json=payload, headers=headers, timeout=20)
    resp.raise_for_status()
    return resp.json()


def geocode_address(address: str):
    """
    Free geocoding using OpenRouteService.
    Converts address -> (lat, lon)
    """
    url = "https://api.openrouteservice.org/geocode/search"
    params = {
        "api_key": ORS_KEY,
        "text": address
    }
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    if "features" in data and data["features"]:
        coords = data["features"][0]["geometry"]["coordinates"]  # [lon, lat]
        return (coords[1], coords[0])  # return (lat, lon)

    return None
