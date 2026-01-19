from pydantic import BaseModel, Field, conlist
from typing import Annotated


class Affirmation(BaseModel):
    """
    A single affirmation.
    """

    text: str = Field(
        ...,
        description="A short, single-sentence affirmation.",
        max_length=80,
    )

class Affirmations(BaseModel):
    """
    A collection of affirmations for emotional well-being.
    """

    affirmations: Annotated[
        conlist(Affirmation, min_length=3, max_length=3),
        Field(
            description="A list of exactly three affirmations.",
        ),
    ]
