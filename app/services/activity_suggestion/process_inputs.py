from app.services.activity_suggestion.state import RecommendationState

async def process_inputs(state: RecommendationState) -> RecommendationState:
    core_moods = ['excited', 'happy', 'loved', 'okay', 'chill', 'bored', 'sad', 'angry', 'stressed']
    if state['user_mood'].strip().lower() not in core_moods:
        state['user_mood'] = 'Excited'
    else:
        state['user_mood'] = state['user_mood'].strip().title()

    routine_length_mapping = {
        '<5': 'Quick (5–10 min)',
        '5-10': 'Quick (5–10 min)',
        '10-15': 'Quick (5–10 min)',
        '15-30': 'Moderate (15-30 min)',
        '>15': 'Moderate (15-30 min)',
        '>30': 'Extended (30+ min)'
    }
    if state['routine_length'].strip() not in routine_length_mapping:
        state['routine_length'] = routine_length_mapping['5-10']
    else:
        state['routine_length'] = routine_length_mapping[state['routine_length'].strip()]

    return state