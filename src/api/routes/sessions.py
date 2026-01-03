"""Session management endpoints."""
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException

from ...models.requests import CreateSessionRequest
from ...models.responses import SessionInfoResponse, SessionResponse
from ...services.session_manager import DistributedSessionManager
from ..dependencies import get_session_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionResponse)
async def create_session(
    request: CreateSessionRequest,
    manager: DistributedSessionManager = Depends(get_session_manager),
):
    """Create a new session.

    Args:
        request: Session creation request
        manager: Session manager dependency

    Returns:
        SessionResponse with session_id and created_at

    Raises:
        HTTPException: 400 if session exists, 500 on error
    """
    try:
        # Generate user_id if not provided
        user_id = request.user_id or str(uuid.uuid4())

        session_data = await manager.create_session(
            user_id=user_id,
            system_prompt=request.system_prompt,
        )
        return SessionResponse(**session_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{session_id}", response_model=SessionInfoResponse)
async def get_session(
    session_id: str,
    manager: DistributedSessionManager = Depends(get_session_manager),
):
    """Get session information.

    Args:
        session_id: Session identifier
        manager: Session manager dependency

    Returns:
        SessionInfoResponse with session details

    Raises:
        HTTPException: 404 if not found, 500 on error
    """
    try:
        session_info = await manager.get_session_info(session_id)
        return SessionInfoResponse(**session_info)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting session: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    manager: DistributedSessionManager = Depends(get_session_manager),
):
    """Delete a session.

    Args:
        session_id: Session identifier
        manager: Session manager dependency

    Returns:
        dict with success message

    Raises:
        HTTPException: 500 on error
    """
    try:
        await manager.delete_session(session_id)
        return {"message": "Session deleted"}
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("", response_model=list[str])
async def list_sessions(
    manager: DistributedSessionManager = Depends(get_session_manager),
):
    """List all active sessions.

    Args:
        manager: Session manager dependency

    Returns:
        List of session ID strings

    Raises:
        HTTPException: 500 on error
    """
    try:
        sessions = await manager.list_sessions()
        return sessions
    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
