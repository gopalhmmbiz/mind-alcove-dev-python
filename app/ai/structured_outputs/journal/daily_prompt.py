from pydantic import BaseModel, Field

class JournalPrompt(BaseModel):
    """
    A single journal encouragement prompt for the user.
    """

    prompt: str = Field(
        ...,
        description=(
            "The final journal encouragement prompt. Must be under 25 words, "
            "not too personal but aligns with user's interests, and derived from the user's reflection history."
        ),
        min_length=10,
        max_length=200,
    )
