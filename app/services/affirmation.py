from fastapi import BackgroundTasks
from langchain.chat_models import init_chat_model
from langchain.messages import SystemMessage, HumanMessage

from app.ai.models import FAST
from app.ai.prompts.affirmation import SYSTEM_MESSAGE, USER_MESSAGE_TEMPLATE
from app.ai.structured_outputs.affirmation import Affirmations
from app.api.schemas.affirmation import (
    AffirmationRequest,
    AffirmationResponse,
)
from app.core.exceptions import AppException
from app.core.context import request_id_context
from app.services.llm_calls_trace import log_llm_event

# Initialize the LLM
_llm = init_chat_model(
    FAST,
    temperature=0.5,
    timeout=30,
    max_retries=3
)

# Bind structured output with include_raw=True to capture metadata
_structured_llm = _llm.with_structured_output(Affirmations, include_raw=True)


async def generate_affirmations_service(
    payload: AffirmationRequest,
    background_tasks: BackgroundTasks
) -> AffirmationResponse:
    """
    Generate affirmations using LLM based on user input.
    """
    request_id = request_id_context.get()
    feature_name = "affirmations"
    user_id = payload.user_id

    # Prepare user message
    formatted_user_message = USER_MESSAGE_TEMPLATE.format(
        user_goal=payload.user_goal
    )

    messages = [
        SystemMessage(SYSTEM_MESSAGE),
        HumanMessage(formatted_user_message),
    ]

    try:
        response = await _structured_llm.ainvoke(messages)
        parsed_output: Affirmations = response["parsed"]
        raw_message = response["raw"]

        # Extract token usage
        usage = getattr(raw_message, "usage_metadata", {}) or raw_message.response_metadata.get("token_usage", {})

        background_tasks.add_task(
            log_llm_event,
            {
                "request_id": request_id,
                "user_id": user_id,
                "feature": feature_name,
                "model": FAST,
                "input_tokens": usage.get("input_tokens", usage.get("prompt_tokens", 0)),
                "total_tokens": usage.get("total_tokens", 0),
                "status": "success"
            }
        )

        return AffirmationResponse(
            affirmations=[affirmation.text for affirmation in parsed_output.affirmations],
        )

    except Exception as e:
        await log_llm_event({
            "request_id": request_id,
            "user_id": user_id,
            "feature": feature_name,
            "model": FAST,
            "status": "failed",
            "message": str(e)
        })

        raise AppException(
            status_code=500,
            message="The AI is taking a deep breath right now. Please try again in a few moments.",
        )
