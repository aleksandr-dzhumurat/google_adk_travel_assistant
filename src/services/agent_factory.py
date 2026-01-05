"""Factory for creating agent instances with dependencies."""
from concurrent.futures import ThreadPoolExecutor

from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel

from ..agent.perplexity import EventSearcher
from ..agent.pydantic_agent import AgentDependencies, get_tools
from ..config.settings import Settings


class AgentFactory:
    """Factory for creating agent instances with dependency injection."""

    def __init__(self, settings: Settings, executor: ThreadPoolExecutor):
        """Initialize agent factory.

        Args:
            settings: Application settings instance
            executor: ThreadPoolExecutor for running sync operations
        """
        self.settings = settings
        self.event_searcher = EventSearcher(api_key=settings.perplexity_api_key)
        self.executor = executor
        with open("src/agent/system_prompt.txt", "r") as f:
            self.system_prompt = f.read()

    def create_agent(self) -> Agent:
        """Create agent instance.

        The event_agent is a module-level singleton shared across all sessions.
        Each session uses the same agent but with different message history.

        Returns:
            Agent instance
        """
        return Agent(
            model=GeminiModel(self.settings.gemini_model),
            deps_type=AgentDependencies,
            system_prompt=self.system_prompt,
            tools=get_tools(self.executor),
            retries=2,
            end_strategy="exhaustive",  # Execute ALL tool calls, don't stop early
        )

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
