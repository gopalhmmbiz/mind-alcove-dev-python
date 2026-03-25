from operator import add
from typing import Annotated, List, Dict, Any, TypedDict

from app.ai.structured_outputs.activity_suggestion.reconcile_patterns import UserDynamicProfile
from app.ai.structured_outputs.activity_suggestion.select_activities import DailyRoutine
from app.db.models.acvtivity_ai_logs import ActivityAiLog


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
    activity_library: List[Dict[str, Any]]
    suggestion_history: List[ActivityAiLog]
    mapping_dict: Dict[str, Any]
    activity_routine: DailyRoutine
    prev_journals: List[Dict[str, Any]]
    formatted_journal_str: str
    journal_prompt: str
    errors: Annotated[List[str], add]
