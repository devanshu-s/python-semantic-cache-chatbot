import time
from typing import List, Tuple
from backend.config.settings import settings
from backend.config.constants import PYTHON_GUARDRAIL_SYSTEM_PROMPT
from backend.models.chat_models import ChatMessage
from backend.utils.logger import logger

class ChatbotService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL

    def generate_response(self, query: str, history: List[ChatMessage]) -> Tuple[str, float]:
        """
        Send prompt context to Google Gemini API and measure response latency (in ms).
        Returns (response_text, latency_ms).
        """
        start_time = time.perf_counter()

        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            error_msg = (
                "⚠️ **Gemini API Key Required**: Please configure a valid `GEMINI_API_KEY` (starting with `AIzaSy...`) in your `.env` file from https://aistudio.google.com/app/apikey."
            )
            return error_msg, latency_ms

        try:
            # Primary: google-genai SDK
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)
            
            contents = []
            for msg in history:
                role = "user" if msg.role == "user" else "model"
                contents.append(
                    types.Content(
                        role=role,
                        parts=[types.Part.from_text(text=msg.content)]
                    )
                )
            contents.append(
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=query)]
                )
            )

            config = types.GenerateContentConfig(
                system_instruction=PYTHON_GUARDRAIL_SYSTEM_PROMPT,
                temperature=0.7,
            )

            response = client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config
            )
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            return response.text.strip(), latency_ms

        except Exception as e1:
            error_str = str(e1)
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            logger.error(f"Gemini API generation error: {error_str}")

            if "RESOURCE_EXHAUSTED" in error_str or "429" in error_str or "quota" in error_str.lower():
                return (
                    "⚠️ **Gemini API Quota Exceeded (429)**: Your current Gemini API key has 0 remaining free requests or has exceeded its rate limit.\n\n"
                    "**Fix**: Create a fresh, free API key at **[https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)** and paste it into `.env` as `GEMINI_API_KEY=AIzaSy...`."
                ), latency_ms

            if "NOT_FOUND" in error_str or "404" in error_str:
                return (
                    f"⚠️ **Model Not Found (404)**: The model `{self.model_name}` was not found or is unavailable for this key.\n\n"
                    "**Fix**: Ensure `GEMINI_MODEL=gemini-2.0-flash` is set in `.env`."
                ), latency_ms

            return f"❌ **Gemini API Error**: {error_str}", latency_ms

chatbot_service = ChatbotService()
