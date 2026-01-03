"""Pydantic-AI agent implementation with event discovery tools."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from typing import Dict

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.gemini import GeminiModel

from .geo_tools import (
    geocode_address as sync_geocode_address,
    geocode_address_near as sync_geocode_address_near,
    get_city_center as sync_get_city_center,
    reverse_geocode as sync_reverse_geocode,
)
from .perplexity import EventSearcher

# Thread pool for running sync operations
executor = ThreadPoolExecutor(max_workers=4)


@dataclass
class AgentDependencies:
    """Dependencies injected into agent context."""

    mapbox_token: str
    perplexity_api_key: str
    event_searcher: EventSearcher


# System prompt
SYSTEM_PROMPT = """You are an event discovery assistant.

CRITICAL RULES:
1. DO NOT explain what you're going to do - JUST DO IT
2. DO NOT say "I will get coordinates" or "I'll search" - USE THE TOOLS IMMEDIATELY
3. When you have city and country - call BOTH tools (get_city_center AND search_events) BEFORE responding with text

Your workflow:

1. If no city/country provided: Ask for them briefly

2. If city and country are provided:
   - IMMEDIATELY call get_city_center(city, country)
   - IMMEDIATELY call search_events(city, country, lat, lon) with the coordinates from step above
   - THEN present the event list

DO NOT generate explanatory text before calling tools. Call tools FIRST, present results AFTER.

3. **Wait for User Selection**: After presenting events, ask the user which events they want to visit and wait for their response.

4. **Geocode ONLY Chosen Event Venues**: After the user selects specific events:
   - ONLY geocode the addresses/venues that the user has chosen
   - For each chosen venue, use geocode_address_near with ALL required parameters: address, city center lat/lon, city name, and country name
   - This ensures results are from the correct city and country (not from other countries with similar venue names)
   - The function uses multiple constraints: proximity bias, bounding box, and enhanced query with city/country
   - DO NOT geocode events the user didn't select

5. **Provide Google Maps Links**: At the end of your response, include a section with clickable Google Maps links for ONLY the chosen event locations:
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
- reverse_geocode: Convert coordinates to addresses"""


# Create pydantic-ai agent with exhaustive tool execution
event_agent = Agent(
    model=GeminiModel("gemini-2.0-flash-exp"),
    deps_type=AgentDependencies,
    system_prompt=SYSTEM_PROMPT,
    retries=2,
    end_strategy='exhaustive',  # Execute ALL tool calls, don't stop early
)


@event_agent.tool
async def get_city_center(
    ctx: RunContext[AgentDependencies], city: str, country: str
) -> dict:
    """Get the center coordinates of a city.

    Args:
        city: City name
        country: Country name

    Returns:
        dict with longitude, latitude, city, country, place_name or error
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"🔧 TOOL CALLED: get_city_center(city={city}, country={country})")

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(executor, sync_get_city_center, city, country)

    logger.info(f"🔧 TOOL RESULT: get_city_center returned: {result}")
    return result


@event_agent.tool
async def search_events(
    ctx: RunContext[AgentDependencies],
    city: str,
    country: str,
    center_latitude: float,
    center_longitude: float,
) -> Dict:
    """Search for popular events in a city for the current month.

    Args:
        city: City name
        country: Country name
        center_latitude: Latitude of city center
        center_longitude: Longitude of city center

    Returns:
        dict with event search results including search_center location
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"🔧 TOOL CALLED: search_events(city={city}, country={country}, lat={center_latitude}, lon={center_longitude})")

    month = datetime.now().strftime("%B")
    year = datetime.now().year

    # Run EventSearcher.search_events in executor (has @backoff retry)
    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(
        executor,
        ctx.deps.event_searcher.search_events,
        city,
        country,
        month,
        year,
        None,  # categories
    )

    # Add search center info if no error
    if "error" not in results:
        results["search_center"] = {
            "latitude": center_latitude,
            "longitude": center_longitude,
            "location": f"{city}, {country}",
        }

    logger.info(f"🔧 TOOL RESULT: search_events returned {len(results.get('events', []))} events")
    return results


@event_agent.tool
async def geocode_address_near(
    ctx: RunContext[AgentDependencies],
    address: str,
    proximity_latitude: float,
    proximity_longitude: float,
    city: str,
    country: str,
) -> dict:
    """Convert addresses to coordinates with strong locality constraints.

    This is the REQUIRED tool for geocoding event venues. It uses proximity bias,
    bounding box, and enhanced query to ensure results are from the correct city.

    Args:
        address: Address or venue name
        proximity_latitude: Latitude of city center for proximity bias
        proximity_longitude: Longitude of city center for proximity bias
        city: City name for enhanced query
        country: Country name for enhanced query

    Returns:
        dict with coordinates, place_name, city, country or error
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        executor,
        sync_geocode_address_near,
        address,
        proximity_latitude,
        proximity_longitude,
        city,
        country,
    )


@event_agent.tool
async def geocode_address(ctx: RunContext[AgentDependencies], address: str) -> dict:
    """Convert address to coordinates (basic version).

    NOTE: Avoid using this for event venues. Use geocode_address_near instead
    to ensure results are from the correct city/country.

    Args:
        address: Full address string

    Returns:
        dict with coordinates, place_name, full_response or error
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, sync_geocode_address, address)


@event_agent.tool
async def reverse_geocode(
    ctx: RunContext[AgentDependencies], latitude: float, longitude: float
) -> dict:
    """Convert coordinates to human-readable address.

    Args:
        latitude: Geographic latitude
        longitude: Geographic longitude

    Returns:
        dict with address, coordinates, full_response or error
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, sync_reverse_geocode, latitude, longitude)
