import numpy as np

def normalize_vector(vec: np.ndarray) -> np.ndarray:
    """Normalize vector to unit length (L2 norm) for cosine similarity computation."""
    vec = np.array(vec, dtype=np.float32)
    norm = np.linalg.norm(vec)
    if norm == 0:
        return vec
    return vec / norm

def compute_cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Compute cosine similarity score between two vectors."""
    v1 = normalize_vector(vec1)
    v2 = normalize_vector(vec2)
    return float(np.dot(v1, v2))
