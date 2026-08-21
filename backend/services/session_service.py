import os
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from backend.models.auth_models import (
    UserProfile,
    ChatSessionSummary,
    SessionMessageItem,
    CreateSessionRequest
)
from backend.utils.logger import logger

class SessionService:
    def __init__(self):
        self.local_store_path = "backend/database/user_sessions.json"
        self._ensure_local_store()

    def _ensure_local_store(self):
        os.makedirs(os.path.dirname(self.local_store_path), exist_ok=True)
        if not os.path.exists(self.local_store_path):
            with open(self.local_store_path, "w", encoding="utf-8") as f:
                json.dump({}, f)

    def _load_local_data(self) -> Dict[str, Any]:
        self._ensure_local_store()
        try:
            with open(self.local_store_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_local_data(self, data: Dict[str, Any]):
        self._ensure_local_store()
        with open(self.local_store_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def list_sessions(self, user_id: str = "local_user") -> List[ChatSessionSummary]:
        """List all chat sessions stored locally, ordered newest first."""
        data = self._load_local_data()
        user_chats = data.get(user_id, {})
        sessions = []
        for sid, sdata in user_chats.items():
            sessions.append(ChatSessionSummary(
                id=sid,
                user_id=user_id,
                title=sdata.get("title", "Conversation"),
                created_at=sdata.get("created_at", ""),
                updated_at=sdata.get("updated_at", ""),
                message_count=len(sdata.get("messages", []))
            ))
        sessions.sort(key=lambda x: x.updated_at, reverse=True)
        return sessions

    def create_session(self, req: CreateSessionRequest) -> ChatSessionSummary:
        """Create a new local chat session."""
        session_id = f"chat_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow().isoformat()
        msgs = []
        if req.initial_messages:
            for m in req.initial_messages:
                msgs.append({
                    "role": m.role,
                    "content": m.content,
                    "timestamp": m.timestamp or now,
                    "metadata": m.metadata or {}
                })

        data = self._load_local_data()
        uid = req.user_id or "local_user"
        if uid not in data:
            data[uid] = {}

        data[uid][session_id] = {
            "title": req.title or "New Conversation",
            "created_at": now,
            "updated_at": now,
            "messages": msgs
        }
        self._save_local_data(data)
        logger.info(f"Created local session {session_id} for user {uid}")

        return ChatSessionSummary(
            id=session_id,
            user_id=uid,
            title=req.title or "New Conversation",
            created_at=now,
            updated_at=now,
            message_count=len(msgs)
        )

    def get_session_messages(self, user_id: str, session_id: str) -> List[SessionMessageItem]:
        """Retrieve all messages for a specific local chat session."""
        data = self._load_local_data()
        user_chats = data.get(user_id, {})
        sess = user_chats.get(session_id)
        if not sess:
            return []

        return [
            SessionMessageItem(
                role=m.get("role", "user"),
                content=m.get("content", ""),
                timestamp=m.get("timestamp", ""),
                metadata=m.get("metadata", {})
            )
            for m in sess.get("messages", [])
        ]

    def append_message(self, user_id: str, session_id: str, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Append a message to a local session."""
        now = datetime.utcnow().isoformat()
        data = self._load_local_data()
        uid = user_id or "local_user"
        if uid not in data:
            data[uid] = {}

        if session_id not in data[uid]:
            # Auto-create session
            display_title = content[:35] + "..." if len(content) > 35 else content
            data[uid][session_id] = {
                "title": display_title or "Conversation",
                "created_at": now,
                "updated_at": now,
                "messages": []
            }

        sess = data[uid][session_id]
        sess["messages"].append({
            "role": role,
            "content": content,
            "timestamp": now,
            "metadata": metadata or {}
        })
        sess["updated_at"] = now
        
        # Auto-update title from first user message if default
        if sess.get("title") in ["New Conversation", "Conversation", ""] and role == "user":
            sess["title"] = content[:35] + "..." if len(content) > 35 else content

        self._save_local_data(data)
        return True

    def delete_session(self, user_id: str, session_id: str) -> bool:
        """Delete a chat session from local storage."""
        data = self._load_local_data()
        uid = user_id or "local_user"
        if uid in data and session_id in data[uid]:
            del data[uid][session_id]
            self._save_local_data(data)
            logger.info(f"Deleted local session {session_id} for user {uid}")
            return True
        return False


session_service = SessionService()
