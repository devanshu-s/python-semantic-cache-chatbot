from fastapi import APIRouter
from typing import List
from backend.models.cache_models import CacheStats, CacheEntry
from backend.services.semantic_cache_service import semantic_cache_service

router = APIRouter(prefix="/api/cache", tags=["Cache Management"])

@router.get("/stats", response_model=CacheStats)
async def get_cache_statistics() -> CacheStats:
    """Get FAISS vector index & cache metadata stats."""
    return semantic_cache_service.get_stats()

@router.get("/entries", response_model=List[CacheEntry])
async def list_cached_entries() -> List[CacheEntry]:
    """Get all cached query-response pairs."""
    return semantic_cache_service.get_all_entries()

@router.post("/clear")
async def clear_semantic_cache():
    """Reset FAISS index and clear all cached entries."""
    semantic_cache_service.clear_cache()
    return {"message": "Semantic cache successfully cleared."}
