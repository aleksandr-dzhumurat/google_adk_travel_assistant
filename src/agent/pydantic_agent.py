"""Pydantic-AI agent implementation with event discovery tools."""
import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List

from pydantic_ai import RunContext
from pydantic_ai.tools import Tool

from .geo_tools import (
    geocode_address as geocode_address_from_mapbox,
    geocode_address_near as geocode_address_near_from_mapbox,
    get_city_center as get_city_center_from_mapbox,
    reverse_geocode as reverse_geocode_from_mapbox,
)
from .perplexity import EventSearcher


@dataclass
class AgentDependencies:
    """Dependencies injected into agent context."""

    mapbox_token: str
    perplexity_api_key: str
    event_searcher: EventSearcher


def get_tools(executor) -> List[Tool]:
    """Get the list of tools for the agent."""

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

        result = await get_city_center_from_mapbox(
            city, country, ctx.deps.mapbox_token
        )

        logger.info(f"🔧 TOOL RESULT: get_city_center returned: {result}")
        return result

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
        logger.info(
            f"🔧 TOOL CALLED: search_events(city={city}, country={country}, lat={center_latitude}, lon={center_longitude})"
        )

        month = datetime.now().strftime("%B")
        year = datetime.now().year

        results = await ctx.deps.event_searcher.search_events(
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

        logger.info(
            f"🔧 TOOL RESULT: search_events returned {len(results.get('events', []))} events"
        )
        return results

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
        return await geocode_address_near_from_mapbox(
            address,
            proximity_latitude,
            proximity_longitude,
            city,
            country,
            ctx.deps.mapbox_token,
        )

    async def geocode_address(
        ctx: RunContext[AgentDependencies], address: str
    ) -> dict:
        """Convert address to coordinates (basic version).

        NOTE: Avoid using this for event venues. Use geocode_address_near instead
        to ensure results are from the correct city/country.

        Args:
            address: Full address string

        Returns:
            dict with coordinates, place_name, full_response or error
        """
        return await geocode_address_from_mapbox(address, ctx.deps.mapbox_token)

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
        return await reverse_geocode_from_mapbox(
            latitude, longitude, ctx.deps.mapbox_token
        )

    return [
        Tool(get_city_center),
        Tool(search_events),
        Tool(geocode_address_near),
        Tool(geocode_address),
        Tool(reverse_geocode),
    ]
