from pydantic import BaseModel, Field


class JournalSuggestion(BaseModel):
    """
    A single AI-generated journal guidance suggestion.
    """

    title: str = Field(
        ...,
        description="The title of the journal",
        min_length=1,
        max_length=50,
    )

    suggestion: str = Field(
        ...,
        description="A single-sentence, open-ended journal guidance suggestion to help the user reflect deeper.",
        min_length=10,
        max_length=200,
    )
