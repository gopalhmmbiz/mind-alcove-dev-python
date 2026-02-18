from pydantic import BaseModel, Field
from typing import List, Optional, Union


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
    is_premium: bool | int = Field(
        ...,
        description="flag whether the user is premium or not"
    )

class Activity(BaseModel):
    id: Optional[Union[int, str]] = None
    name: Optional[str] = None
    benefit_tags: List[str] = []
    time_val: Optional[Union[int, str]] = None
    parent_category_id: Optional[Union[int, str]] = None
    parent_category_name: Optional[str] = None
    type: Optional[str] = None

class DailyRoutine(BaseModel):
    morning: List[Activity]
    afternoon: List[Activity]
    evening: List[Activity]

class ActivitySuggestionResponse(BaseModel):
    routine: DailyRoutine
