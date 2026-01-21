from fastapi import APIRouter, Depends

from app.api.schemas.journal import (
    JournalSuggestionRequest,
    JournalSuggestionResponse,
)
from app.core.dependencies import require_secret_key
from app.core.responses import SuccessResponse
from app.services.journal import generate_journal_suggestion_service

router = APIRouter()


@router.post(
    "/generate-journal-suggestion",
    tags=["journals"],
    response_model=SuccessResponse[JournalSuggestionResponse],
    dependencies=[Depends(require_secret_key)],
)
async def generate_journal_suggestion(
    payload: JournalSuggestionRequest,
) -> SuccessResponse[JournalSuggestionResponse]:
    data = await generate_journal_suggestion_service(payload)
    return SuccessResponse(data=data)
