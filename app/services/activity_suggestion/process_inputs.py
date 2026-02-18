from app.services.activity_suggestion.state import RecommendationState

async def process_inputs(state: RecommendationState) -> dict:
    core_moods = ['excited', 'happy', 'loved', 'okay', 'chill', 'bored', 'sad', 'angry', 'stressed']
    if not state['user_mood'] or state['user_mood'].strip().lower() not in core_moods:
        user_mood = 'Excited'
    else:
        user_mood = state['user_mood'].strip().title()
    core_goals = ["calm", "focus", "resilience", "sleep", "happiness", "support", "heal", "awareness", "motivation"]

    if not state['user_goal'] or state['user_goal'].strip().lower() not in core_goals:
        user_goal = 'Calm, Awareness, Happiness'
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
    if not state["routine_length"] or state['routine_length'].strip() not in routine_length_mapping:
        routine_length = "Quick (5–10 min)"
    else:
        routine_length = routine_length_mapping[state['routine_length'].strip()]

    return {
        "user_mood": user_mood,
        "user_goal": user_goal,
        "routine_length": routine_length
    }
