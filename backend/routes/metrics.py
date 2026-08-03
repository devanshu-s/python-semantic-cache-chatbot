from fastapi import APIRouter
from backend.models.metrics_models import SystemMetrics
from backend.services.metrics_service import metrics_service

router = APIRouter(prefix="/api/metrics", tags=["Metrics & Benchmarking"])

@router.get("", response_model=SystemMetrics)
async def get_system_metrics() -> SystemMetrics:
    """Retrieve real-time performance KPIs and cache hit/miss statistics."""
    return metrics_service.get_metrics()

@router.post("/reset")
async def reset_system_metrics():
    """Reset all performance counters."""
    metrics_service.reset_metrics()
    return {"message": "Metrics successfully reset."}
