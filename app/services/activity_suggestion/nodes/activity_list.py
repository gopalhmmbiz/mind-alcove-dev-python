import json
import random
import re
from datetime import datetime, timezone, timedelta

import httpx
from loguru import logger
from sqlalchemy import select, desc

from app.core.config import settings
from app.core.exceptions import AppException
from app.db.models.acvtivity_ai_logs import ActivityAiLog
from app.db.session import AsyncSessionLocal
from app.services.activity_suggestion.state import RecommendationState


def generate_activity_key(activity_details: dict) -> str:
    """
    Generates a unique key: type__id
    Example: type='guidedbreathing', id=38
    Result: "guidedbreathing__38"
    """
    # 1. Get the type and id (defaults to 'unknown' and '0' if missing)
    raw_type = str(activity_details.get("type", "unknown")).lower()
    raw_id = str(activity_details.get("id", "0"))

    # 2. Clean the type (remove non-alphanumeric chars/whitespaces)
    # clean_type = re.sub(r'[^a-zA-Z0-9]', '', raw_type)

    # 3. Return the stable key
    return f"{raw_type}__{raw_id}"


async def get_activity_library(state: RecommendationState) -> dict:
    """
    Asynchronously fetches the activity library from the Laravel service,
    generates unique keys for each activity, and deduplicates the list.
    """
    logger.info(f"NODE START: get_activity_library | User: {state.get('user_id')}")
    url = f'{settings.laravel_base_url}/storage/ai-sync/ai-sync.json'

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            # Raise exception for 4XX/5XX responses
            response.raise_for_status()

            data = response.json()
            main_items = data.get("mainItems", [])

            if not main_items:
                logger.error(f"Activity list fetch successful but 'mainItems' is missing or empty at {url}")
                raise AppException(
                    status_code=500,
                    message="Activity list is empty."
                )

            logger.info(f"Fetched {len(main_items)} raw items from library sync.")

            # Filtering non-premium activities
            if not state.get('is_premium', False):
                initial_count = len(main_items)
                main_items = [activity for activity in main_items if not activity.get('is_premium', False)]
                logger.info(f"Non-premium user: Filtered out {initial_count - len(main_items)} premium activities.")

            store = set()
            unique_activity_library = []

            for activity_details in main_items:
                # Generate key using the provided helper
                activity_key = generate_activity_key(activity_details)

                if activity_key not in store:
                    store.add(activity_key)
                    # Merge the generated key into the activity object
                    unique_activity_library.append({"activity_key": activity_key, **activity_details})
                else:
                    logger.warning(
                        f"Duplicate activity found: {activity_key}. Skipping ID: {activity_details.get('id')}")

            logger.info(f"NODE FINISHED: get_activity_library | Total Unique Activities: {len(unique_activity_library)}")
            return {
                'activity_library': unique_activity_library
            }

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP {e.response.status_code} error fetching library: {url}")
            raise AppException(
                status_code=e.response.status_code,
                message=f"Activity library sync error: {e.response.status_code}"
            )
        except Exception as e:
            # logger.exception automatically captures the full stack trace for debugging
            logger.exception(f"Unexpected error in get_activity_library: {str(e)}")
            raise AppException(
                status_code=500,
                message=f"An unexpected error occurred during library fetch: {e}"
            )


async def fetch_suggestion_history(state: RecommendationState) -> dict:
    """
    Fetches raw suggestion logs for the last 7 days using a local async session.
    Stores the full objects in the 'suggestion_history' state key for downstream processing.
    """
    user_id = state.get("user_id")
    logger.info(f"NODE START: fetch_suggestion_history | User: {user_id}")

    lookback_date = datetime.now(timezone.utc) - timedelta(days=7)

    async with AsyncSessionLocal() as db:
        try:
            # Querying the full ActivityAiLog objects to ensure all metadata (created_at, suggested) is available
            query = (
                select(ActivityAiLog)
                .where(ActivityAiLog.user_id == user_id)
                .where(ActivityAiLog.created_at >= lookback_date)
                .order_by(desc(ActivityAiLog.created_at))
            )

            result = await db.execute(query)
            # Scalars used to get the model instances directly
            logs = list(result.scalars().all())

            if not logs:
                logger.warning(f"No suggestion history found for user_id: {user_id} in the last 7 days.")
                return {
                    "suggestion_history": []
                }

            logger.info(
                f"NODE FINISHED: fetch_suggestion_history | Successfully retrieved {len(logs)} days of history.")
            return {
                "suggestion_history": logs
            }

        except Exception as e:
            # loguru.exception captures the full stack trace automatically
            logger.exception(f"Failed to fetch suggestion history for user {user_id}: {str(e)}")
            # Return an empty list to prevent the graph from breaking in subsequent nodes
            return {
                "suggestion_history": [],
                "errors": [str(e)]
            }


