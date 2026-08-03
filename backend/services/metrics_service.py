from typing import List
from backend.models.metrics_models import SystemMetrics
from backend.services.semantic_cache_service import semantic_cache_service

class MetricsService:
    def __init__(self):
        self.total_requests = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.total_latencies: List[float] = []
        self.gemini_latencies: List[float] = []
        self.cache_latencies: List[float] = []

    def record_query(self, is_hit: bool, total_latency: float, gemini_latency: float, cache_latency: float) -> None:
        """
        Record performance metrics for a processed query.
        """
        self.total_requests += 1
        self.total_latencies.append(total_latency)
        self.cache_latencies.append(cache_latency)

        if is_hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
            self.gemini_latencies.append(gemini_latency)

    def get_metrics(self) -> SystemMetrics:
        """
        Calculate current aggregated metrics summary.
        """
        hit_rate = (self.cache_hits / self.total_requests * 100.0) if self.total_requests > 0 else 0.0
        miss_rate = (self.cache_misses / self.total_requests * 100.0) if self.total_requests > 0 else 0.0
        
        avg_total_lat = (sum(self.total_latencies) / len(self.total_latencies)) if self.total_latencies else 0.0
        avg_gemini_lat = (sum(self.gemini_latencies) / len(self.gemini_latencies)) if self.gemini_latencies else 0.0
        avg_cache_lat = (sum(self.cache_latencies) / len(self.cache_latencies)) if self.cache_latencies else 0.0

        cache_stats = semantic_cache_service.get_stats()

        return SystemMetrics(
            total_requests=self.total_requests,
            cache_hits=self.cache_hits,
            cache_misses=self.cache_misses,
            hit_rate_percentage=round(hit_rate, 2),
            miss_rate_percentage=round(miss_rate, 2),
            avg_total_latency_ms=round(avg_total_lat, 2),
            avg_gemini_latency_ms=round(avg_gemini_lat, 2),
            avg_cache_latency_ms=round(avg_cache_lat, 2),
            gemini_api_calls_saved=self.cache_hits,
            cache_size=cache_stats.total_entries
        )

    def reset_metrics(self) -> None:
        """Reset in-memory performance statistics counters."""
        self.total_requests = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.total_latencies.clear()
        self.gemini_latencies.clear()
        self.cache_latencies.clear()

metrics_service = MetricsService()
