import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "Python Chatbot (Semantic Cache)"
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 8000))
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8000")
    
    # Semantic Cache Config (0.60 threshold)
    SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", 0.60))
    FAISS_DIMENSION: int = int(os.getenv("FAISS_DIMENSION", 768))
    FAISS_INDEX_PATH: str = os.getenv("FAISS_INDEX_PATH", "backend/database/faiss.index")
    CACHE_METADATA_PATH: str = os.getenv("CACHE_METADATA_PATH", "backend/database/cache_store.json")
    
    # Gemini AI Models
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-004")


    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()


