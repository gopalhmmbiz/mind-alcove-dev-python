from pydantic import BaseModel, Field


class LLMInsightOutput(BaseModel):
    advice: str = Field(description="The non-clinical advice text, under 35 words.")
