from fastapi import APIRouter, Depends

from app.api.schemas.activity_suggestion import (
    ActivitySuggestionRequest,
    ActivitySuggestionResponse,
)
from app.core.dependencies import verify_signature
from app.core.responses import SuccessResponse
from app.services.activity_suggestion.main_service import generate_activity_routine

router = APIRouter()


@router.post(
    "/get-activity-routine",
    tags=["activity-routine"],
    response_model=SuccessResponse[ActivitySuggestionResponse],
    dependencies=[Depends(verify_signature)]
)
async def get_activity_routine(
    payload: ActivitySuggestionRequest,
) -> SuccessResponse[ActivitySuggestionResponse]:
    data = await generate_activity_routine(payload)
    return SuccessResponse(data=data)
