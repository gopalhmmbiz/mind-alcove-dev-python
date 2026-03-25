from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.activity_suggestion import (
    ActivitySuggestionRequest,
    ActivitySuggestionResponse,
    Activity,
    DailyRoutine,
    JournalPrompt
)
from app.core.exceptions import AppException
from app.db.session import get_db
from app.services.activity_suggestion.graph import RecommendationState, graph


async def generate_activity_routine(data: ActivitySuggestionRequest, db: AsyncSession = Depends(get_db)) -> ActivitySuggestionResponse:
    state = RecommendationState(
        user_id=data.user_id,
        user_mood=data.user_mood,
        user_goal=data.user_goal,
        is_premium=data.is_premium,
        routine_length=data.routine_length
    )
    state: RecommendationState = await graph.ainvoke(state)

    if not state.get('activity_routine'):
        raise AppException(
            status_code=500,
            message='. '.join(state["errors"]) if len(state.get("errors")) > 0 else 'Internal graph error.'
        )
    daily_routine = state["activity_routine"]
    daily_routine = daily_routine.model_dump()

    output_routine = {}
    for slot in daily_routine.keys():
        slot_activities = daily_routine[slot]
        formatted_activities = []
        for activity in slot_activities:
            original_activity = state['mapping_dict'][activity["id"]]
            formatted_activity = Activity(
                id=original_activity["id"],
                name=original_activity["name"],
                time_val=original_activity["time_val"],
                benefit_tags=activity["benefits"],
                type=original_activity["type"],
                parent_category_id=original_activity["parent_category_id"],
                parent_category_name=original_activity["parent_category_name"],
            )
            formatted_activities.append(formatted_activity)
            # formatted_activities.append(JournalPrompt(prompts=[state['journal_prompt']]))
        output_routine[slot] = formatted_activities
    # daily_routine = {}
    # slots = ['morning', 'afternoon', 'evening']
    # for slot in slots:
    #     types = set()
    #     slot_list = []
    #     for activity in activity_list:
    #         if activity["type"] not in types:
    #             types.add(activity["type"])
    #             slot_list.append(
    #                 Activity(
    #                     id=activity["id"],
    #                     name=activity["name"],
    #                     time_val=activity["time_val"],
    #                     benefit_tags=['Mental Peace', 'Satisfaction'],
    #                     type=activity['type'],
    #                     parent_category_id=activity["parent_category_id"],
    #                     parent_category_name=activity["parent_category_name"],
    #                 )
    #             )
    #     slot_list.append(JournalPrompt(prompts=["How about journaling your recent achievements?", "Write about your recent learnings."]))
    #     daily_routine[slot] = slot_list

    return ActivitySuggestionResponse(routine=output_routine)
