import json
from sqlalchemy import select
from loguru import logger

from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage

from app.db.session import AsyncSessionLocal
from app.db.models.users import UserProfile
from app.ai.models import SMART
from app.ai.prompts.activity_suggeston.reconcile_patterns import SYSTEM_MESSAGE, USER_MESSAGE
from app.core.util import convert_to_csv
from app.services.activity_suggestion.state import RecommendationState
from app.ai.structured_outputs.activity_suggestion.reconcile_patterns import UserDynamicProfile


async def get_user_patterns(state: RecommendationState) -> dict:
    """
    Fetches the user's dynamic activity profile directly from the database.
    New users or errors receive a default profile with a specific biography instruction.
    """
    user_id = state.get('user_id')

    async with AsyncSessionLocal() as db:
        try:
            # 1. Fetch only the activity profile field
            stmt = (
                select(UserProfile.activity_suggestion_profile)
                .where(UserProfile.id == user_id)
            )
            result = await db.execute(stmt)
            raw_profile = result.scalar_one_or_none()

            # 2. Handle New User Case (No profile in DB)
            # This is a standard flow, so no warning log is needed.
            if not raw_profile:
                return {
                    "user_profile": UserDynamicProfile(
                        biography="User profile is unavailable. Treat user as new user.",
                        observations=[]
                    )
                }

            # 3. Parse existing profile
            try:
                profile_dict = json.loads(raw_profile)
                # We return the object to ensure consistency with the fallback cases
                return {"user_profile": UserDynamicProfile(**profile_dict)}
            except (json.JSONDecodeError, TypeError):
                # CRITICAL: Captures if the text in DB isn't valid JSON
                logger.exception(f"Critical: Corrupted JSON profile for User: {user_id}")
                return {
                    "user_profile": UserDynamicProfile(
                        biography="User profile is unavailable. Treat user as new user.",
                        observations=[]
                    )
                }

        except Exception as e:
            # CRITICAL: Captures DB connection or query failures
            logger.exception(f"Database Error: Failed to fetch user patterns for User: {user_id} | {str(e)}")
            return {
                "user_profile": UserDynamicProfile(
                    biography="User profile is unavailable. Treat user as new user.",
                    observations=[]
                ),
                "errors": "DB failure"
            }


# Define the LLM model
_llm = init_chat_model(
    SMART,
    temperature=0,
    timeout=60,
    max_retries=3
)
_structured_llm = _llm.with_structured_output(UserDynamicProfile)


async def reconcile_patterns(state: RecommendationState) -> RecommendationState:
    """
    Feeds activity logs and the existing profile to the AI to update behavioral patterns.
    """
    if state['activity_logs']:
        # 1. Prepare the CSV data
        csv_logs = convert_to_csv(state['activity_logs'])

        # 2. Prepare the existing profile as a JSON string for the prompt
        # We use .model_dump_json() for Pydantic V2 compatibility
        profile_json = state['user_profile'].model_dump_json(indent=2)

        # 3. Construct the messages
        messages = [
            SystemMessage(content=SYSTEM_MESSAGE),
            HumanMessage(content=USER_MESSAGE.format(
                activity_logs=csv_logs,
                previous_patterns=profile_json
            ))
        ]

        # 4. Invoke the AI
        # This will return a validated UserDynamicProfile object
        response: UserDynamicProfile = await _structured_llm.ainvoke(messages)

        state['user_profile'] = response

        return response
    else:
        return state
