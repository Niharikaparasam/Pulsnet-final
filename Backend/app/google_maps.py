# app/google_maps.py
import os
import requests
from urllib.parse import urlencode
from dotenv import load_dotenv
load_dotenv()

# 🔐 Your OpenRouteService basic key
ORS_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjQ5OTI0ZDVkYTM2NzQzYmQ4NWJmMjZjYzU2OGI3NjI1IiwiaCI6Im11cm11cjY0In0="

DIRECTIONS_URL = "https://api.openrouteservice.org/v2/directions/driving-car"
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

def directions_route(origin: tuple, destination: tuple, extra: dict = None):
    """
    origin: (lat, lon)
    destination: (lat, lon)
    returns: dict with keys: geometry (list of [lat, lon]), distance_m, duration_s, raw (full JSON)
    """
    if not ORS_KEY:
        raise Exception("ORS API key not set on server (ORS_KEY).")

    # ORS expects coordinates as [[lon, lat],[lon, lat]]
    coords = [[origin[1], origin[0]], [destination[1], destination[0]]]
    payload = {
        "coordinates": coords,
        "units": "m",           # meters
        "instructions": False,  # we don't need step-by-step for now
    }
    if extra:
        payload.update(extra)

    headers = {
        "Authorization": ORS_KEY,
        "Content-Type": "application/json"
    }

    resp = requests.post(DIRECTIONS_URL, json=payload, headers=headers, timeout=20)
    resp.raise_for_status()
    data = resp.json()

    # Parse geometry: ORS returns geometry in "features"[0]["geometry"]["coordinates"] as [lon,lat] pairs
    coords_list = []
    try:
        coords_raw = data["features"][0]["geometry"]["coordinates"]
        # convert to [lat, lon] order for Leaflet
        coords_list = [[c[1], c[0]] for c in coords_raw]
    except Exception:
        coords_list = []

    distance_m = None
    duration_s = None
    try:
        props = data["features"][0]["properties"]["summary"]
        distance_m = props.get("distance")  # meters
        duration_s = props.get("duration")  # seconds
    except Exception:
        pass

    return {
        "geometry": coords_list,
        "distance_m": distance_m,
        "duration_s": duration_s,
        "raw": data
    }
