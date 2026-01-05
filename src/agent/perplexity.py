"""Asynchronous event searcher using Perplexity AI API and httpx."""
import json
from datetime import datetime
from typing import Dict, List, Optional

import backoff
import httpx


class EventSearcher:
    """Asynchronous event searcher using Perplexity AI."""

    def __init__(self, api_key: str):
        """Initialize the event searcher."""
        if not api_key:
            raise ValueError("Perplexity API key must be provided.")
        self.api_key = api_key
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _build_event_search_prompt(
        self,
        city: str,
        country: str,
        month: str,
        year: Optional[int] = None,
        categories: Optional[List[str]] = None,
    ) -> str:
        """Build the prompt for event search."""
        current_year = year or datetime.now().year
        category_filter = (
            f"\nFocus on these categories: {', '.join(categories)}" if categories else ""
        )
        return f"""Search for the most attractive and popular events happening in {city}, {country} during {month} {current_year}.{category_filter}

For each event, provide:
1. Event Name
2. Date(s) - specific dates in {month} {current_year}
3. Venue/Location
4. Event Type/Category (concert, festival, exhibition, sports, theater, etc.)
5. Brief Description (1-2 sentences)
6. Why it's attractive (popularity, uniqueness, cultural significance)
7. Ticket/Booking Information (if available)
8. Official Website or Source

Requirements:
- Only include CONFIRMED events with reliable sources
- Prioritize events with high cultural/entertainment value
- Include diverse event types (music, arts, sports, food, cultural)
- List 8-12 top events
- Sort by attractiveness/popularity
- Include both ticketed and free events
- Verify dates are specifically in {month} {current_year}

Format as a numbered list with clear sections for each event."""

    @backoff.on_exception(
        backoff.expo, (httpx.TimeoutException, httpx.ConnectError), max_tries=3, max_time=90
    )
    async def search_events(
        self,
        city: str = "Antwerp",
        country: str = "Belgium",
        month: str = "October",
        year: Optional[int] = None,
        categories: Optional[List[str]] = None,
        max_tokens: int = 2000,
        temperature: float = 0.3,
    ) -> Dict:
        """Search for events asynchronously."""
        user_prompt = self._build_event_search_prompt(
            city=city, country=country, month=month, year=year, categories=categories
        )
        system_prompt = """You are an expert event curator and local culture specialist.
You have access to real-time information about events, festivals, and cultural activities.
Provide accurate, up-to-date, and well-sourced information.
Be concise but informative. Always cite sources when available."""
        payload = {
            "model": "sonar",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": 0.9,
            "search_domain_filter": ["perplexity.ai"],
            "return_images": False,
            "return_related_questions": True,
            "search_recency_filter": "month",
        }
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.base_url, headers=self.headers, json=payload, timeout=30
                )
                response.raise_for_status()
                return response.json()
            except httpx.RequestError as e:
                return {
                    "error": str(e),
                    "status_code": e.response.status_code if e.response else None,
                    "response_text": e.response.text if e.response else None,
                }

    def format_results(self, response: Dict) -> str:
        """Format the event search results."""
        if "error" in response:
            return f"❌ Error: {response['error']}"
        try:
            content = response["choices"][0]["message"]["content"]
            citations = response.get("citations", [])
            output = "🎭 EVENT SEARCH RESULTS\n"
            output += "=" * 60 + "\n\n"
            output += content
            if citations:
                output += "\n\n" + "=" * 60
                output += "\n📚 SOURCES:\n"
                for i, citation in enumerate(citations, 1):
                    output += f"{i}. {citation}\n"
            return output
        except (KeyError, IndexError) as e:
            return f"❌ Error parsing response: {e}\n{json.dumps(response, indent=2)}"
