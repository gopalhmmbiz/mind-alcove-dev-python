from langchain.chat_models import init_chat_model
from langchain.messages import SystemMessage, HumanMessage

from app.ai.models import SMART
from app.ai.prompts.journal.suggestion import SYSTEM_MESSAGE, USER_MESSAGE
from app.ai.structured_outputs.journal import JournalSuggestion
from app.api.schemas.journal import (
    JournalSuggestionRequest,
    JournalSuggestionResponse,
)


async def generate_journal_suggestion_service(
    payload: JournalSuggestionRequest,
) -> JournalSuggestionResponse:
    """
    Generate a single journal guidance prompt using LLM.
    """

    formatted_user_message = USER_MESSAGE.format(
        journal_text=payload.journal_text,
        mood=payload.mood,
        emotion=payload.emotion,
        life_factor=payload.life_factor,
    )

    messages = [
        SystemMessage(SYSTEM_MESSAGE),
        HumanMessage(formatted_user_message),
    ]

    # Define the LLM model
    llm = init_chat_model(SMART, temperature=0.9)

    structured_llm = llm.with_structured_output(JournalSuggestion)

    response: JournalSuggestion = await structured_llm.ainvoke(messages)

    return JournalSuggestionResponse(suggestion=response.suggestion)
