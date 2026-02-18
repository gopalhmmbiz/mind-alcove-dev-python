from typing import List
from pydantic import BaseModel, Field

class Activity(BaseModel):
    """
    Essential activity data for the user's schedule, focusing on identification
    and clear, concise benefits.
    """
    id: int = Field(..., description="The unique activity identifier from the library.")
    name: str = Field(..., description="The name of the specific activity.")
    activity_type: str = Field(..., description="The category/parent activity name.")
    time: int = Field(..., description="The duration of the activity in minutes.")
    benefits: List[str] = Field(
        ...,
        min_items=1,
        max_items=3,
        description="A list of 2 to 3 concise benefits (e.g., 'Mental Balance', 'Emotional Relief')."
    )

class DailyRoutine(BaseModel):
    """
    The finalized daily wellness schedule organized by time of day.
    """
    morning: List[Activity] = Field(default_factory=list)
    afternoon: List[Activity] = Field(default_factory=list)
    evening: List[Activity] = Field(default_factory=list)
