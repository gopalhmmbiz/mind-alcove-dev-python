# app/services/llm_trace.py
from app.db.session import AsyncSessionLocal
from app.db.models.llm_calls import LLMCall

async def log_llm_event(trace_data: dict):
    """
    Background task to log LLM calls.
    Uses AsyncSessionLocal directly to ensure a fresh session.
    """
    async with AsyncSessionLocal() as session:
        try:
            new_call = LLMCall(**trace_data)
            session.add(new_call)
            await session.commit()
        except Exception as e:
            await session.rollback()
