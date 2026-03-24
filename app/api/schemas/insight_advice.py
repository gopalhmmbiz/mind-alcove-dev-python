from pydantic import BaseModel, Field
from typing import List, Optional

class MoodCount(BaseModel):
    mood_id: int
    mood_board_emotions: str
    total: float

class MoodCause(BaseModel):
    title: str
    total: int
    percent: float

class MoodInfluencer(BaseModel):
    mood_id: int
    mood: str
    causes: List[MoodCause]

class MoodAdviceRequest(BaseModel):
    user_id: int = Field(
        ...,
        description="The unique ID of the user requesting insights"
    )
    overallCounts: List[MoodCount] = Field(
        ...,
        description="List of total counts for each emotion recorded"
    )
    overallMoodInfluencer: List[MoodInfluencer] = Field(
        ...,
        description="Detailed breakdown of what caused specific moods"
    )
    startDate: str = Field(..., description="Start date of the mood tracking period")
    endDate: str = Field(..., description="End date of the mood tracking period")

class MoodInsight(BaseModel):
    mood_id: int
    mood: str
    insight: str

class MoodAdviceResponse(BaseModel):
    insights: List[MoodInsight]
