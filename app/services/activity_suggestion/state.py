from operator import add
from typing import Annotated, List, Dict, Any, TypedDict

from app.ai.structured_outputs.activity_suggestion.reconcile_patterns import UserDynamicProfile
from app.ai.structured_outputs.activity_suggestion.select_activities import DailyRoutine


class RecommendationState(TypedDict, total=False):
    """
    The LangGraph state for the Mind Alcove recommendation engine.
    'total=False' allows nodes to return partial state updates.
    """
    user_id: str
    is_premium: bool
    user_mood: str
    user_goal: str
    routine_length: str
    user_profile: UserDynamicProfile
    activity_logs: List[Dict[str, Any]]
    activity_library: List[Dict[str, Any]]
    activity_routine: DailyRoutine
    errors: Annotated[List[str], add]
