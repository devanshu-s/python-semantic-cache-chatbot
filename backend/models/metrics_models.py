from pydantic import BaseModel, Field
from typing import List, Dict, Any

class SystemMetrics(BaseModel):
    total_requests: int
    cache_hits: int
    cache_misses: int
    hit_rate_percentage: float
    miss_rate_percentage: float
    avg_total_latency_ms: float
    avg_gemini_latency_ms: float
    avg_cache_latency_ms: float
    gemini_api_calls_saved: int
    cache_size: int

class BenchmarkComparison(BaseModel):
    queries_tested: int
    without_cache_avg_latency_ms: float
    with_cache_avg_latency_ms: float
    latency_reduction_percentage: float
    cache_hit_count: int
    gemini_calls_saved: int
