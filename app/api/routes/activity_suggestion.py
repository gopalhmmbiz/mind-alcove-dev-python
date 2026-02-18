from fastapi import APIRouter, Depends

from app.api.schemas.activity_suggestion import (
    ActivitySuggestionRequest,
    ActivitySuggestionResponse,
)
from app.core.dependencies import require_secret_key
from app.core.responses import SuccessResponse
from app.services.activity_suggestion.main_service import generate_activity_routine

router = APIRouter()


@router.post(
    "/get-activity-routine",
    tags=["activity-routine"],
    response_model=SuccessResponse[ActivitySuggestionResponse],
    dependencies=[Depends(require_secret_key)]
)
async def get_activity_routine(
    payload: ActivitySuggestionRequest,
) -> SuccessResponse[ActivitySuggestionResponse]:
    data = await generate_activity_routine(payload)
    return SuccessResponse(data=data)
