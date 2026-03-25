from loguru import logger
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage

from app.ai.models import SMART
from app.ai.structured_outputs.activity_suggestion.select_activities import DailyRoutine
from app.ai.prompts.activity_suggeston.select_activities import SYSTEM_MESSAGE, USER_MESSAGE
from app.core.context import request_id_context
from app.core.util import convert_to_csv
from app.services.activity_suggestion.state import RecommendationState
from app.services.llm_calls_trace import log_llm_event



# Initialize model with raw output enabled
_llm = init_chat_model(
    SMART,
    temperature=0,
    timeout=60,
    max_retries=3
)
_structured_llm = _llm.with_structured_output(DailyRoutine, include_raw=True)


async def get_activity_suggestions(state: RecommendationState) -> dict:
    """
    Main recommendation service. Selects activities based on user context
    and library availability, tracking tokens via log_llm_event.
    """
    user_id = state.get("user_id")
    request_id = request_id_context.get()  # Accessing the context variable
    feature_name = "activity_suggestion"

    # 1. Prepare Data
    activities_csv_string = convert_to_csv(state.get('activity_library', []))

    if not activities_csv_string:
        logger.warning(f"Aborting AI call | User: {user_id} | Reason: Empty filtered library.")
        return {"errors": "No eligible activities found."}

    system_content = SYSTEM_MESSAGE.format(activity_library=activities_csv_string)
    user_content = USER_MESSAGE.format(
        user_profile=state["user_profile"].model_dump_json(indent=2),
        user_goal=state["user_goal"],
        user_mood=state["user_mood"],
        routine_length=state["routine_length"],
    )

    messages = [
        SystemMessage(content=system_content),
        HumanMessage(content=user_content)
    ]

    try:
        # 2. Execute Async LLM Call
        response = await _structured_llm.ainvoke(messages)
        parsed_output: DailyRoutine = response["parsed"]
        raw_message = response["raw"]

        # 3. Extract Token Usage for Tracing
        usage = getattr(raw_message, "usage_metadata", {}) or raw_message.response_metadata.get("token_usage", {})

        await log_llm_event({
            "request_id": request_id,
            "user_id": user_id,
            "feature": feature_name,
            "model": SMART,
            "input_tokens": usage.get("input_tokens", usage.get("prompt_tokens", 0)),
            "total_tokens": usage.get("total_tokens", 0),
            "status": "success"
        })

        return {
            "activity_routine": parsed_output,
            "tokens_used": usage.get("total_tokens", 0)
        }

    except Exception as e:
        # CRITICAL: Log failure for debugging
        logger.exception(f"Node Error: get_activity_suggestions | User: {user_id}")

        await log_llm_event({
            "request_id": request_id,
            "user_id": user_id,
            "feature": feature_name,
            "model": SMART,
            "status": "failed",
            "message": str(e)
        })

        return {"errors": f"AI selection error: {str(e)}"}
