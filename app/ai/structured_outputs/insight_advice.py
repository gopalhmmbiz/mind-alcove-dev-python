from typing import List
from pydantic import BaseModel, Field

class MoodInsight(BaseModel):
    mood_id: int = Field(description="The ID of the mood this insight refers to")
    mood: str = Field(description="The name of the emotion (e.g., STRESSED, HAPPY)")
    insight: str = Field(description="The non-clinical advice/insight under 35 words")

class LLMInsightResponse(BaseModel):
    insights: List[MoodInsight]