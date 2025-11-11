#!/usr/bin/env python3
"""
Test script for the Mapbox agent tools.
This is a simple CLI tool to test agent functionality.

Usage:
    PYTHONPATH=src python scripts/test_agent.py
    or
    make test-agent
"""

import os

from dotenv import load_dotenv

from agent import mapbox_agent
from agent.geo_tools import geocode_address, get_city_center, reverse_geocode

print(f"Loaded vars: {load_dotenv()}")


def main():
    """Main entry point for testing the agent tools."""
    MAPBOX_TOKEN = os.getenv("MAPBOX_ACCESS_TOKEN")

    print("=" * 70)
    print(f"🗺️  Testing {mapbox_agent.name}")
    print("=" * 70)
    print(f"Mapbox token configured: {'Yes' if MAPBOX_TOKEN else 'No'}")
    print(f"Agent initialized with {len(mapbox_agent.tools)} tools\n")

    # Test 1: Get City Center
    print("Test 1: Get City Center")
    print("-" * 70)
    city = "Paris"
    country = "France"
    print(f"City: {city}, {country}")
    city_result = get_city_center(city, country)
    if "error" not in city_result:
        print(
            f"✅ Center Coordinates: ({city_result['latitude']}, {city_result['longitude']})"
        )
        print(f"   Place: {city_result['place_name']}\n")
    else:
        print(f"❌ Error: {city_result['error']}\n")

    # Test 2: Geocoding
    print("Test 2: Geocoding")
    print("-" * 70)
    address = "1600 Amphitheatre Parkway, Mountain View, CA"
    print(f"Address: {address}")
    result = geocode_address(address)
    if "error" not in result:
        print(f"✅ Coordinates: {result['coordinates']}")
        print(f"   Place: {result['place_name']}\n")
    else:
        print(f"❌ Error: {result['error']}\n")

    # Test 3: Reverse Geocoding
    if "coordinates" in result:
        print("Test 3: Reverse Geocoding")
        print("-" * 70)
        lon, lat = result["coordinates"]
        print(f"Coordinates: ({lat}, {lon})")
        reverse_result = reverse_geocode(lat, lon)
        if "error" not in reverse_result:
            print(f"✅ Address: {reverse_result['address']}\n")
        else:
            print(f"❌ Error: {reverse_result['error']}\n")

    print("=" * 70)
    print("✅ All tests completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
