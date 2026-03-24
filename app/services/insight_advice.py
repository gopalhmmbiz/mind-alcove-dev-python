from fastapi import BackgroundTasks
from langchain.chat_models import init_chat_model
from langchain.messages import SystemMessage, HumanMessage
from loguru import logger

from app.ai.models import FAST
from app.ai.structured_outputs.insight_advice import LLMInsightOutput
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

        lines.append(f"### {mood_name} ({percentage:.1f}%)")

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
_structured_llm = _llm.with_structured_output(LLMInsightOutput, include_raw=True)


async def get_insight_advice_service(
    payload: MoodAdviceRequest,
    background_tasks: BackgroundTasks
) -> MoodAdviceResponse:
    """
    Main service logic: Formats data, calls the LLM, and logs telemetry.
    """
    request_id = request_id_context.get()
    feature_name = "mood_insight_advice"
    user_id = payload.user_id

    # 1. Prepare the LLM input
    formatted_report = format_mood_data_for_llm(payload)
    formatted_user_message = USER_MESSAGE_TEMPLATE.format(
        formatted_mood_report=formatted_report
    )

    messages = [
        SystemMessage(content=SYSTEM_MESSAGE),
        HumanMessage(content=formatted_user_message),
    ]

    try:
        # 2. Execute LLM Call
        response = await _structured_llm.ainvoke(messages)
        parsed_output: LLMInsightOutput = response["parsed"]
        raw_message = response["raw"]

        if not parsed_output or not parsed_output.advice:
            logger.warning(f"Empty AI response for User: {user_id} | Req: {request_id}")
            raise ValueError("LLM failed to generate advice.")

        # 3. Handle Token Telemetry
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

        return MoodAdviceResponse(advice=parsed_output.advice)

    except Exception as e:
        # 4. Error Handling and Failure Logging
        logger.exception(f"Insight Advice Error | User: {user_id} | {str(e)}")

        background_tasks.add_task(
            log_llm_event,
            {
                "request_id": request_id,
                "user_id": user_id,
                "feature": feature_name,
                "model": FAST,
                "status": "failed",
                "message": str(e)
            }
        )

        raise AppException(
            status_code=500,
            message="The AI is reflecting on your data. Please try again in a moment.",
        )