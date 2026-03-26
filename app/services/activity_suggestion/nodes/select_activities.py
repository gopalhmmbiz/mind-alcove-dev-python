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
    logger.info(f"NODE START: get_activity_suggestions | User: {user_id}")

    request_id = request_id_context.get()  # Accessing the context variable
    feature_name = "activity_suggestion"

    # 1. Prepare Data
    library = state.get('activity_library', [])
    activities_csv_string = convert_to_csv(library)

    if not activities_csv_string:
        logger.warning(f"Aborting AI call | User: {user_id} | Reason: Empty library.")
        return {"errors": ["No eligible activities found."]}

    logger.info(f"Preparing prompt with {len(library)} activities for User {user_id}.")

    # Use .get() to avoid potential KeyErrors if state wasn't fully initialized
    user_profile = state.get("user_profile")
    profile_json = user_profile.model_dump_json(indent=2) if user_profile else "{}"

    system_content = SYSTEM_MESSAGE.format(activity_library=activities_csv_string)
    user_content = USER_MESSAGE.format(
        user_profile=profile_json,
        user_goal=state.get("user_goal", "General Wellness"),
        user_mood=state.get("user_mood", "Okay"),
        routine_length=state.get("routine_length", "Moderate"),
    )

    messages = [
        SystemMessage(content=system_content),
        HumanMessage(content=user_content)
    ]

    try:
        # 2. Execute Async LLM Call
        logger.info(f"Invoking LLM for activity selection (Model: {SMART})...")
        response = await _structured_llm.ainvoke(messages)
        parsed_output: DailyRoutine = response["parsed"]
        raw_message = response["raw"]

        # 3. Extract Token Usage for Tracing
        usage = getattr(raw_message, "usage_metadata", {}) or raw_message.response_metadata.get("token_usage", {})
        total_tokens = usage.get("total_tokens", 0)

        await log_llm_event({
            "request_id": request_id,
            "user_id": user_id,
            "feature": feature_name,
            "model": SMART,
            "input_tokens": usage.get("input_tokens", usage.get("prompt_tokens", 0)),
            "total_tokens": total_tokens,
            "status": "success"
        })

        logger.info(f"NODE FINISHED: get_activity_suggestions | Success. Tokens: {total_tokens}")

        return {
            "activity_routine": parsed_output
        }

    except Exception as e:
        # CRITICAL: Log failure for debugging
        logger.exception(f"Node Error: get_activity_suggestions | User: {user_id} | {str(e)}")

        await log_llm_event({
            "request_id": request_id,
            "user_id": user_id,
            "feature": feature_name,
            "model": SMART,
            "status": "failed",
            "message": str(e)
        })

        return {"errors": [f"AI selection error: {str(e)}"]}
