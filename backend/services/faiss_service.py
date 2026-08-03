import os
import faiss
import numpy as np
from typing import Tuple, List
from backend.config.settings import settings
from backend.utils.logger import logger
from backend.utils.helpers import ensure_directory_exists

class FAISSService:
    def __init__(self):
        self.dimension = settings.FAISS_DIMENSION
        self.filepath = settings.FAISS_INDEX_PATH
        self.index = self._initialize_index()

    def _initialize_index(self) -> faiss.Index:
        """Initialize or load FAISS IndexFlatIP (Inner Product = Cosine Similarity for normalized vectors)."""
        ensure_directory_exists(self.filepath)
        if os.path.exists(self.filepath):
            try:
                index = faiss.read_index(self.filepath)
                logger.info(f"Loaded existing FAISS index from {self.filepath} with {index.ntotal} vectors.")
                return index
            except Exception as e:
                logger.error(f"Failed to load FAISS index from {self.filepath}: {e}. Creating new index.")
        
        index = faiss.IndexFlatIP(self.dimension)
        logger.info(f"Initialized new FAISS IndexFlatIP with dimension {self.dimension}.")
        return index

    def add_vector(self, vector: np.ndarray) -> int:
        """
        Add normalized vector to index and return its assigned vector index ID.
        """
        vec = np.ascontiguousarray(vector.reshape(1, -1), dtype=np.float32)
        vector_id = self.index.ntotal
        self.index.add(vec)
        self.save_index()
        logger.info(f"Added vector to FAISS index. Total vectors now: {self.index.ntotal}")
        return vector_id

    def search_vector(self, query_vector: np.ndarray, top_k: int = 1) -> Tuple[np.ndarray, np.ndarray]:
        """
        Search for top_k most similar vectors. Returns (scores, vector_indices).
        """
        if self.index.ntotal == 0:
            return np.array([[-1.0]], dtype=np.float32), np.array([[-1]], dtype=np.int64)

        vec = np.ascontiguousarray(query_vector.reshape(1, -1), dtype=np.float32)
        scores, indices = self.index.search(vec, top_k)
        return scores[0], indices[0]

    def save_index(self) -> None:
        """Save FAISS index to disk."""
        ensure_directory_exists(self.filepath)
        try:
            faiss.write_index(self.index, self.filepath)
        except Exception as e:
            logger.error(f"Failed to write FAISS index to {self.filepath}: {e}")

    def reset_index(self) -> None:
        """Clear all vectors from the index."""
        self.index = faiss.IndexFlatIP(self.dimension)
        self.save_index()
        logger.info("FAISS index reset.")

    def get_total_count(self) -> int:
        """Get total number of vectors stored in FAISS."""
        return self.index.ntotal

faiss_service = FAISSService()
