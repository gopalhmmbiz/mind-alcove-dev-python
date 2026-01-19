from pydantic import BaseModel, Field
from typing import Optional, List


class AffirmationRequest(BaseModel):
    user_goal: str = Field(
        ...,
        description="Short-term goal the user wants to work on using affirmations"
    )
    mood: str = Field(
        "Not Available",
        description="User's recent overall mood"
    )
    emotion: Optional[str] = Field(
        "Not Available",
        description="User's current specific emotion"
    ),
    life_factor: str = Field(
        "Not Available",
        description="Life factor for user's recent overall mood"
    )

class AffirmationResponse(BaseModel):
    affirmations: List[str]
