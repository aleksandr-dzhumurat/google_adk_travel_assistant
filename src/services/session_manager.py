"""Distributed session manager with Redis persistence."""
import logging
from datetime import datetime
from typing import List, Tuple

from pydantic_ai.messages import ModelMessage

from ..config.settings import Settings
from .agent_factory import AgentFactory
from .agent_service import AgentService
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
        """Initialize distributed session manager."""
        self.redis_store = redis_store
        self.settings = settings
        self.agent_service = AgentService(agent_factory, settings)

    async def create_session(self, user_id: str, system_prompt: str | None = None) -> dict:
        """Create new session."""
        existing = await self.redis_store.load_session(user_id)
        if existing:
            raise ValueError(f"Session {user_id} already exists")
        metadata = {
            "user_id": user_id,
            "system_prompt": system_prompt,
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "message_count": 0,
        }
        await self.redis_store.save_session(
            session_id=user_id, messages=[], metadata=metadata
        )
        logger.info(f"Created session: {user_id}")
        return {"session_id": user_id, "created_at": metadata["created_at"]}

    async def _load_and_prepare_session(
        self, session_id: str
    ) -> Tuple[dict, List[ModelMessage]]:
        """Load session and prepare message history."""
        session_data = await self.redis_store.load_session(session_id)
        if not session_data:
            raise ValueError(f"Session {session_id} not found")
        messages: List[ModelMessage] = session_data["messages"]
        max_messages = self.settings.max_messages_per_session
        if len(messages) > max_messages:
            messages = messages[-max_messages:]
        return session_data, messages

    async def _update_and_save_session(
        self, session_id: str, session_data: dict, messages: List[ModelMessage]
    ):
        """Update session metadata and save to Redis."""
        session_data["metadata"]["last_activity"] = datetime.now().isoformat()
        session_data["metadata"]["message_count"] = len(messages)
        await self.redis_store.save_session(
            session_id=session_id, messages=messages, metadata=session_data["metadata"]
        )
        await self.redis_store.touch_session(session_id)

    async def send_message_stream(self, session_id: str, message: str):
        """Send message and stream agent response chunks."""
        session_data, messages = await self._load_and_prepare_session(session_id)
        result_obj = None
        try:
            async for chunk in self.agent_service.run_agent_stream(
                session_id, message, messages
            ):
                if chunk.get("type") == "_result":
                    result_obj = chunk.get("result")
                else:
                    yield chunk
        except Exception as e:
            logger.error(f"Error in stream: {e}")
            raise
        if result_obj:
            messages.extend(result_obj.new_messages())
        else:
            logger.warning("No result object received from stream")
        yield {"type": "done", "message_count": len(messages)}
        await self._update_and_save_session(session_id, session_data, messages)
        logger.info(f"Streamed message for session: {session_id}")

    async def send_message(self, session_id: str, message: str) -> dict:
        """Send message and get agent response."""
        session_data, messages = await self._load_and_prepare_session(session_id)
        result = await self.agent_service.run_agent(session_id, message, messages)
        messages.extend(result.new_messages())
        await self._update_and_save_session(session_id, session_data, messages)
        logger.info(f"Processed message for session: {session_id}")
        return {
            "session_id": session_id,
            "response": result.output,
            "message_count": len(messages),
        }

    async def get_session_info(self, session_id: str) -> dict:
        """Get session information."""
        session_data = await self.redis_store.load_session(session_id)
        if not session_data:
            raise ValueError(f"Session {session_id} not found")
        return {
            "session_id": session_id,
            **session_data["metadata"],
            "message_count": len(session_data["messages"]),
        }

    async def delete_session(self, session_id: str):
        """Delete session."""
        await self.redis_store.delete_session(session_id)
        logger.info(f"Deleted session: {session_id}")

    async def list_sessions(self) -> List[str]:
        """List all active sessions."""
        return await self.redis_store.get_all_session_ids()
