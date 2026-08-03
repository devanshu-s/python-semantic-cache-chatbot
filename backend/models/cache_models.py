from pydantic import BaseModel, Field
from typing import List, Optional

class CacheEntry(BaseModel):
    id: int
    query: str
    response: str
    timestamp: str
    vector_id: int

class CacheSearchResult(BaseModel):
    is_hit: bool
    similarity_score: float
    cached_entry: Optional[CacheEntry] = None
    latency_ms: float

class CacheStats(BaseModel):
    total_entries: int
    dimension: int
    similarity_threshold: float
    index_file_size_bytes: int
    file_path: str
