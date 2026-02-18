from pydantic import BaseModel, Field
from typing import List


class ActivitySuggestionRequest(BaseModel):
    user_id: int | str
    user_mood: str = Field(
        ...,
        description="current mood of the user"
    )
    user_goal: str = Field(
        ...,
        description="overall goal of the user"
    )
    routine_length: str = Field(
        ...,
        description="preferred routine length of the user"
    )
    is_premium: bool = Field(
        ...,
        description="flag whether the user is premium or not"
    )

class Activity(BaseModel):
    id: int | str
    name: str
    benefit_tags: List[str]
    time_val: int | str
    parent_category_id: int | str
    parent_category_name: str
    type: str

class DailyRoutine(BaseModel):
    morning: List[Activity]
    afternoon: List[Activity]
    evening: List[Activity]

class ActivitySuggestionResponse(BaseModel):
    routine: DailyRoutine
