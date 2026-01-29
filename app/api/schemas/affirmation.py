from pydantic import BaseModel, Field
from typing import List


class AffirmationRequest(BaseModel):
    user_goal: str = Field(
        ...,
        description="The goal the user wants to work on using affirmations"
    )


class AffirmationResponse(BaseModel):
    affirmations: List[str]
