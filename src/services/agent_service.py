"""Service for interacting with the pydantic-ai agent."""
import asyncio
import logging
from typing import List

from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage

from ..config.settings import Settings
from .agent_factory import AgentFactory

logger = logging.getLogger(__name__)


class AgentService:
    """Service for agent-related operations."""

    def __init__(self, agent_factory: AgentFactory, settings: Settings):
        """Initialize the agent service.

        Args:
            agent_factory: The agent factory.
            settings: The application settings.
        """
        self.agent_factory = agent_factory
        self.settings = settings
        self._agent_cache: dict[str, Agent] = {}

    def _get_or_create_agent(self, session_id: str) -> Agent:
        """Get a cached agent or create a new one.

        Args:
            session_id: The session ID.

        Returns:
            The agent instance.
        """
        if session_id not in self._agent_cache:
            self._agent_cache[session_id] = self.agent_factory.create_agent()
        return self._agent_cache[session_id]

    async def run_agent(self, session_id: str, message: str, messages: List[ModelMessage]) -> dict:
        """Run the agent with the given message and message history.

        Args:
            session_id: The session ID.
            message: The user message.
            messages: The message history.

        Returns:
            The agent result.
        """
        agent = self._get_or_create_agent(session_id)
        deps = self.agent_factory.create_dependencies()
        result = await agent.run(message, deps=deps, message_history=messages)
        return result

    async def run_agent_stream(self, session_id: str, message: str, messages: List[ModelMessage]):
        """Run the agent with streaming.

        Args:
            session_id: The session ID.
            message: The user message.
            messages: The message history.

        Yields:
            Chunks of the agent's response.
        """
        agent = self._get_or_create_agent(session_id)
        deps = self.agent_factory.create_dependencies()
        status_messages = [
            "Still searching for information...",
            "This is taking a bit longer than expected, please wait...",
            "Almost there, still processing...",
            "Thank you for your patience, still working on it...",
        ]

        result_obj = None
        try:
            async for chunk in self._stream_with_status(
                agent, message, deps, messages, status_messages, interval=3.0
            ):
                if chunk.get("type") == "_result":
                    result_obj = chunk.get("result")
                else:
                    yield chunk

        except Exception as e:
            logger.error(f"Error in stream: {e}")
            raise

        if result_obj:
            yield {"type": "_result", "result": result_obj}
        else:
            logger.warning("No result object received from stream")

    async def _stream_with_status(self, agent, message, deps, messages, status_messages, interval):
        """Stream agent results with periodic status updates."""
        status_index = 0
        last_status = asyncio.get_event_loop().time()
        chunk_queue = asyncio.Queue()
        stream_done = asyncio.Event()
        result_container = {}

        async def run_stream():
            try:
                async with agent.run_stream(
                    message, deps=deps, message_history=messages
                ) as result:
                    async for chunk in result.stream_text(delta=True):
                        await chunk_queue.put({"type": "text", "content": chunk})
                result_container["result"] = result
                stream_done.set()
            except Exception as e:
                result_container["error"] = e
                stream_done.set()

        stream_task = asyncio.create_task(run_stream())
        logger.info(f"Started agent stream in background. Will send status every {interval}s")

        first_chunk_received = False
        consecutive_timeouts = 0
        try:
            while not stream_done.is_set() or not chunk_queue.empty():
                current_time = asyncio.get_event_loop().time()
                if current_time - last_status >= interval:
                    if consecutive_timeouts >= 3:
                        status_msg = status_messages[status_index % len(status_messages)]
                        logger.info(f"Sending status update after {consecutive_timeouts * 0.1:.1f}s wait: {status_msg}")
                        yield {"type": "status", "content": status_msg}
                        status_index += 1
                        last_status = current_time
                try:
                    chunk = await asyncio.wait_for(chunk_queue.get(), timeout=0.1)
                    if not first_chunk_received:
                        logger.info("First chunk received from agent")
                        first_chunk_received = True
                    consecutive_timeouts = 0
                    yield chunk
                except asyncio.TimeoutError:
                    consecutive_timeouts += 1
                    continue
            while not chunk_queue.empty():
                chunk = await chunk_queue.get()
                yield chunk
            await asyncio.sleep(0.1)
            if "error" in result_container:
                raise result_container["error"]
            if "result" in result_container:
                yield {"type": "_result", "result": result_container["result"]}
            else:
                raise RuntimeError("Stream completed but no result available")
        except Exception as e:
            logger.error(f"Error in stream_with_status: {e}")
            stream_task.cancel()
            raise
        finally:
            await stream_task
