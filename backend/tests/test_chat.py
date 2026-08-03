from fastapi.testclient import TestClient
from backend.app import app
from backend.services.semantic_cache_service import semantic_cache_service

client = TestClient(app)

def setup_function():
    semantic_cache_service.clear_cache()

def teardown_function():
    semantic_cache_service.clear_cache()

def test_root_endpoint():
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "online"

def test_chat_flow_hit_miss():
    payload = {
        "query": "How to iterate over a list in Python?",
        "history": [],
        "similarity_threshold": 0.80
    }
    
    # First request: Cache Miss
    res1 = client.post("/api/chat", json=payload)
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["is_cached"] is False
    assert data1["source"] == "gemini"
    
    # Second identical request: Cache Hit
    res2 = client.post("/api/chat", json=payload)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["is_cached"] is True
    assert data2["source"] == "cache"
    assert data2["similarity_score"] >= 0.80
    assert data2["gemini_latency_ms"] == 0.0

def test_off_topic_query():
    payload = {
        "query": "What is the capital of France?",
        "history": []
    }
    res = client.post("/api/chat", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "strictly as a Python programming assistant" in data["response"]
