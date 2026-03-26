import json
from sqlalchemy import select, update
from loguru import logger

from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage

from app.core.context import request_id_context
from app.db.session import AsyncSessionLocal
from app.db.models.users import UserProfile
from app.ai.models import SMART
from app.ai.prompts.activity_suggeston.reconcile_patterns import SYSTEM_MESSAGE, USER_MESSAGE
from app.services.activity_suggestion.state import RecommendationState
from app.ai.structured_outputs.activity_suggestion.reconcile_patterns import UserDynamicProfile
from app.services.llm_calls_trace import log_llm_event


async def get_user_patterns(state: RecommendationState) -> dict:
    """
    Fetches the user's dynamic activity profile directly from the database.
    New users or errors receive a default profile with a specific biography instruction.
    """
    user_id = state.get('user_id')
    logger.info(f"NODE START: get_user_patterns | User: {user_id}")

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
            if not raw_profile:
                logger.info(f"NODE FINISHED: get_user_patterns | User: {user_id}. | No behavioural profile found for user.")
                return {
                    "user_profile": UserDynamicProfile(
                        biography="User profile is unavailable. Treat user as fresh user.",
                        observations=[]
                    )
                }

            # 3. Parse existing profile
            try:
                profile_dict = json.loads(raw_profile)
                profile_obj = UserDynamicProfile(**profile_dict)

                logger.info(
                    f"Profile Loaded: Successfully retrieved {len(profile_obj.observations)} patterns for User {user_id}.")

                logger.info(f"NODE FINISHED: get_user_patterns | User: {user_id}")
                return {
                    "user_profile": profile_obj
                }

            except (json.JSONDecodeError, TypeError):
                logger.exception(f"Critical: Corrupted JSON profile for User, treating as fresh user | User: {user_id}")
                return {
                    "user_profile": UserDynamicProfile(
                        biography="User profile is unavailable. Treat user as fresh user.",
                        observations=[]
                    )
                }

        except Exception as e:
            logger.exception(f"Database Error: Failed to fetch user patterns for User: {user_id} | {str(e)}")
            return {
                "user_profile": UserDynamicProfile(
                    biography="User profile is unavailable. Treat user as fresh user.",
                    observations=[]
                ),
                "errors": ["DB failure"]
            }


# Define the LLM model
_llm = init_chat_model(
    SMART,
    temperature=0,
    timeout=60,
    max_retries=3
)
_structured_llm = _llm.with_structured_output(UserDynamicProfile, include_raw=True)


async def reconcile_patterns(state: RecommendationState) -> dict:
    """
    Reconciles yesterday's activity logs with the existing user profile.
    Updates behavioral patterns and stability scores.
    """
    user_id = state.get("user_id")
    logger.info(f"NODE START: reconcile_patterns | User: {user_id}")

    # 1. Early Exit Logic
    activity_logs = state.get("formatted_activity_logs", "").strip()
    current_profile = state.get("user_profile")

    if not activity_logs:
        logger.info(f"NODE SKIP: reconcile_patterns | User: {user_id} | No activity logs available.")
        return {
            "user_profile": current_profile
        }

    request_id = request_id_context.get()
    feature_name = "behavioral_profiling"

    # 2. Prepare Messages
    previous_patterns_json = current_profile.model_dump_json(indent=2)

    messages = [
        SystemMessage(content=SYSTEM_MESSAGE),
        HumanMessage(content=USER_MESSAGE.format(
            activity_logs=activity_logs,
            previous_patterns=previous_patterns_json
        ))
    ]

    try:
        # 3. Invoke LLM
        logger.info(f"Invoking LLM for profiling reconciliation for User {user_id}...")
        response = await _structured_llm.ainvoke(messages)
        parsed_output: UserDynamicProfile = response["parsed"]
        raw_message = response["raw"]

        # 4. Extract Token Usage for Tracing
        usage = getattr(raw_message, "usage_metadata", {}) or raw_message.response_metadata.get("token_usage", {})

        await log_llm_event({
            "request_id": request_id,
            "user_id": user_id,
            "feature": feature_name,
            "model": SMART,
            "input_tokens": usage.get("input_tokens", usage.get("prompt_tokens", 0)),
            "total_tokens": usage.get("total_tokens", 0),
            "status": "success"
        })

        logger.info(
            f"NODE FINISHED: reconcile_patterns | Profile updated with {len(parsed_output.observations)} observations.")

        # 5. Update State with the new reconciled profile
        return {"user_profile": parsed_output}

    except Exception as e:
        logger.exception(f"Node Error: reconcile_patterns | User: {user_id} | {str(e)}")

        await log_llm_event({
            "request_id": request_id,
            "user_id": user_id,
            "feature": feature_name,
            "model": SMART,
            "status": "failed",
            "message": str(e)
        })

        # Return the existing profile so the user data isn't lost on error
        return {"user_profile": current_profile, "errors": [f"Profiling error: {str(e)}"]}


