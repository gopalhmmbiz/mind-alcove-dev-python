from fastapi import APIRouter, Depends, BackgroundTasks

from app.api.schemas.insight_advice import (
    MoodAdviceRequest,
    MoodAdviceResponse,
)
from app.core.dependencies import verify_signature
from app.core.responses import SuccessResponse
from app.services.insight_advice import get_insight_advice_service

router = APIRouter()


@router.post(
    "/get-insight-advice",
    tags=["moods"],
    response_model=SuccessResponse[MoodAdviceResponse],
    dependencies=[Depends(verify_signature)],
)
async def get_insight_advice(
    payload: MoodAdviceRequest,
    background_tasks: BackgroundTasks,
) -> SuccessResponse[MoodAdviceResponse]:
    """
    Analyzes aggregated mood data to provide a brief,
    non-clinical AI insight (approx. 35 words).
    """
    data = await get_insight_advice_service(
        payload=payload,
        background_tasks=background_tasks
    )
    return SuccessResponse(data=data)