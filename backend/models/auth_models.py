from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class UserProfile(BaseModel):
    uid: str
    email: str
    display_name: str
    photo_url: Optional[str] = None

class SessionMessageItem(BaseModel):
    role: str
    content: str
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None

class ChatSessionSummary(BaseModel):
    id: str
    user_id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int = 0

class CreateSessionRequest(BaseModel):
    user_id: str
    title: Optional[str] = "New Conversation"
    initial_messages: Optional[List[SessionMessageItem]] = []

class AppendMessageRequest(BaseModel):
    role: str
    content: str
    metadata: Optional[Dict[str, Any]] = None

class UpdateSessionTitleRequest(BaseModel):
    title: str
