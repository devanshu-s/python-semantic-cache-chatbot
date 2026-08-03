import time
from fastapi import APIRouter, HTTPException, status
from backend.config.settings import settings
from backend.models.chat_models import ChatRequest, ChatResponse
from backend.services.semantic_cache_service import semantic_cache_service
from backend.services.chatbot_service import chatbot_service
from backend.services.metrics_service import metrics_service
from backend.utils.helpers import get_current_timestamp
from backend.utils.logger import logger

router = APIRouter(prefix="/api/chat", tags=["Chat"])

@router.post("", response_model=ChatResponse)
async def process_chat_message(request: ChatRequest) -> ChatResponse:
    """
    Process incoming user query in a conversational flow:
    1. Search semantic cache using direct query embedding and backend threshold (settings.SIMILARITY_THRESHOLD).
    2. If similarity exceeds threshold -> return cached response immediately (CACHE HIT).
    3. Else -> query Google Gemini API with conversational history, store in cache, return result (CACHE MISS).
    """
    query = request.query.strip()
    if not query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query string cannot be empty."
        )

    start_total_time = time.perf_counter()

    # Use backend-configured similarity threshold if not explicitly overridden
    effective_threshold = (
        request.similarity_threshold
        if request.similarity_threshold is not None
        else settings.SIMILARITY_THRESHOLD
    )

    # 1. Search Semantic Cache on direct query embedding
    search_result, query_vector = semantic_cache_service.search_cache(
        query=query,
        threshold=effective_threshold
    )

    if search_result.is_hit and search_result.cached_entry:
        total_latency = (time.perf_counter() - start_total_time) * 1000.0
        cache_entry = search_result.cached_entry

        metrics_service.record_query(
            is_hit=True,
            total_latency=total_latency,
            gemini_latency=0.0,
            cache_latency=search_result.latency_ms
        )

        return ChatResponse(
            query=query,
            response=cache_entry.response,
            is_cached=True,
            similarity_score=round(search_result.similarity_score, 4),
            total_latency_ms=round(total_latency, 2),
            gemini_latency_ms=0.0,
            cache_latency_ms=round(search_result.latency_ms, 2),
            source="cache",
            timestamp=get_current_timestamp()
        )

    # 2. Cache Miss -> Invoke Gemini Chatbot Service with full history
    gemini_response_text, gemini_latency = chatbot_service.generate_response(
        query=query,
        history=request.history
    )

    # 3. Save Q&A pair into Semantic Cache
    semantic_cache_service.add_to_cache(
        query=query,
        response=gemini_response_text,
        vector=query_vector
    )

    total_latency = (time.perf_counter() - start_total_time) * 1000.0

    metrics_service.record_query(
        is_hit=False,
        total_latency=total_latency,
        gemini_latency=gemini_latency,
        cache_latency=search_result.latency_ms
    )

    return ChatResponse(
        query=query,
        response=gemini_response_text,
        is_cached=False,
        similarity_score=round(search_result.similarity_score, 4),
        total_latency_ms=round(total_latency, 2),
        gemini_latency_ms=round(gemini_latency, 2),
        cache_latency_ms=round(search_result.latency_ms, 2),
        source="gemini",
        timestamp=get_current_timestamp()
    )
