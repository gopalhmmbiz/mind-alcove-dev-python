from pydantic import BaseModel, Field
from typing import Optional


class JournalSuggestionRequest(BaseModel):
    journal_text: str = Field(
        ...,
        description="Full journal text including the app question(s) and user answer(s).",
        min_length=1,
    )

    mood: str = Field(
        "Not Available",
        description="User's recent overall mood",
    )

    emotion: Optional[str] = Field(
        "Not Available",
        description="User's current specific emotion",
    )

    life_factor: str = Field(
        "Not Available",
        description="Life factor influencing the user's mood and emotion",
    )


class JournalSuggestionResponse(BaseModel):
    suggestion: str = Field(
        ...,
        description="A single AI-generated journal guidance suggestion",
    )
