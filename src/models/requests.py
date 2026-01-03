"""Request models for API endpoints."""
from typing import Optional
from pydantic import BaseModel, Field


class CreateSessionRequest(BaseModel):
    """Request to create a new session."""

    user_id: Optional[str] = Field(default=None, description="Optional user ID")
    system_prompt: Optional[str] = Field(
        default=None, description="Optional custom system prompt"
    )


class SendMessageRequest(BaseModel):
    """Request to send a message to an agent."""

    message: str = Field(..., min_length=1, max_length=4000, description="User message")
