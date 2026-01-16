from pydantic import BaseModel, Field
from typing import Optional


class AffirmationRequest(BaseModel):
    user_goal: str = Field(
        ...,
        description="Short-term goal the user wants to work on using affirmations"
    )
    overall_goal: str = Field(
        "Not Available",
        description="User's long-term intention for using the app"
    )
    mood: str = Field(
        "Not Available",
        description="User's recent overall mood"
    )
    emotion: Optional[str] = Field(
        "Not Available",
        description="User's current specific emotion"
    )

class AffirmationResponse(BaseModel):
    affirmation_one: str
    affirmation_two: str
    affirmation_three: str
