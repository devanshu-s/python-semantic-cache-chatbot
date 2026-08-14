import os
import json
import time
import numpy as np
from typing import Dict, List, Optional
from backend.config.settings import settings
from backend.models.cache_models import CacheEntry, CacheSearchResult, CacheStats
from backend.services.embedding_service import embedding_service
from backend.services.faiss_service import faiss_service
from backend.utils.logger import logger
from backend.utils.helpers import ensure_directory_exists, get_current_timestamp

class SemanticCacheService:
    def __init__(self):
        self.metadata_path = settings.CACHE_METADATA_PATH
        self.default_threshold = settings.SIMILARITY_THRESHOLD
        self.cache_store: Dict[int, CacheEntry] = self._load_metadata()

    def _load_metadata(self) -> Dict[int, CacheEntry]:
        """Load JSON metadata mapping vector_id -> CacheEntry."""
        ensure_directory_exists(self.metadata_path)
        if os.path.exists(self.metadata_path):
            try:
                with open(self.metadata_path, 'r', encoding='utf-8') as f:
                    raw_data = json.load(f)
                    store = {}
                    for k, v in raw_data.items():
                        store[int(k)] = CacheEntry(**v)
                    logger.info(f"Loaded {len(store)} cache metadata entries from {self.metadata_path}.")
                    return store
            except Exception as e:
                logger.error(f"Failed to load cache metadata from {self.metadata_path}: {e}")
        return {}

    def _save_metadata(self) -> None:
        """Persist metadata dictionary to JSON file."""
        ensure_directory_exists(self.metadata_path)
        try:
            raw_data = {str(k): v.model_dump() for k, v in self.cache_store.items()}
            with open(self.metadata_path, 'w', encoding='utf-8') as f:
                json.dump(raw_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save cache metadata to {self.metadata_path}: {e}")

    def search_cache(self, query: str, threshold: Optional[float] = None) -> Tuple[CacheSearchResult, np.ndarray]:
        """
        Search for semantically similar query in FAISS cache.
        Returns (CacheSearchResult, query_embedding).
        """
        start_time = time.perf_counter()
        effective_threshold = threshold if threshold is not None else self.default_threshold

        query_embedding = embedding_service.generate_embedding(query)
        scores, vector_indices = faiss_service.search_vector(query_embedding, top_k=1)

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        if scores[0] >= 0 and vector_indices[0] != -1:
            best_score = float(scores[0])
            best_vector_id = int(vector_indices[0])

            if best_score >= effective_threshold and best_vector_id in self.cache_store:
                cached_entry = self.cache_store[best_vector_id]
                logger.info(f"CACHE HIT! Score: {best_score:.4f} >= Threshold: {effective_threshold} for query: '{query}'")
                return CacheSearchResult(
                    is_hit=True,
                    similarity_score=best_score,
                    cached_entry=cached_entry,
                    latency_ms=latency_ms
                ), query_embedding

            logger.info(f"CACHE MISS (Score: {best_score:.4f} < Threshold: {effective_threshold}) for query: '{query}'")
            return CacheSearchResult(
                is_hit=False,
                similarity_score=max(0.0, best_score),
                cached_entry=None,
                latency_ms=latency_ms
            ), query_embedding

        logger.info(f"CACHE MISS (Empty index) for query: '{query}'")
        return CacheSearchResult(
            is_hit=False,
            similarity_score=0.0,
            cached_entry=None,
            latency_ms=latency_ms
        ), query_embedding

    def add_to_cache(self, query: str, response: str, vector: np.ndarray) -> CacheEntry:
        """
        Add query-response pair and pre-computed vector to cache.
        """
        vector_id = faiss_service.add_vector(vector)
        entry_id = len(self.cache_store) + 1
        entry = CacheEntry(
            id=entry_id,
            query=query.strip(),
            response=response.strip(),
            timestamp=get_current_timestamp(),
            vector_id=vector_id
        )
        self.cache_store[vector_id] = entry
        self._save_metadata()
        logger.info(f"Saved new cache entry ID #{entry_id} (Vector ID: {vector_id})")
        return entry

    def clear_cache(self) -> None:
        """Clear all cache vectors and metadata."""
        faiss_service.reset_index()
        self.cache_store.clear()
        self._save_metadata()
        logger.info("Semantic cache successfully cleared.")

    def get_all_entries(self) -> List[CacheEntry]:
        """Return list of all cached entries ordered by ID."""
        return sorted(list(self.cache_store.values()), key=lambda x: x.id)

    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        index_file_size = 0
        if os.path.exists(settings.FAISS_INDEX_PATH):
            index_file_size = os.path.getsize(settings.FAISS_INDEX_PATH)

        return CacheStats(
            total_entries=len(self.cache_store),
            dimension=settings.FAISS_DIMENSION,
            similarity_threshold=self.default_threshold,
            index_file_size_bytes=index_file_size,
            file_path=settings.FAISS_INDEX_PATH
        )

    def set_threshold(self, threshold: float) -> float:
        """Update default similarity threshold dynamically."""
        self.default_threshold = max(0.0, min(1.0, threshold))
        logger.info(f"Updated semantic cache default threshold to: {self.default_threshold}")
        return self.default_threshold


# Fixed syntax in get_stats
semantic_cache_service = SemanticCacheService()
