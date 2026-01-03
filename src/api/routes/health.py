"""Health check and metrics endpoints."""
from fastapi import APIRouter, Depends

from ..dependencies import get_redis_store, get_session_manager
from ...services.session_manager import DistributedSessionManager
from ...services.session_store import RedisSessionStore

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Basic health check endpoint.

    Returns:
        dict with status
    """
    return {"status": "healthy"}


@router.get("/health/detailed")
async def detailed_health_check(
    redis_store: RedisSessionStore = Depends(get_redis_store),
):
    """Detailed health check with dependency status.

    Args:
        redis_store: Redis store dependency

    Returns:
        dict with status and service health
    """
    redis_healthy = await redis_store.health_check()

    return {
        "status": "healthy" if redis_healthy else "degraded",
        "redis": "connected" if redis_healthy else "disconnected",
    }


@router.get("/metrics")
async def metrics(
    manager: DistributedSessionManager = Depends(get_session_manager),
):
    """Get system metrics.

    Args:
        manager: Session manager dependency

    Returns:
        dict with system metrics
    """
    sessions = await manager.list_sessions()

    return {
        "active_sessions": len(sessions),
        "max_sessions": manager.settings.max_sessions,
    }
