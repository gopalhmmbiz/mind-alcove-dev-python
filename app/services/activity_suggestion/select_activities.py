import csv
from io import StringIO
from typing import List, Dict, Any

from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage

from app.ai.models import SMART
from app.ai.structured_outputs.activity_suggestion.reconcile_patterns import BehavioralObservation, UserDynamicProfile
from app.ai.structured_outputs.activity_suggestion.select_activities import DailyRoutine
from app.ai.prompts.activity_suggeston.select_activities import SYSTEM_MESSAGE, USER_MESSAGE

from dotenv import load_dotenv

from app.core.util import convert_to_csv
from app.services.activity_suggestion.state import RecommendationState

load_dotenv()

# Define the LLM model
_llm = init_chat_model(
    SMART,
    temperature=0,
    timeout=60,
    max_retries=3
)
_structured_llm = _llm.with_structured_output(DailyRoutine)


def get_activity_suggestions(
        state: RecommendationState,
) -> RecommendationState:
    """
    The main recommendation service.
    """
    # CSV conversion
    activities_csv_string = convert_to_csv(state['activity_library'])

    # Inject the library into the System Message
    system_content = SYSTEM_MESSAGE.format(activity_library=activities_csv_string)

    # Inject user context into the Human Message
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

    # LLM Call
    try:
        response: DailyRoutine = _structured_llm.invoke(messages)
        state["activity_routine"] = response
    except Exception as e:
        state["errors"].append(str(e))

    return state
