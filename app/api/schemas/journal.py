from pydantic import BaseModel, Field


class JournalSuggestionRequest(BaseModel):
    journal_text: str = Field(
        ...,
        description="Full journal text including the app question(s) and user answer(s).",
        min_length=1,
    )
    user_id: int = Field(
        description="The ID of the user who made the request",
    )


class JournalSuggestionResponse(BaseModel):
    title: str = Field(
        ...,
        description="The title of the journal",
    )
    suggestion: str = Field(
        ...,
        description="A single AI-generated journal guidance suggestion",
    )
