from loguru import logger
from app.services.activity_suggestion.state import RecommendationState


async def process_inputs(state: RecommendationState) -> dict:
    logger.info(f"NODE START: process_inputs | User: {state.get('user_id')}")

    if not state.get('user_mood'):
        user_mood = 'Excited'
        logger.warning(f"Invalid/Missing mood: {state.get('user_mood')}. Defaulting to 'Excited'.")
    else:
        user_mood = state['user_mood'].strip().title()

    if not state.get('user_goal'):
        user_goal = 'Calm, Awareness, Happiness'
        logger.warning(f"Invalid/Missing goal: {state.get('user_goal')}. Defaulting to Calm, Awareness, Happiness.")
    else:
        user_goal = state['user_goal'].strip().title()

    routine_length_mapping = {
        '<5': 'Quick (5–10 min)',
        '5-10': 'Quick (5–10 min)',
        '10-15': 'Quick (5–10 min)',
        '15-30': 'Moderate (15-30 min)',
        '>15': 'Moderate (15-30 min)',
        '>30': 'Extended (30+ min)'
    }
    if not state.get("routine_length") or state['routine_length'].strip() not in routine_length_mapping:
        routine_length = "Moderate (15-30 min)"
        logger.info(f"Defaulting routine length to 'Moderate (15-30 min)'.")
    else:
        routine_length = routine_length_mapping[state['routine_length'].strip()]

    logger.info(f"NODE FINISHED: process_inputs | Mood: {user_mood}, Goal: {user_goal}, Length: {routine_length}")

    return {
        "user_mood": user_mood,
        "user_goal": user_goal,
        "routine_length": routine_length
    }
