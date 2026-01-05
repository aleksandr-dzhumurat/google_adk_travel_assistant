"""Asynchronous geocoding tools using Mapbox API and httpx."""
import httpx
from urllib.parse import quote

MAPBOX_API_BASE = "https://api.mapbox.com"


async def get_city_center(city: str, country: str, mapbox_token: str) -> dict:
    """Get the center coordinates of a city."""
    try:
        query = f"{city}, {country}"
        url = f"{MAPBOX_API_BASE}/geocoding/v5/mapbox.places/{quote(query)}.json"
        params = {
            "access_token": mapbox_token,
            "limit": 1,
            "types": "place",
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        if data.get("features"):
            feature = data["features"][0]
            coords = feature["geometry"]["coordinates"]
            return {
                "longitude": coords[0],
                "latitude": coords[1],
                "city": city,
                "country": country,
                "place_name": feature["place_name"],
            }
        else:
            return {"error": f"Could not find coordinates for {city}, {country}"}
    except Exception as e:
        return {"error": str(e)}


async def geocode_address(address: str, mapbox_token: str) -> dict:
    """Convert address to coordinates (basic version)."""
    try:
        url = f"{MAPBOX_API_BASE}/geocoding/v5/mapbox.places/{quote(address)}.json"
        params = {"access_token": mapbox_token, "limit": 1}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        if data.get("features"):
            feature = data["features"][0]
            return {
                "coordinates": feature["geometry"]["coordinates"],
                "place_name": feature["place_name"],
                "full_response": feature,
            }
        else:
            return {"error": "No results found"}
    except Exception as e:
        return {"error": str(e)}


async def geocode_address_near(
    address: str,
    proximity_latitude: float,
    proximity_longitude: float,
    city: str,
    country: str,
    mapbox_token: str,
) -> dict:
    """Convert addresses to coordinates with strong locality constraints."""
    try:
        enhanced_query = f"{address}, {city}, {country}"
        url = f"{MAPBOX_API_BASE}/geocoding/v5/mapbox.places/{quote(enhanced_query)}.json"

        bbox_delta = 0.45
        bbox = (
            f"{proximity_longitude - bbox_delta},{proximity_latitude - bbox_delta},"
            f"{proximity_longitude + bbox_delta},{proximity_latitude + bbox_delta}"
        )

        params = {
            "access_token": mapbox_token,
            "limit": 1,
            "proximity": f"{proximity_longitude},{proximity_latitude}",
            "bbox": bbox,
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        if data.get("features"):
            feature = data["features"][0]
            return {
                "coordinates": feature["geometry"]["coordinates"],
                "place_name": feature["place_name"],
                "city": city,
                "country": country,
                "proximity_used": {
                    "latitude": proximity_latitude,
                    "longitude": proximity_longitude,
                },
                "full_response": feature,
            }
        else:
            return {"error": f"No results found for '{address}' in {city}, {country}"}
    except Exception as e:
        return {"error": str(e)}


async def reverse_geocode(latitude: float, longitude: float, mapbox_token: str) -> dict:
    """Convert coordinates to human-readable address."""
    try:
        url = f"{MAPBOX_API_BASE}/geocoding/v5/mapbox.places/{longitude},{latitude}.json"
        params = {"access_token": mapbox_token}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        if data.get("features"):
            feature = data["features"][0]
            return {
                "address": feature["place_name"],
                "coordinates": [longitude, latitude],
                "full_response": feature,
            }
        else:
            return {"error": "No results found"}
    except Exception as e:
        return {"error": str(e)}
