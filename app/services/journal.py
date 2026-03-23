from fastapi import BackgroundTasks
from langchain.chat_models import init_chat_model
from langchain.messages import SystemMessage, HumanMessage
from loguru import logger

from app.ai.models import SMART
from app.ai.prompts.journal.suggestion import SYSTEM_MESSAGE, USER_MESSAGE
from app.ai.structured_outputs.journal.suggestion import JournalSuggestion
from app.api.schemas.journal import (
    JournalSuggestionRequest,
    JournalSuggestionResponse,
)
from app.core.context import request_id_context
from app.core.exceptions import AppException
from app.services.llm_calls_trace import log_llm_event

# Define the LLM model
_llm = init_chat_model(
    SMART,
    temperature=0.7,
    timeout=15,
    max_retries=3
)

_structured_llm = _llm.with_structured_output(JournalSuggestion, include_raw=True)

JOURNAL_LENGTH_CAP = 10000 # a hard cap on incoming journal input to protect from high token costs

async def generate_journal_suggestion_service(
    payload: JournalSuggestionRequest,
    background_tasks: BackgroundTasks
) -> JournalSuggestionResponse:
    """
    Generate a single journal guidance prompt using LLM.
    """

    request_id = request_id_context.get()
    feature_name = "journal_suggestion_n_title"
    user_id = payload.user_id

    formatted_user_message = USER_MESSAGE.format(
        journal_text=payload.journal_text[:JOURNAL_LENGTH_CAP]
    )

    messages = [
        SystemMessage(SYSTEM_MESSAGE),
        HumanMessage(formatted_user_message),
    ]

    try:
        response = await _structured_llm.ainvoke(messages)
        parsed_output: JournalSuggestion = response["parsed"]
        raw_message = response["raw"]

        # Track Unusual: LLM succeeded but returned empty or incomplete structured data
        if not parsed_output or not parsed_output.title or not parsed_output.suggestion:
            logger.warning(f"Unusual: LLM returned incomplete journal suggestion for User: {user_id}")

        # Extract token usage
        usage = getattr(raw_message, "usage_metadata", {}) or raw_message.response_metadata.get("token_usage", {})

        background_tasks.add_task(
            log_llm_event,
            {
                "request_id": request_id,
                "user_id": user_id,
                "feature": feature_name,
                "model": SMART,
                "input_tokens": usage.get("input_tokens", usage.get("prompt_tokens", 0)),
                "total_tokens": usage.get("total_tokens", 0),
                "status": "success"
            }
        )

        return JournalSuggestionResponse(title=parsed_output.title, suggestion=parsed_output.suggestion)

    except Exception as e:
        # CRITICAL: Log the full traceback for debugging on VPS
        logger.exception(f"Journal Suggestion Service Error | User: {user_id} | {str(e)}")

        await log_llm_event({
            "request_id": request_id,
            "user_id": user_id,
            "feature": feature_name,
            "model": SMART,
            "status": "failed",
            "message": str(e)
        })

        raise AppException(
            status_code=500,
            message="Oops, something went wrong...",
        )
