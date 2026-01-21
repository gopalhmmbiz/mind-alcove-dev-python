from pydantic import BaseModel, Field


class JournalSuggestion(BaseModel):
    """
    A single AI-generated journal guidance suggestion.
    """

    suggestion: str = Field(
        ...,
        description="A single-sentence, open-ended journal guidance suggestion to help the user reflect deeper.",
        min_length=10,
        max_length=200,
    )
