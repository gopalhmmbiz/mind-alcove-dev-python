from fastapi import APIRouter

from app.api.schemas.health import HealthResponse
from app.core.config import settings
from app.core.responses import SuccessResponse

router = APIRouter()


@router.get("/health", tags=["health"], response_model=SuccessResponse[HealthResponse])
def health() -> SuccessResponse[HealthResponse]:
    data = HealthResponse(
        app=settings.app_name,
        environment=settings.env,
        status="running",
    )

    return SuccessResponse(data=data)
