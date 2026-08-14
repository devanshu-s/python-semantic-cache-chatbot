import os
import sys
import json
import time

# Ensure project root is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.services.semantic_cache_service import semantic_cache_service
from backend.services.embedding_service import embedding_service
from backend.services.faiss_service import faiss_service
from backend.utils.logger import logger

def seed_cache():
    metadata_path = "backend/database/cache_store.json"
    if not os.path.exists(metadata_path):
        print(f"Metadata file {metadata_path} not found.")
        return

    with open(metadata_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    total_entries = len(raw_data)
    print(f"Found {total_entries} entries in {metadata_path}. Generating FAISS vectors...")

    # Reset FAISS index before seeding
    faiss_service.reset_index()

    start_time = time.time()
    for idx, (key, entry) in enumerate(raw_data.items(), 1):
        query = entry["query"]
        # Generate embedding for query
        vector = embedding_service.generate_embedding(query)
        # Add vector to FAISS index
        faiss_service.add_vector(vector)
        print(f"[{idx}/{total_entries}] Cached query: '{query}' -> Vector ID: {entry['vector_id']}")

    print(f"\n✅ Successfully seeded FAISS index with {faiss_service.get_total_count()} vectors in {time.time() - start_time:.2f}s!")

if __name__ == "__main__":
    seed_cache()
