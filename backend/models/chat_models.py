from pydantic import BaseModel, Field
from typing import List, Optional

class ChatMessage(BaseModel):
    role: str = Field(..., description="'user' or 'assistant'")
    content: str = Field(..., description="Message text")

class ChatRequest(BaseModel):
    query: str = Field(..., description="User question or query text")
    history: List[ChatMessage] = Field(default_factory=list, description="Previous conversation turn history")
    similarity_threshold: Optional[float] = Field(default=None, description="Custom similarity threshold for cache search")

class ChatResponse(BaseModel):
    query: str
    response: str
    is_cached: bool
    similarity_score: float
    total_latency_ms: float
    gemini_latency_ms: float
    cache_latency_ms: float
    source: str  # 'cache' or 'gemini'
    timestamp: str
