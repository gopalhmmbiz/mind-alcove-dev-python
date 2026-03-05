from fastapi import APIRouter, Depends, BackgroundTasks

from app.api.schemas.affirmation import (
    AffirmationRequest,
    AffirmationResponse,
)
from app.core.dependencies import verify_signature
from app.core.responses import SuccessResponse
from app.services.affirmation import generate_affirmations_service

router = APIRouter()


@router.post(
    "/generate-affirmations",
    tags=["affirmations"],
    response_model=SuccessResponse[AffirmationResponse],
    dependencies=[Depends(verify_signature)]
)
async def generate_affirmations(
    payload: AffirmationRequest,
    background_tasks: BackgroundTasks,
) -> SuccessResponse[AffirmationResponse]:
    """
    Endpoint to trigger AI affirmation generation.
    """

    data = await generate_affirmations_service(
        payload=payload,
        background_tasks=background_tasks
    )

    return SuccessResponse(data=data)
