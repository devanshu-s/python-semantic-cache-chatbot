from typing import List
from backend.config.constants import PYTHON_GUARDRAIL_SYSTEM_PROMPT
from backend.models.chat_models import ChatMessage

class PromptService:
    @staticmethod
    def build_prompt(query: str, history: List[ChatMessage]) -> str:
        """
        Build full prompt containing system instructions, conversation history, and current user query.
        """
        prompt_parts = [PYTHON_GUARDRAIL_SYSTEM_PROMPT]
        
        if history:
            prompt_parts.append("\n--- Conversation History ---")
            for msg in history:
                role = "User" if msg.role == "user" else "Assistant"
                prompt_parts.append(f"{role}: {msg.content}")
        
        prompt_parts.append("\n--- Current Query ---")
        prompt_parts.append(f"User: {query}")
        prompt_parts.append("Assistant:")
        
        return "\n".join(prompt_parts)

prompt_service = PromptService()
