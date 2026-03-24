from fastapi import BackgroundTasks
from langchain.chat_models import init_chat_model
from langchain.messages import SystemMessage, HumanMessage
from loguru import logger

from app.ai.models import FAST
from app.ai.structured_outputs.insight_advice import LLMInsightResponse
from app.api.schemas.insight_advice import (
    MoodAdviceRequest,
    MoodAdviceResponse,
)
from app.ai.prompts.insight_advice import SYSTEM_MESSAGE, USER_MESSAGE_TEMPLATE
from app.core.exceptions import AppException
from app.core.context import request_id_context
from app.services.llm_calls_trace import log_llm_event


def format_mood_data_for_llm(data: MoodAdviceRequest) -> str:
    """
    Converts structured mood data into a grouped, percentage-based
    narrative for the LLM.
    """
    # 1. Map influencers to their respective moods for easy lookup
    influencer_map = {
        inf.mood.upper(): inf.causes for inf in data.overallMoodInfluencer
    }

    lines = [f"User Mood Report ({data.startDate} to {data.endDate}):\n"]

    # 2. Iterate through counts and attach specific influencers
    for item in data.overallCounts:
        mood_name = item.mood_board_emotions.upper()
        percentage = item.total

        lines.append(f"### {mood_name}\nID: {item.mood_id}\nPercentage: {percentage:.1f}%")

        causes = influencer_map.get(mood_name, [])
        if causes:
            causes_text = ", ".join([f"{c.title} ({c.percent}%)" for c in causes])
            lines.append(f"Influencers: {causes_text}")
        else:
            lines.append("Influencers: None recorded")

        lines.append("")  # Visual separation for LLM readability

    return "\n".join(lines)


# Initialize the LLM with FAST model settings
_llm = init_chat_model(
    FAST,
    temperature=0.7,
    timeout=30,
    max_retries=3
)

# Bind structured output to capture the advice specifically
_structured_llm = _llm.with_structured_output(LLMInsightResponse, include_raw=True)


async def get_insight_advice_service(
        payload: MoodAdviceRequest,
        background_tasks: BackgroundTasks
) -> MoodAdviceResponse:
    request_id = request_id_context.get()
    feature_name = "mood_insight_advice"
    user_id = payload.user_id

    # 1. Format data using your new logic
    formatted_report = format_mood_data_for_llm(payload)

    # 2. Prepare messages
    formatted_user_message = USER_MESSAGE_TEMPLATE.format(
        formatted_mood_report=formatted_report
    )

    messages = [
        SystemMessage(content=SYSTEM_MESSAGE),
        HumanMessage(content=formatted_user_message),
    ]

    try:
        # 3. Invoke LLM
        response = await _structured_llm.ainvoke(messages)
        parsed_output: LLMInsightResponse = response["parsed"]
        raw_message = response["raw"]

        # 4. Token Tracking
        usage = getattr(raw_message, "usage_metadata", {}) or raw_message.response_metadata.get("token_usage", {})

        background_tasks.add_task(
            log_llm_event,
            {
                "request_id": request_id,
                "user_id": user_id,
                "feature": feature_name,
                "model": FAST,
                "input_tokens": usage.get("input_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
                "status": "success"
            }
        )

        # 5. Return the list of insights
        return MoodAdviceResponse(
            insights=[item.model_dump() for item in parsed_output.insights]
        )

    except Exception as e:
        logger.exception(f"Multi-Insight Service Error | User: {user_id} | {str(e)}")
        # ... (error logging task)
        raise AppException(status_code=500, message="AI is reflecting on your moods. Try again soon.")
