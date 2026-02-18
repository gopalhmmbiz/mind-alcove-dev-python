from fastapi import APIRouter, Depends

from app.api.schemas.activity_suggestion import (
    ActivitySuggestionRequest,
    ActivitySuggestionResponse,
)
from app.core.dependencies import require_secret_key
from app.core.responses import SuccessResponse
from app.services.activity_suggestion.main_service import get_activity_suggestion

router = APIRouter()


@router.post(
    "/get-activity-suggestion",
    tags=["activity-suggestion"],
    response_model=SuccessResponse[ActivitySuggestionResponse],
    dependencies=[Depends(require_secret_key)]
)
async def activity_suggestion(
    payload: ActivitySuggestionRequest,
) -> SuccessResponse[ActivitySuggestionResponse]:
    data = await get_activity_suggestion(payload)
    return SuccessResponse(data=data)
