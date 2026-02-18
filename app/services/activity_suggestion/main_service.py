# import json
from typing import Dict, List, Any

import httpx
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.structured_outputs.activity_suggestion.reconcile_patterns import UserDynamicProfile
from app.api.schemas.activity_suggestion import ActivitySuggestionRequest, ActivitySuggestionResponse, Activity, DailyRoutine
from app.core.config import settings
from app.core.exceptions import AppException
# from app.db.repo.users import get_activity_profile
from app.db.session import get_db
from app.services.activity_suggestion.graph import RecommendationState, graph


async def _get_activity_library() -> List[Dict[str, Any]]:
    """
    Asynchronously fetches activity data and extracts the 'mainItems' list.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(settings.activity_list_endpoint)
            # Raise an exception for 4XX/5XX errors
            response.raise_for_status()
            data = response.json()
            if data.get("mainItems", []):
                return data.get("mainItems", [])
            else:
                raise AppException(
                    status_code=500,
                    message=f"Activity list is empty"
                )

        except httpx.HTTPStatusError as e:
            raise AppException(
                status_code=e.response.status_code,
                message=f"Error response {e.response.status_code} while fetching {settings.activity_list_endpoint}"
            )
        except Exception as e:
            raise AppException(
                status_code=500,
                message=f"An unexpected error occurred: {e}"
            )


def _format_activity_data(raw_data):
    formatted_list = []
    mapping_dict = {}

    for index, item in enumerate(raw_data, start=1):
        # Generate a simple, token-efficient unique internal ID
        internal_id = index

        # 1. Create the LLM-optimized dictionary
        formatted_item = {
            "id": internal_id,
            "name": item.get("name"),
            "description": item.get("description"),
            "goal": item.get("primary_goal"),
            "benefits": item.get("benefits"),
            "mood": item.get("core_mood"),
            "preferred_slot": item.get("daily_time"),
            "cooldown_period_in_hours": item.get("repetetion"),
            "activity_duration_in_minutes": item.get("time_val"),
            "activity_type": item.get("parent_category_name")
        }

        formatted_list.append(formatted_item)

        # 2. Map the internal ID to the full original object for later retrieval
        mapping_dict[internal_id] = item

    return formatted_list, mapping_dict


async def _filter_non_premium_activities(activities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    non_premium_activities = []
    for activity in activities:
        if activity.get("is_premium"):      # we usually get 1 or 0 in "is_premium" field
            continue
        non_premium_activities.append(activity)
    return non_premium_activities


async def generate_activity_routine(data: ActivitySuggestionRequest, db: AsyncSession = Depends(get_db)) -> ActivitySuggestionResponse:
    # profile_str = await get_activity_profile(db, data.user_id)
    # if profile_str is None:
    #     raise AppException(
    #         status_code=404,
    #         message=f"Activity profile for user {data.user_id} not found"
    #     )
    # try:
    #     profile_data = json.loads(profile_str)
    # except json.JSONDecodeError:
    #     raise AppException(
    #         status_code=500,
    #         message="Profile data is corrupted or not valid JSON"
    #     )

    activity_list = await _get_activity_library()
    if not data.is_premium:
        activity_list = await _filter_non_premium_activities(activity_list)
    clean_acitvity_list, original_mapping = _format_activity_data(activity_list)

    state = RecommendationState(
        user_id=data.user_id,
        user_mood=data.user_mood,
        user_goal=data.user_goal,
        is_premium=data.is_premium,
        routine_length=data.routine_length,
        user_profile=UserDynamicProfile(
            biography="New user, no history yet.",
            observations=[]
        ),
        activity_library=clean_acitvity_list,
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
            original_activity = original_mapping[activity["id"]]
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
        output_routine[slot] = formatted_activities
    return ActivitySuggestionResponse(routine=output_routine)
