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
    Strictly validates that both Title and Suggestion are returned.
    """
    request_id = request_id_context.get()
    feature_name = "journal_suggestion_n_title"
    user_id = payload.user_id

    logger.info(
        f"SERVICE START: generate_journal_suggestion_service | User: {user_id} | Input: {len(payload.journal_text)} chars")

    # 1. Prepare messages with the 10k character hard cap
    capped_text = payload.journal_text[:JOURNAL_LENGTH_CAP]
    formatted_user_message = USER_MESSAGE.format(journal_text=capped_text)

    messages = [
        SystemMessage(SYSTEM_MESSAGE),
        HumanMessage(formatted_user_message),
    ]

    # Capture the prompt for the new DB column
    input_prompt_dump = "\n\n".join([f"[{msg.type.upper()}]: {msg.content}" for msg in messages])

    try:
        logger.info(f"Invoking LLM for journal suggestion | Model: {SMART} | User: {user_id}")
        response = await _structured_llm.ainvoke(messages)
        parsed_output: JournalSuggestion = response["parsed"]
        raw_message = response["raw"]

        # Extract token usage immediately (so we log cost even on validation failure)
        usage = getattr(raw_message, "usage_metadata", {}) or raw_message.response_metadata.get("token_usage", {})
        total_tokens = usage.get("total_tokens", 0)

        # 2. VALIDATION: Raise error and log if Title or Suggestion is missing
        if not parsed_output or not getattr(parsed_output, 'title', None) or not getattr(parsed_output, 'suggestion',
                                                                                         None):
            error_detail = f"Incomplete AI Output | User: {user_id} | Has Title: {bool(getattr(parsed_output, 'title', False))} | Has Suggestion: {bool(getattr(parsed_output, 'suggestion', False))}"

            # Log to terminal/file
            logger.error(error_detail)

            # Log to llm_calls_vthree table as a failure
            await log_llm_event({
                "request_id": request_id,
                "user_id": user_id,
                "feature": feature_name,
                "model": SMART,
                "input_prompt": input_prompt_dump,
                "input_tokens": usage.get("input_tokens", usage.get("prompt_tokens", 0)),
                "total_tokens": total_tokens,
                "status": "failed",
                "message": "Validation Failed: Missing Title or Suggestion in structured output."
            })

            raise AppException(
                status_code=500,
                message="The AI couldn't quite wrap its head around that entry. Please try again."
            )

        # 3. SUCCESS PATH
        background_tasks.add_task(
            log_llm_event,
            {
                "request_id": request_id,
                "user_id": user_id,
                "feature": feature_name,
                "model": SMART,
                "input_prompt": input_prompt_dump,
                "input_tokens": usage.get("input_tokens", usage.get("prompt_tokens", 0)),
                "total_tokens": total_tokens,
                "status": "success"
            }
        )

        logger.info(f"SERVICE FINISHED: generate_journal_suggestion_service | Success. Tokens: {total_tokens}")
        return JournalSuggestionResponse(title=parsed_output.title, suggestion=parsed_output.suggestion)

    except AppException:
        # Re-raise so it's not caught by the generic Exception block
        raise
    except Exception as e:
        # CRITICAL: Log full traceback for unexpected crashes (timeouts, connection errors, etc.)
        logger.exception(f"Journal Suggestion Service Error | User: {user_id} | {str(e)}")

        await log_llm_event({
            "request_id": request_id,
            "user_id": user_id,
            "feature": feature_name,
            "model": SMART,
            "input_prompt": input_prompt_dump,
            "status": "failed",
            "message": str(e)
        })

        raise AppException(
            status_code=500,
            message="Something went wrong while processing your journal. Our engineers are on it.",
        )
