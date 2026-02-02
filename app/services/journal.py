from langchain.chat_models import init_chat_model
from langchain.messages import SystemMessage, HumanMessage

from app.ai.models import SMART
from app.ai.prompts.journal.suggestion import SYSTEM_MESSAGE, USER_MESSAGE
from app.ai.structured_outputs.journal import JournalSuggestion
from app.api.schemas.journal import (
    JournalSuggestionRequest,
    JournalSuggestionResponse,
)


# Define the LLM model
_llm = init_chat_model(
    SMART,
    temperature=0.7,
    timeout=15,
    max_retries=3
)

_structured_llm = _llm.with_structured_output(JournalSuggestion)

async def generate_journal_suggestion_service(
    payload: JournalSuggestionRequest,
) -> JournalSuggestionResponse:
    """
    Generate a single journal guidance prompt using LLM.
    """

    formatted_user_message = USER_MESSAGE.format(
        journal_text=payload.journal_text
    )

    messages = [
        SystemMessage(SYSTEM_MESSAGE),
        HumanMessage(formatted_user_message),
    ]

    response: JournalSuggestion = await _structured_llm.ainvoke(messages)

    return JournalSuggestionResponse(title=response.title, suggestion=response.suggestion)
