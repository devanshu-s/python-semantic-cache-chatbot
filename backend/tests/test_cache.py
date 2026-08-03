import pytest
from backend.services.semantic_cache_service import semantic_cache_service
from backend.services.embedding_service import embedding_service

@pytest.fixture(autouse=True)
def clean_cache():
    semantic_cache_service.clear_cache()
    yield
    semantic_cache_service.clear_cache()

def test_cache_miss_on_empty_index():
    result, _ = semantic_cache_service.search_cache("How to sort a list in Python?")
    assert result.is_hit is False
    assert result.cached_entry is None

def test_cache_hit_on_identical_query():
    query = "How to sort a list in Python?"
    response = "Use the sort() method or sorted() function."
    vec = embedding_service.generate_embedding(query)
    
    semantic_cache_service.add_to_cache(query, response, vec)
    
    result, _ = semantic_cache_service.search_cache(query, threshold=0.80)
    assert result.is_hit is True
    assert result.cached_entry is not None
    assert result.cached_entry.response == response
    assert result.similarity_score >= 0.80

def test_cache_clear():
    query = "How do I print in Python?"
    vec = embedding_service.generate_embedding(query)
    semantic_cache_service.add_to_cache(query, "Use print('hello')", vec)
    
    assert semantic_cache_service.get_stats().total_entries == 1
    semantic_cache_service.clear_cache()
    assert semantic_cache_service.get_stats().total_entries == 0
