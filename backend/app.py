from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.config.settings import settings
from backend.routes import chat, cache, metrics, test_cases, leetcode, sessions
from backend.utils.logger import logger
from backend.services.faiss_service import faiss_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.PROJECT_NAME} backend...")
    logger.info(f"Loaded FAISS index with {faiss_service.get_total_count()} entries.")
    yield
    logger.info("Shutting down backend...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for Python Chatbot with FAISS Semantic Cache",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(chat.router)
app.include_router(cache.router)
app.include_router(metrics.router)
app.include_router(test_cases.router)
app.include_router(leetcode.router)
app.include_router(sessions.router)




@app.get("/")
async def root():
    return {
        "status": "online",
        "app_name": settings.PROJECT_NAME,
        "similarity_threshold": settings.SIMILARITY_THRESHOLD,
        "gemini_model": settings.GEMINI_MODEL
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app:app", host=settings.HOST, port=settings.PORT, reload=True)
