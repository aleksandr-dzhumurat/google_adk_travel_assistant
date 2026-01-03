"""FastAPI application for multi-user event discovery system."""
import logging
from contextlib import asynccontextmanager
from datetime import timedelta

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..config.settings import settings
from ..services.agent_factory import AgentFactory
from ..services.session_manager import DistributedSessionManager
from ..services.session_store import RedisSessionStore
from .dependencies import app_state
from .routes import health, messages, sessions

# Setup logging
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan for startup and shutdown.

    Args:
        app: FastAPI application instance

    Yields:
        None
    """
    # Startup
    logger.info("Starting FastAPI application...")

    # Create Redis store
    redis_store = RedisSessionStore(
        redis_url=settings.redis_url,
        session_ttl=timedelta(hours=settings.session_ttl_hours),
    )

    # Health check Redis
    if not await redis_store.health_check():
        raise RuntimeError("Redis connection failed")

    logger.info("Redis connection established")

    # Create agent factory
    agent_factory = AgentFactory(settings)

    # Create session manager
    session_manager = DistributedSessionManager(
        redis_store=redis_store,
        agent_factory=agent_factory,
        settings=settings,
    )

    # Store in app state
    app_state["session_manager"] = session_manager
    app_state["redis_store"] = redis_store

    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Shutting down application...")

    # Cleanup Redis
    await redis_store.close()

    logger.info("Application shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Event Discovery Multi-User API",
    description="FastAPI + Redis + pydantic-ai multi-user agent system",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api/v1")
app.include_router(sessions.router, prefix="/api/v1")
app.include_router(messages.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint.

    Returns:
        dict with service info
    """
    return {
        "service": "Event Discovery API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }
