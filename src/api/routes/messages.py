"""Message/chat endpoints."""
import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from ...models.requests import SendMessageRequest
from ...models.responses import MessageResponse
from ...services.session_manager import DistributedSessionManager
from ..dependencies import get_session_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sessions", tags=["messages"])


@router.post("/{session_id}/messages/stream")
async def send_message_stream(
    session_id: str,
    request: SendMessageRequest,
    manager: DistributedSessionManager = Depends(get_session_manager),
):
    """Send a message and get streaming agent response.

    Args:
        session_id: Session identifier
        request: Message request with user message
        manager: Session manager dependency

    Returns:
        StreamingResponse with agent response chunks

    Raises:
        HTTPException: 404 if session not found, 500 on error
    """
    async def generate():
        try:
            # Send immediate acknowledgment
            yield f"data: {json.dumps({'type': 'status', 'content': 'Processing your request...'})}\n\n"

            # Stream the agent response
            async for chunk in manager.send_message_stream(session_id, request.message):
                yield f"data: {json.dumps(chunk)}\n\n"

            yield "data: [DONE]\n\n"
        except ValueError as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            yield f"data: {json.dumps({'type': 'error', 'content': 'Internal server error'})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/{session_id}/messages", response_model=MessageResponse)
async def send_message(
    session_id: str,
    request: SendMessageRequest,
    manager: DistributedSessionManager = Depends(get_session_manager),
):
    """Send a message and get agent response (non-streaming).

    Args:
        session_id: Session identifier
        request: Message request with user message
        manager: Session manager dependency

    Returns:
        MessageResponse with agent response

    Raises:
        HTTPException: 404 if session not found, 500 on error
    """
    try:
        response_data = await manager.send_message(
            session_id=session_id,
            message=request.message,
        )
        return MessageResponse(**response_data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
