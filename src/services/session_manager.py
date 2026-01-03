"""Distributed session manager with Redis persistence."""
import asyncio
import logging
from datetime import datetime
from typing import List

from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage

from ..config.settings import Settings
from .agent_factory import AgentFactory
from .session_store import RedisSessionStore

logger = logging.getLogger(__name__)


class DistributedSessionManager:
    """Session manager with Redis backend for distributed deployment."""

    def __init__(
        self,
        redis_store: RedisSessionStore,
        agent_factory: AgentFactory,
        settings: Settings,
    ):
        """Initialize distributed session manager.

        Args:
            redis_store: Redis session store instance
            agent_factory: Agent factory for creating agents and dependencies
            settings: Application settings
        """
        self.redis_store = redis_store
        self.agent_factory = agent_factory
        self.settings = settings

        # Local cache of agent instances (per-process)
        self._agent_cache: dict[str, Agent] = {}

    async def create_session(self, user_id: str, system_prompt: str | None = None) -> dict:
        """Create new session.

        Args:
            user_id: Unique user/session identifier
            system_prompt: Optional custom system prompt (not currently used)

        Returns:
            dict with session_id and created_at

        Raises:
            ValueError: If session already exists
        """
        # Check if exists
        existing = await self.redis_store.load_session(user_id)
        if existing:
            raise ValueError(f"Session {user_id} already exists")

        # Create initial session metadata
        metadata = {
            "user_id": user_id,
            "system_prompt": system_prompt,
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "message_count": 0,
        }

        # Save to Redis with empty message history
        await self.redis_store.save_session(
            session_id=user_id, messages=[], metadata=metadata
        )

        logger.info(f"Created session: {user_id}")

        return {"session_id": user_id, "created_at": metadata["created_at"]}

    def _get_or_create_agent(self, session_id: str) -> Agent:
        """Get cached agent or create new one.

        Args:
            session_id: Session identifier for caching

        Returns:
            Agent instance
        """
        if session_id not in self._agent_cache:
            self._agent_cache[session_id] = self.agent_factory.create_agent()

        return self._agent_cache[session_id]

    async def _stream_with_status(self, agent, message, deps, messages, status_messages, interval):
        """Stream agent results with periodic status updates.

        Args:
            agent: The agent instance
            message: User message
            deps: Agent dependencies
            messages: Message history
            status_messages: List of status messages to rotate through
            interval: Seconds between status updates
        """
        status_index = 0
        last_status = asyncio.get_event_loop().time()

        # Queue to collect chunks from the agent stream
        chunk_queue = asyncio.Queue()
        stream_done = asyncio.Event()
        result_container = {}

        # Background task to run the agent stream
        async def run_stream():
            try:
                # Agent is configured with end_strategy='exhaustive' to execute all tool calls
                async with agent.run_stream(
                    message,
                    deps=deps,
                    message_history=messages
                ) as result:
                    async for chunk in result.stream_text(delta=True):
                        await chunk_queue.put({"type": "text", "content": chunk})

                # Store result for later
                result_container['result'] = result
                stream_done.set()
            except Exception as e:
                result_container['error'] = e
                stream_done.set()

        # Start the stream in background
        stream_task = asyncio.create_task(run_stream())
        logger.info(f"Started agent stream in background. Will send status every {interval}s")

        # Stream from queue with status updates
        first_chunk_received = False
        consecutive_timeouts = 0
        try:
            while not stream_done.is_set() or not chunk_queue.empty():
                current_time = asyncio.get_event_loop().time()

                # Check if we should send a status update based on consecutive timeouts
                # Send status if we've been waiting for a while (even after first chunk)
                if current_time - last_status >= interval:
                    # Only send status if we're still waiting (multiple timeouts)
                    if consecutive_timeouts >= 3:  # 3 timeouts = 0.3s of waiting
                        status_msg = status_messages[status_index % len(status_messages)]
                        logger.info(f"Sending status update after {consecutive_timeouts * 0.1:.1f}s wait: {status_msg}")
                        yield {
                            "type": "status",
                            "content": status_msg
                        }
                        status_index += 1
                        last_status = current_time

                # Try to get a chunk with short timeout
                try:
                    chunk = await asyncio.wait_for(chunk_queue.get(), timeout=0.1)

                    if not first_chunk_received:
                        logger.info("First chunk received from agent")
                        first_chunk_received = True

                    # Reset timeout counter when we get a chunk
                    consecutive_timeouts = 0
                    yield chunk

                except asyncio.TimeoutError:
                    # No chunk yet, increment timeout counter
                    consecutive_timeouts += 1
                    continue

            # Drain any remaining chunks
            while not chunk_queue.empty():
                chunk = await chunk_queue.get()
                yield chunk

            # Wait a bit for task completion
            await asyncio.sleep(0.1)

            # Check for errors
            if 'error' in result_container:
                raise result_container['error']

            # Yield a special marker with the result object
            if 'result' in result_container:
                # Yield the result so caller can extract new_messages
                yield {"type": "_result", "result": result_container['result']}
            else:
                raise RuntimeError("Stream completed but no result available")

        except Exception as e:
            logger.error(f"Error in stream_with_status: {e}")
            stream_task.cancel()
            raise
        finally:
            # Ensure task is complete
            await stream_task

    async def send_message_stream(self, session_id: str, message: str):
        """Send message and stream agent response chunks.

        Args:
            session_id: Session identifier
            message: User message text

        Yields:
            dict with type and content for each chunk

        Raises:
            ValueError: If session not found
        """
        # Load session from Redis
        session_data = await self.redis_store.load_session(session_id)

        if not session_data:
            raise ValueError(f"Session {session_id} not found")

        # Get agent
        agent = self._get_or_create_agent(session_id)

        # Get message history
        messages: List[ModelMessage] = session_data["messages"]

        # Trim if too long
        max_messages = self.settings.max_messages_per_session
        if len(messages) > max_messages:
            messages = messages[-max_messages:]

        # Get dependencies
        deps = self.agent_factory.create_dependencies()

        # Status messages for long-running operations
        status_messages = [
            "Still searching for information...",
            "This is taking a bit longer than expected, please wait...",
            "Almost there, still processing...",
            "Thank you for your patience, still working on it...",
        ]

        # Stream results with status updates (3 second interval for testing)
        result_obj = None
        try:
            # Yield all chunks and extract result
            async for chunk in self._stream_with_status(
                agent, message, deps, messages, status_messages, interval=3.0
            ):
                if chunk.get("type") == "_result":
                    # Internal marker - extract result object
                    result_obj = chunk.get("result")
                else:
                    # Normal chunk - yield to client
                    yield chunk

        except Exception as e:
            logger.error(f"Error in stream: {e}")
            raise

        # Update messages with new messages from result
        if result_obj:
            messages.extend(result_obj.new_messages())
        else:
            logger.warning("No result object received from stream")

        # Update metadata
        session_data["metadata"]["last_activity"] = datetime.now().isoformat()
        session_data["metadata"]["message_count"] = len(messages)

        # Yield completion signal
        yield {"type": "done", "message_count": len(messages)}

        # Save back to Redis
        await self.redis_store.save_session(
            session_id=session_id, messages=messages, metadata=session_data["metadata"]
        )

        # Touch TTL
        await self.redis_store.touch_session(session_id)

        logger.info(f"Streamed message for session: {session_id}")

        # Send completion signal
        yield {"type": "done", "message_count": len(messages)}

    async def send_message(self, session_id: str, message: str) -> dict:
        """Send message and get agent response.

        Args:
            session_id: Session identifier
            message: User message text

        Returns:
            dict with session_id, response, and message_count

        Raises:
            ValueError: If session not found
        """
        # Load session from Redis
        session_data = await self.redis_store.load_session(session_id)

        if not session_data:
            raise ValueError(f"Session {session_id} not found")

        # Get agent
        agent = self._get_or_create_agent(session_id)

        # Get message history
        messages: List[ModelMessage] = session_data["messages"]

        # Trim if too long (prevent memory issues)
        max_messages = self.settings.max_messages_per_session
        if len(messages) > max_messages:
            messages = messages[-max_messages:]
            logger.info(
                f"Trimmed message history for session {session_id} to {max_messages}"
            )

        # Get dependencies
        deps = self.agent_factory.create_dependencies()

        # Run agent
        result = await agent.run(message, deps=deps, message_history=messages)

        # Update message history with new messages
        messages.extend(result.new_messages())

        # Update metadata
        session_data["metadata"]["last_activity"] = datetime.now().isoformat()
        session_data["metadata"]["message_count"] = len(messages)

        # Save back to Redis
        await self.redis_store.save_session(
            session_id=session_id, messages=messages, metadata=session_data["metadata"]
        )

        # Touch TTL
        await self.redis_store.touch_session(session_id)

        logger.info(f"Processed message for session: {session_id}")

        return {
            "session_id": session_id,
            "response": result.output,
            "message_count": len(messages),
        }

    async def get_session_info(self, session_id: str) -> dict:
        """Get session information.

        Args:
            session_id: Session identifier

        Returns:
            dict with session metadata

        Raises:
            ValueError: If session not found
        """
        session_data = await self.redis_store.load_session(session_id)

        if not session_data:
            raise ValueError(f"Session {session_id} not found")

        return {
            "session_id": session_id,
            **session_data["metadata"],
            "message_count": len(session_data["messages"]),
        }

    async def delete_session(self, session_id: str):
        """Delete session.

        Args:
            session_id: Session identifier
        """
        await self.redis_store.delete_session(session_id)

        # Remove from cache
        if session_id in self._agent_cache:
            del self._agent_cache[session_id]

        logger.info(f"Deleted session: {session_id}")

    async def list_sessions(self) -> List[str]:
        """List all active sessions.

        Returns:
            List of session ID strings
        """
        return await self.redis_store.get_all_session_ids()
