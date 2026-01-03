"""Redis-based session storage."""
import pickle
from datetime import datetime, timedelta
from typing import List, Optional

import redis.asyncio as redis
from pydantic_ai.messages import ModelMessage


class RedisSessionStore:
    """Redis-backed session storage with TTL expiration."""

    def __init__(self, redis_url: str, session_ttl: timedelta = timedelta(hours=24)):
        """Initialize Redis session store.

        Args:
            redis_url: Redis connection URL
            session_ttl: Session time-to-live duration
        """
        self.redis_client = redis.from_url(
            redis_url, decode_responses=False, encoding="utf-8"
        )
        self.session_ttl = session_ttl

    async def save_session(
        self, session_id: str, messages: List[ModelMessage], metadata: dict
    ):
        """Save session with message history and metadata.

        Args:
            session_id: Unique session identifier
            messages: List of ModelMessage objects
            metadata: Session metadata dict
        """
        # Pickle messages directly (pydantic-ai messages are not standard Pydantic models)
        session_data = {
            "session_id": session_id,
            "messages": messages,  # Store ModelMessage objects directly
            "metadata": metadata,
            "updated_at": datetime.now().isoformat(),
        }

        # Use pickle for serialization
        serialized = pickle.dumps(session_data)

        # Save with TTL
        await self.redis_client.setex(
            f"session:{session_id}", self.session_ttl, serialized
        )

    async def load_session(self, session_id: str) -> Optional[dict]:
        """Load session from Redis.

        Args:
            session_id: Unique session identifier

        Returns:
            Session data dict with messages, or None if not found
        """
        data = await self.redis_client.get(f"session:{session_id}")

        if not data:
            return None

        # Unpickle session data (messages are already ModelMessage objects)
        session_data = pickle.loads(data)

        return session_data

    async def delete_session(self, session_id: str):
        """Delete session from Redis.

        Args:
            session_id: Unique session identifier
        """
        await self.redis_client.delete(f"session:{session_id}")

    async def touch_session(self, session_id: str):
        """Refresh session TTL.

        Args:
            session_id: Unique session identifier
        """
        await self.redis_client.expire(f"session:{session_id}", self.session_ttl)

    async def get_all_session_ids(self) -> List[str]:
        """Get all active session IDs.

        Returns:
            List of session ID strings
        """
        keys = await self.redis_client.keys("session:*")
        return [key.decode("utf-8").replace("session:", "") for key in keys]

    async def health_check(self) -> bool:
        """Check Redis connection health.

        Returns:
            True if Redis is reachable, False otherwise
        """
        try:
            await self.redis_client.ping()
            return True
        except Exception:
            return False

    async def close(self):
        """Close Redis connection."""
        await self.redis_client.close()
