from pydantic import BaseModel, Field

class Affirmations(BaseModel):
    """
    Three structured affirmations for emotional well-being.
    """
    affirmation_one: str = Field(
        ...,
        description="Emotional stabilization affirmation that gently regulates the user's current mood and emotion"
    )
    affirmation_two: str = Field(
        ...,
        description="Identity or belief reinforcement aligned with the user's long-term well-being"
    )
    affirmation_three: str = Field(
        ...,
        description="Action-oriented encouragement aligned with the user's short-term goal"
    )
