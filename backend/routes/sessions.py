from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from backend.models.auth_models import (
    ChatSessionSummary,
    SessionMessageItem,
    CreateSessionRequest,
    AppendMessageRequest,
    UpdateSessionTitleRequest
)
from backend.services.session_service import session_service

router = APIRouter(prefix="/api/sessions", tags=["Local Sessions"])

@router.get("/list", response_model=List[ChatSessionSummary])
async def list_user_sessions(user_id: str = Query("default_user", description="User ID")):
    """List all saved chat sessions stored locally."""
    try:
        return session_service.list_sessions(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create", response_model=ChatSessionSummary)
async def create_chat_session(payload: CreateSessionRequest):
    """Create a new local chat session."""
    try:
        return session_service.create_session(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{session_id}", response_model=List[SessionMessageItem])
async def get_session_messages(session_id: str, user_id: str = Query("default_user")):
    """Get all messages for a specific session."""
    try:
        return session_service.get_session_messages(user_id, session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{session_id}/message")
async def append_message_to_session(
    session_id: str,
    payload: AppendMessageRequest,
    user_id: str = Query("local_user")
):
    """Append a new message to a session."""
    try:
        success = session_service.append_message(
            user_id=user_id,
            session_id=session_id,
            role=payload.role,
            content=payload.content,
            metadata=payload.metadata
        )
        if not success:
            raise HTTPException(status_code=404, detail="Session not found.")
        return {"status": "success", "session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{session_id}")
async def delete_chat_session(session_id: str, user_id: str = Query("default_user")):
    """Delete a chat session."""
    try:
        success = session_service.delete_session(user_id, session_id)
        return {"status": "deleted" if success else "not_found", "session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
