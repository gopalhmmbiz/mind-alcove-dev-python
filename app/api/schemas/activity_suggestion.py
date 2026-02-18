from pydantic import BaseModel, Field
from typing import List, Optional, Union


class ActivitySuggestionRequest(BaseModel):
    user_id: Union[int, str]
    user_mood: Optional[str] = None
    user_goal: Optional[str] = None
    routine_length: Optional[str] = None
    is_premium: Optional[Union[bool, int]] = 0

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
