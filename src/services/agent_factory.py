"""Factory for creating agent instances with dependencies."""
from pydantic_ai import Agent

from ..agent.perplexity import EventSearcher
from ..agent.pydantic_agent import AgentDependencies, event_agent
from ..config.settings import Settings


class AgentFactory:
    """Factory for creating agent instances with dependency injection."""

    def __init__(self, settings: Settings):
        """Initialize agent factory.

        Args:
            settings: Application settings instance
        """
        self.settings = settings
        self.event_searcher = EventSearcher(api_key=settings.perplexity_api_key)

    def create_agent(self) -> Agent:
        """Create agent instance.

        The event_agent is a module-level singleton shared across all sessions.
        Each session uses the same agent but with different message history.

        Returns:
            Agent instance
        """
        return event_agent

    def create_dependencies(self) -> AgentDependencies:
        """Create dependencies for agent context.

        Returns:
            AgentDependencies instance with API keys and services
        """
        return AgentDependencies(
            mapbox_token=self.settings.mapbox_access_token,
            perplexity_api_key=self.settings.perplexity_api_key,
            event_searcher=self.event_searcher,
        )