async def filter_cooldown_activities(state: RecommendationState) -> dict:
    """
    Uses 7-day history to filter activities currently on cooldown.
    """
    user_id = state.get("user_id")
    logger.info(f"NODE START: filter_cooldown_activities | User: {user_id}")

    now = datetime.now(timezone.utc)
    suggestion_history = state.get("suggestion_history", [])
    activity_library = state.get("activity_library", [])

    if not suggestion_history:
        logger.info(
            f"NODE SKIPPED: filter_cooldown_activities | Cooldown skip due to no suggestion history. Returning Activity library as is.")
        return {"activity_library": activity_library}

    slot_offsets = {"morning": 8, "afternoon": 14, "evening": 20}
    history_map = {}

    # PHASE 1: Build the 7-Day Truth Map
    for log in suggestion_history:
        base_date = datetime.combine(log.date, datetime.min.time()).replace(tzinfo=timezone.utc)

        suggested_raw = log.suggested
        if not suggested_raw:
            continue

        try:
            suggested_data = json.loads(suggested_raw) if isinstance(suggested_raw, str) else suggested_raw
            if isinstance(suggested_data, str):
                suggested_data = json.loads(suggested_data)
        except Exception:
            logger.warning(f"Could not parse one of suggested activity routine data. | Date: {log.date} | Data: {suggested_raw}")
            continue

        for slot, offset in slot_offsets.items():
            activities = suggested_data.get(slot, [])
            if not isinstance(activities, list):
                continue

            effective_ts = base_date + timedelta(hours=offset)

            for act in activities:
                key = generate_activity_key(act)
                if key not in history_map or effective_ts > history_map[key]:
                    history_map[key] = effective_ts

    # PHASE 2: Filter the Library
    filtered_library = []
    for activity in activity_library:
        key = activity.get("activity_key")

        # Regex to extract numeric hours from strings like '12 hrs' or '24'
        raw_rep = str(activity.get("repetetion") or "24")
        match = re.search(r"(\d+)", raw_rep)
        cooldown_hours = int(match.group(1)) if match else 24

        if key in history_map:
            hours_passed = (now - history_map[key]).total_seconds() / 3600
            if hours_passed < cooldown_hours:
                continue

        filtered_library.append(activity)

    if len(filtered_library) < 15:
        logger.warning(f"Shortage: Only {len(filtered_library)} items passed cooldown. Refilling randomly.")

        # Set for O(1) lookup speed
        existing_keys = {act.get("activity_key") for act in filtered_library}
        iter_count = 0

        while len(filtered_library) < 30 and iter_count < 100:
            iter_count += 1
            activity = random.choice(activity_library)
            if activity.get("activity_key") not in existing_keys:
                filtered_library.append(activity)
                existing_keys.add(activity.get("activity_key"))

        logger.info(f"Refill complete. Added {len(filtered_library) - (len(existing_keys) - iter_count)} items.")

    logger.info(
        f"NODE FINISHED: filter_cooldown_activities | Filtered out {len(activity_library) - len(filtered_library)} items. {len(filtered_library)} remaining.")

    return {"activity_library": filtered_library}


def format_activity_list(state: "RecommendationState") -> dict:
    """
    Final formatting of the filtered library for the LLM.
    Assigns temporary IDs and creates a mapping_dict for post-processing reconstruction.
    """
    user_id = state.get("user_id")
    logger.info(f"NODE START: format_activity_list | User: {user_id}")

    filtered_library = state.get('activity_library', [])
    formatted_list = []
    mapping_dict = {}

    if not filtered_library:
        logger.warning(f"User: {user_id} | No activities remaining in library after filtering.")
        return {
            'activity_library': [],
            'mapping_dict': {}
        }

    for index, item in enumerate(filtered_library, start=1):
        # Numeric IDs are highly reliable for LLM retrieval
        temp_id = index

        # 1. LLM-Optimized Dictionary (Short keys save tokens)
        formatted_item = {
            "id": temp_id,
            "name": item.get("name"),
            "desc": item.get("description"),
            "goal": item.get("primary_goal"),
            "benefits": item.get("benefits"),
            "mood": item.get("core_mood"),
            "slot": item.get("daily_time"),
            "cooldown_hrs": item.get("repetetion"),
            "duration_mins": item.get("time_val"),
            "category": item.get("parent_category_name")
        }

        formatted_list.append(formatted_item)

        # 2. Map the temp_id to the full original object (including the activity_key)
        # This allows the final node to reconstruct the full JSON for the frontend
        mapping_dict[temp_id] = item

    logger.info(f"NODE FINISHED: format_activity_list | Prepared {len(formatted_list)} items for LLM.")

    return {
        'activity_library': formatted_list,
        'mapping_dict': mapping_dict
    }
