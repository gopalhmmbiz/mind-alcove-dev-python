from fastapi import APIRouter, Depends, BackgroundTasks

from app.api.schemas.journal import (
    JournalSuggestionRequest,
    JournalSuggestionResponse,
)
from app.core.dependencies import verify_signature
from app.core.responses import SuccessResponse
from app.services.journal import generate_journal_suggestion_service

router = APIRouter()


@router.post(
    "/generate-journal-suggestion",
    tags=["journals"],
    response_model=SuccessResponse[JournalSuggestionResponse],
    dependencies=[Depends(verify_signature)],
)
async def generate_journal_suggestion(
    payload: JournalSuggestionRequest,
    background_tasks: BackgroundTasks,
) -> SuccessResponse[JournalSuggestionResponse]:
    data = await generate_journal_suggestion_service(
        payload=payload,
        background_tasks=background_tasks
    )
    return SuccessResponse(data=data)
