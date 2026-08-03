"""
Benchmark Runner Script for Semantic Cache Chatbot
Measures response latencies, cache hit rates, and API call savings WITH vs WITHOUT semantic cache.
"""

import requests
from typing import List

BACKEND_URL = "http://localhost:8000"

BENCHMARK_QUERIES = [
    # Pair 1: List Reversal
    {
        "original": "How do I reverse a list in Python?",
        "variants": [
            "What is the best way to reverse a list in Python?",
            "Python list reversal code example",
            "How to flip a list backwards in Python?"
        ]
    },
    # Pair 2: File Reading
    {
        "original": "How to read a text file line by line in Python?",
        "variants": [
            "What is the syntax to iterate over file lines in Python?",
            "Reading a text file line by line Python code",
            "Best method for reading text files in Python"
        ]
    },
    # Pair 3: Dictionaries
    {
        "original": "How to iterate over a dictionary in Python?",
        "variants": [
            "What is the loop syntax for Python dict keys and values?",
            "How to loop through key value pairs in Python dictionary?",
            "Python dictionary iteration example"
        ]
    },
    # Pair 4: List Comprehension
    {
        "original": "What is list comprehension in Python?",
        "variants": [
            "Explain Python list comprehension with code example",
            "How to use list comprehensions in Python?",
            "Python list comprehension syntax guide"
        ]
    }
]

def run_benchmark():
    print("=" * 70)
    print("⚡ RUNNING SEMANTIC CACHE CHATBOT BENCHMARK ⚡")
    print("=" * 70)

    # 1. Reset Cache and Metrics
    try:
        requests.post(f"{BACKEND_URL}/api/cache/clear")
        requests.post(f"{BACKEND_URL}/api/metrics/reset")
        print("✓ Reset FAISS semantic cache and metrics counters.\n")
    except Exception as e:
        print(f"❌ Failed to communicate with backend at {BACKEND_URL}: {e}")
        print("Please ensure backend server is running (`uvicorn backend.app:app --port 8000`).")
        return

    without_cache_latencies: List[float] = []
    with_cache_latencies: List[float] = []
    hit_count = 0
    miss_count = 0
    similarity_scores: List[float] = []

    print("Phase 1: Populating Cache (Cache Misses -> Direct Gemini Calls)")
    print("-" * 70)

    # Seed the cache with original queries
    for item in BENCHMARK_QUERIES:
        q = item["original"]
        res = requests.post(
            f"{BACKEND_URL}/api/chat",
            json={"query": q, "history": [], "similarity_threshold": 0.50}
        ).json()
        latency = res["total_latency_ms"]
        without_cache_latencies.append(latency)
        miss_count += 1
        print(f" Query: '{q[:45]}...' | Latency: {latency:.2f} ms | Source: {res['source'].upper()}")

    print("\nPhase 2: Executing Semantically Similar Queries (Cache Hits)")
    print("-" * 70)

    # Execute variants (semantic similarities)
    for item in BENCHMARK_QUERIES:
        for variant in item["variants"]:
            res = requests.post(
                f"{BACKEND_URL}/api/chat",
                json={"query": variant, "history": [], "similarity_threshold": 0.50}
            ).json()
            latency = res["total_latency_ms"]
            is_cached = res["is_cached"]
            score = res["similarity_score"]
            similarity_scores.append(score)

            if is_cached:
                hit_count += 1
                with_cache_latencies.append(latency)
                print(f" Query: '{variant[:45]}...' | Latency: {latency:.2f} ms | HIT ({score*100:.1f}%) ⚡")
            else:
                miss_count += 1
                without_cache_latencies.append(latency)
                print(f" Query: '{variant[:45]}...' | Latency: {latency:.2f} ms | MISS ({score*100:.1f}%) 🤖")

    # 3. Calculate Results Summary
    total_queries = miss_count + hit_count
    avg_without_cache = sum(without_cache_latencies) / len(without_cache_latencies) if without_cache_latencies else 0.0
    avg_with_cache = sum(with_cache_latencies) / len(with_cache_latencies) if with_cache_latencies else 0.0

    latency_reduction = (
        ((avg_without_cache - avg_with_cache) / avg_without_cache) * 100.0
        if avg_without_cache > 0 else 0.0
    )
    hit_rate = (hit_count / total_queries) * 100.0 if total_queries > 0 else 0.0
    avg_similarity = (sum(similarity_scores) / len(similarity_scores)) if similarity_scores else 0.0

    print("\n" + "=" * 70)
    print("📊 BENCHMARK PERFORMANCE COMPARISON RESULTS")
    print("=" * 70)
    print(f"Total Benchmark Queries Tested : {total_queries}")
    print(f"Cache Hits                     : {hit_count} ({hit_rate:.1f}%)")
    print(f"Cache Misses                   : {miss_count}")
    print(f"Gemini API Calls Saved         : {hit_count} (100% API cost saved on hits)")
    print(f"Average Similarity Score       : {avg_similarity * 100:.1f}%")
    print(f"Avg Latency WITHOUT Cache      : {avg_without_cache:.2f} ms")
    print(f"Avg Latency WITH Cache         : {avg_with_cache:.2f} ms")
    print(f"⚡ LATENCY REDUCTION            : {latency_reduction:.1f}% FASTER!")
    print("=" * 70)

if __name__ == "__main__":
    run_benchmark()
