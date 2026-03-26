from loguru import logger
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


async def generate_activity_routine(data: ActivitySuggestionRequest,
                                    db: AsyncSession = Depends(get_db)) -> ActivitySuggestionResponse:
    user_id = data.user_id
    logger.info(
        f"SERVICE START: generate_activity_routine | User: {user_id} | Mood: {data.user_mood} | Goal: {data.user_goal}")

    # 1. Initialize State
    state = RecommendationState(
        user_id=user_id,
        user_mood=data.user_mood,
        user_goal=data.user_goal,
        is_premium=data.is_premium,
        routine_length=data.routine_length
    )

    try:
        # 2. Invoke Graph
        logger.info(f"Invoking Activity Recommendation Graph for User: {user_id}")
        state: RecommendationState = await graph.ainvoke(state)

        # 3. Handle Potential Graph Failures
        if not state.get('activity_routine'):
            errors = state.get("errors", [])
            error_msg = '. '.join(errors) if errors else 'Internal graph error.'
            logger.error(f"Graph failed for User {user_id}: {error_msg}")
            raise AppException(
                status_code=500,
                message=error_msg
            )

        # 4. Reconstruct Routine from Mapping Dict
        daily_routine = state["activity_routine"].model_dump()
        mapping_dict = state.get('mapping_dict', {})
        output_routine = {}

        logger.info(f"Reconstructing final routine for User {user_id} using mapping_dict.")

        for slot, slot_activities in daily_routine.items():
            formatted_activities = []

            for activity in slot_activities:
                temp_id = activity.get("id")

                # SAFETY CHECK: Ensure the LLM didn't return an invalid ID
                if temp_id not in mapping_dict:
                    logger.warning(
                        f"LLM Hallucination: Activity ID {temp_id} not found in mapping_dict for User {user_id}. Skipping.")
                    continue

                original_activity = mapping_dict[temp_id]

                # Create final Pydantic model for response
                formatted_activity = Activity(
                    id=original_activity.get("id"),
                    name=original_activity.get("name"),
                    time_val=original_activity.get("time_val"),
                    benefit_tags=activity.get("benefits", []),  # Taking from LLM's tailored response
                    type=original_activity.get("type"),
                    parent_category_id=original_activity.get("parent_category_id"),
                    parent_category_name=original_activity.get("parent_category_name"),
                )
                formatted_activities.append(formatted_activity)

            output_routine[slot] = formatted_activities
            logger.info(f"Slot '{slot.capitalize()}' prepared with {len(formatted_activities)} activities.")

        logger.info(f"SERVICE FINISHED: generate_activity_routine | Successfully generated routine for User: {user_id}")
        return ActivitySuggestionResponse(routine=output_routine)

    except AppException:
        # Re-raise AppExceptions as they are already handled
        raise
    except Exception as e:
        logger.exception(f"Unexpected Critical Error in generate_activity_routine | User: {user_id} | {str(e)}")
        raise AppException(status_code=500, message="An unexpected error occurred while generating your routine.")

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