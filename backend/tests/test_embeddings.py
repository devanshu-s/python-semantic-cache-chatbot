import numpy as np
from backend.services.embedding_service import embedding_service
from backend.utils.similarity import compute_cosine_similarity

def test_embedding_dimension_and_normalization():
    vec = embedding_service.generate_embedding("How to create a dictionary in Python?")
    assert isinstance(vec, np.ndarray)
    assert vec.shape == (768,)
    norm = np.linalg.norm(vec)
    assert abs(norm - 1.0) < 1e-4

def test_similarity_score_identical_texts():
    text1 = "How to reverse a list in Python?"
    text2 = "How to reverse a list in Python?"
    v1 = embedding_service.generate_embedding(text1)
    v2 = embedding_service.generate_embedding(text2)
    similarity = compute_cosine_similarity(v1, v2)
    assert similarity >= 0.99

def test_similarity_score_semantic_variations():
    text1 = "How to reverse a list in Python?"
    text2 = "What is the syntax for reversing a list in Python?"
    v1 = embedding_service.generate_embedding(text1)
    v2 = embedding_service.generate_embedding(text2)
    similarity = compute_cosine_similarity(v1, v2)
    assert similarity > 0.45
