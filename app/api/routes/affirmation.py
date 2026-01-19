from fastapi import APIRouter, Depends

from app.api.schemas.affirmation import (
    AffirmationRequest,
    AffirmationResponse,
)
from app.core.dependencies import require_secret_key
from app.core.responses import SuccessResponse
from app.services.affirmation import generate_affirmations_service

router = APIRouter()


@router.post(
    "/generate-affirmations",
    tags=["affirmations"],
    response_model=SuccessResponse[AffirmationResponse],
    dependencies=[Depends(require_secret_key)]
)
async def generate_affirmations(
    payload: AffirmationRequest,
) -> SuccessResponse[AffirmationResponse]:
    data = await generate_affirmations_service(payload)
    return SuccessResponse(data=data)
