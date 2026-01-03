"""FastAPI dependencies for dependency injection."""
from fastapi import HTTPException

# Global state container (populated at startup)
app_state = {"session_manager": None, "redis_store": None}


def get_session_manager():
    """Get session manager from app state.

    Returns:
        DistributedSessionManager instance

    Raises:
        HTTPException: If service unavailable
    """
    manager = app_state.get("session_manager")
    if not manager:
        raise HTTPException(status_code=503, detail="Service unavailable")
    return manager


def get_redis_store():
    """Get Redis store from app state.

    Returns:
        RedisSessionStore instance

    Raises:
        HTTPException: If service unavailable
    """
    store = app_state.get("redis_store")
    if not store:
        raise HTTPException(status_code=503, detail="Service unavailable")
    return store
