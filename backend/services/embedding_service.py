import hashlib
import numpy as np
from backend.config.settings import settings
from backend.utils.logger import logger
from backend.utils.similarity import normalize_vector

class EmbeddingService:
    def __init__(self):
        self.dimension = settings.FAISS_DIMENSION
        self.api_key = settings.GEMINI_API_KEY
        self.model = settings.EMBEDDING_MODEL

    def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate a normalized 768-dim vector embedding for text using Google Gemini Embedding API,
        with a deterministic semantic feature hash fallback if API key is missing or call fails.
        """
        cleaned_text = text.strip()
        if not cleaned_text:
            return np.zeros(self.dimension, dtype=np.float32)

        if self.api_key and self.api_key != "your_gemini_api_key_here":
            try:
                # Primary: Try google-genai SDK
                try:
                    from google import genai
                    client = genai.Client(api_key=self.api_key)
                    res = client.models.embed_content(
                        model=self.model,
                        contents=cleaned_text
                    )
                    vec = np.array(res.embedding.values, dtype=np.float32)
                    return normalize_vector(vec)
                except Exception:
                    # Alternative: Try legacy google.generativeai SDK
                    import google.generativeai as genai_legacy
                    genai_legacy.configure(api_key=self.api_key)
                    res = genai_legacy.embed_content(
                        model=f"models/{self.model}",
                        content=cleaned_text
                    )
                    vec = np.array(res['embedding'], dtype=np.float32)
                    return normalize_vector(vec)
            except Exception as e:
                logger.warning(f"Gemini embedding API call failed: {e}. Falling back to semantic feature generator.")

        # Fallback deterministic semantic vector generator
        return self._generate_fallback_embedding(cleaned_text)

    def _generate_fallback_embedding(self, text: str) -> np.ndarray:
        """
        Generate a pseudo-semantic deterministic vector representation using word stems and n-grams.
        Allows offline testing & instant local execution.
        """
        # Basic normalization & stemming (strip 'ing', 'ed', 's', 'es')
        tokens = []
        for word in text.lower().replace("?", "").replace("!", "").split():
            clean_w = word.strip(".,;:\"'()")
            if not clean_w:
                continue
            tokens.append(clean_w)
            if clean_w.endswith("ing") and len(clean_w) > 5:
                tokens.append(clean_w[:-3])
            elif clean_w.endswith("ed") and len(clean_w) > 4:
                tokens.append(clean_w[:-2])
            elif clean_w.endswith("s") and len(clean_w) > 4:
                tokens.append(clean_w[:-1])

        vector = np.zeros(self.dimension, dtype=np.float32)
        
        # Word token hashing
        for i, word in enumerate(tokens):
            h = int(hashlib.md5(word.encode('utf-8')).hexdigest(), 16)
            idx = h % self.dimension
            vector[idx] += 2.0

        # Character trigram features
        full_str = " ".join(tokens)
        for j in range(len(full_str) - 2):
            trigram = full_str[j:j+3]
            h_tri = int(hashlib.sha256(trigram.encode('utf-8')).hexdigest(), 16)
            idx_tri = h_tri % self.dimension
            vector[idx_tri] += 1.0

        return normalize_vector(vector)

embedding_service = EmbeddingService()
