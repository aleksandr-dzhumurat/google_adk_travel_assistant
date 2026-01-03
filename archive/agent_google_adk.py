import os
from datetime import datetime
from typing import Dict

from dotenv import load_dotenv
from google import genai
from google.adk import Agent
from google.adk.tools import FunctionTool

from .geo_tools import (
    geocode_address,
    geocode_address_near,
    get_city_center,
    reverse_geocode,
)
from .perplexity import EventSearcher

print(f"Loaded vars: {load_dotenv()}")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
AGENT_NAME = os.getenv("AGENT_NAME", "event_route_agent")

client = genai.Client(api_key=GOOGLE_API_KEY) if GOOGLE_API_KEY else None

event_searcher = EventSearcher()


def search_events(
    city: str, country: str, center_latitude: float, center_longitude: float
) -> Dict:
    month = datetime.now().strftime("%B")
    year = datetime.now().year

    results = event_searcher.search_events(
        city=city, country=country, month=month, year=year, categories=None
    )

    if "error" not in results:
        results["search_center"] = {
            "latitude": center_latitude,
            "longitude": center_longitude,
            "location": f"{city}, {country}",
        }

    return results


mapbox_agent = Agent(
    name=AGENT_NAME,
    model="gemini-2.0-flash-exp",
    instruction="""You are an intelligent event discovery and route planning assistant.

Your workflow should follow these steps:

1. **Clarify Location**: First, ask the user to specify the country and city they want to explore if not already provided.

2. **Get City Center Coordinates**: Before searching for events, use the get_city_center tool to obtain the coordinates of the city center. This provides a reference point for event search and route planning.

3. **Search for Events**: Use the search_events tool with the city, country, and center coordinates to find the top popular events happening in that city for the current month.

4. **Present Events to User**: After receiving the event search results:
   - Present the list of events to the user in a clear, numbered format
   - Include key details for each event (name, date/time, venue, description)
   - Ensure dates are clearly formatted and easy to read
   - Ask the user to select which events they're interested in visiting
   - Wait for the user's response before proceeding

5. **Geocode ONLY Chosen Event Venues**: After the user selects specific events:
   - ONLY geocode the addresses/venues that the user has chosen
   - For each chosen venue, use geocode_address_near with ALL required parameters: address, city center lat/lon, city name, and country name
   - This ensures results are from the correct city and country (not from other countries with similar venue names)
   - The function uses multiple constraints: proximity bias, bounding box, and enhanced query with city/country
   - DO NOT geocode events the user didn't select

6. **Provide Google Maps Links**: At the end of your response, include a section with clickable Google Maps links for ONLY the chosen event locations:
   - Format: https://www.google.com/maps?q=LATITUDE,LONGITUDE
   - Example: https://www.google.com/maps?q=37.7749,-122.4194
   - Create one link per event venue with a clear label showing the event name AND date
   - Include the event date/time prominently with each link
   - This allows users to easily open the location in Google Maps and know when the event is happening

Always be helpful, clear, and enthusiastic about helping users discover great events and plan their visits!

Available tools:
- get_city_center: Get the center coordinates of a city (USE THIS FIRST after getting city/country from user)
- search_events: Find top events in a city for the current month (requires city center coordinates)
- geocode_address_near: Convert addresses to coordinates with strong locality constraints (REQUIRED for venues - needs address, proximity lat/lon, city, country)
- geocode_address: Convert addresses to coordinates (basic version - avoid using for event venues)
- reverse_geocode: Convert coordinates to addresses""",
    tools=[
        FunctionTool(get_city_center),
        FunctionTool(search_events),
        FunctionTool(geocode_address_near),
        FunctionTool(geocode_address),
        FunctionTool(reverse_geocode),
    ],
)
