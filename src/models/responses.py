"""Response models for API endpoints."""
from pydantic import BaseModel


class SessionResponse(BaseModel):
    """Response when creating a session."""

    session_id: str
    created_at: str


class SessionInfoResponse(BaseModel):
    """Detailed session information."""

    session_id: str
    user_id: str
    created_at: str
    last_activity: str
    message_count: int


class MessageResponse(BaseModel):
    """Response when sending a message."""

    session_id: str
    response: str
    message_count: int
