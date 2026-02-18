from pydantic import BaseModel, Field
from typing import List

class BehavioralObservation(BaseModel):
    """
    A single behavioral signal capturing context and result.
    Example: 'When it is Morning and the user feels Bored, they tend to perform Motivation Breathing which results in a Happy mood.'
    """
    pattern: str = Field(
        ...,
        max_length=300,
        description="The behavior pattern: 'When [Context], user tends to [Behavior/Result]'"
    )
    stability: int = Field(
        default=1,
        ge=0,
        le=7,
        description="Strength/Weight of the pattern. +1 for match, -1 for contradiction. Pruned at 0."
    )

class UserDynamicProfile(BaseModel):
    """
    The persistent state of the user, used to inform the recommendation engine.
    """
    biography: str = Field(
        ...,
        max_length=750,
        description="A concise semantic summary of the user's current wellness identity and momentum."
    )
    observations: List[BehavioralObservation] = Field(
        default_factory=list,
        max_length=20,
        description="List of up to 20 tactical observations about user behavior. Merge or prune if exceeding 20."
    )
