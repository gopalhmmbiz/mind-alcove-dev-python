from pydantic import BaseModel, Field, field_validator
from typing import List


class AffirmationRequest(BaseModel):
    user_id: int = Field(
        description="The ID of the user who made the affirmation request",
    )
    user_goal: str = Field(
        ...,
        min_length=2,
        max_length=1000,  # Prevent prompt injection or huge token costs
        description="The goal the user wants to work on using affirmations"
    )

    @field_validator("user_goal")
    @classmethod
    def strip_text(cls, v: str) -> str:
        return v.strip()


class AffirmationResponse(BaseModel):
    affirmations: List[str]