def format_previous_activity_logs(state: RecommendationState) -> dict:
    """
    Converts previous day's performance data into a Markdown-style log.
    """
    user_id = state.get("user_id")
    logger.info(f"NODE START: format_previous_activity_logs | User: {user_id}")

    history = state.get("suggestion_history", [])
    if not history:
        logger.info(f"NODE SKIPPED: format_previous_activity_logs | No history found for User {user_id}. Skipping log formatting.")
        return {"formatted_activity_logs": ""}

    # latest_log is 'yesterday' due to desc(created_at) sorting in fetch node
    latest_log = history[0]

    # 1. Robust JSON Decoding
    performed_raw = latest_log.performed
    if not performed_raw:
        logger.warning(f"Performed column is empty for User {user_id}. Returning empty log string.")
        return {"formatted_activity_logs": None}

    try:
        performed_data = json.loads(performed_raw) if isinstance(performed_raw, str) else performed_raw
        if isinstance(performed_data, str):
            performed_data = json.loads(performed_data)
    except Exception as e:
        logger.error(f"Failed to decode performed column for User {user_id}: {e}")
        return {"formatted_activity_logs": None}

    # 2. Build the Markdown Log
    markdown_lines = []

    for slot in ["morning", "afternoon", "evening"]:
        activities = performed_data.get(slot, [])
        if not activities:
            continue

        markdown_lines.append(f"### {slot.capitalize()}")

        for act in activities:
            # EXCLUSION: Skip daily_journal_prompts
            if act.get("type") == "daily_journal_prompts":
                continue

            status = act.get("performance_status", "Not started")
            name = act.get("name", None)
            category = act.get("parent_category_name", None)
            if not name or not category:
                continue
            duration = f"{act.get('time_val', '0')}m"

            # Formatting logic: Bold the status if attempted
            status_display = f"**[{status.capitalize()}]**" if status.lower() != "not started" else f"[{status.capitalize()}]"

            # Base line with name, category, and duration (included for all)
            line = f"- {status_display} {name} ({category}) | {duration}"

            # Append mood shift if available
            pre = act.get("pre_mood", None)
            post = act.get("post_mood", None)
            if pre and post:
                line += f" | Mood: {pre} → {post}"

            markdown_lines.append(line)

        markdown_lines.append("")  # Spacer

    formatted_log = "\n".join(markdown_lines).strip()

    if not formatted_log:
        logger.info(f"Log generated but empty (likely only journal prompts existed).")
    else:
        logger.info(f"Successfully formatted logs for User {user_id} ({len(markdown_lines)} lines).")

    logger.info(f"NODE FINISHED: format_previous_activity_logs | User: {user_id}")

    return {
        "formatted_activity_logs": formatted_log if formatted_log else ""
    }


async def persist_user_patterns(state: RecommendationState) -> dict:
    """
    Saves the updated UserDynamicProfile back to the database.
    This ensures behavioral learning persists across sessions.
    """
    user_id = state.get("user_id")
    logger.info(f"NODE START: persist_user_patterns | User: {user_id}")

    updated_profile = state.get("user_profile")

    if not updated_profile:
        logger.warning(f"NODE SKIP: persist_user_patterns | No profile found in state for User {user_id}.")
        return {}

    async with AsyncSessionLocal() as db:
        try:
            # 1. Serialize Pydantic model to JSON string
            profile_json = updated_profile.model_dump_json()

            # 2. Perform the Update
            stmt = (
                update(UserProfile)
                .where(UserProfile.id == user_id)
                .values(activity_suggestion_profile=profile_json)
            )

            await db.execute(stmt)
            await db.commit()

            logger.info(f"NODE FINISHED: persist_user_patterns | Successfully saved new profile data for User {user_id}.")
            return {}

        except Exception as e:
            logger.exception(f"Database Error: Failed to persist patterns for User: {user_id} | {str(e)} | Lost Profile Data: {profile_json}")
            await db.rollback()
            return {"errors": [f"Database persistence failure: {str(e)}"]}
