import json
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, desc, func
from sqlalchemy.exc import SQLAlchemyError
from loguru import logger
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage

from app.ai.models import SMART
from app.db.session import AsyncSessionLocal
from app.db.models.journal import JournalPost
from app.services.activity_suggestion.state import RecommendationState
from app.ai.prompts.journal.daily_prompt import SYSTEM_MESSAGE, USER_MESSAGE
from app.ai.structured_outputs.journal.daily_prompt import JournalPrompt
from app.services.llm_calls_trace import log_llm_event
from app.core.context import request_id_context


JOURNAL_LOOKUP_DAYS = 7
CHARACTER_LIMIT = 10000

async def get_recent_journals(state: RecommendationState) -> dict:
    """
    Fetches the last 7 days of journals including questions and answers.
    Order: Latest -> Oldest.
    """
    user_id = state.get('user_id')
    logger.info(f"NODE START: get_recent_journals | User: {user_id}")

    async with AsyncSessionLocal() as db:
        try:
            threshold_date = datetime.now(timezone.utc) - timedelta(days=JOURNAL_LOOKUP_DAYS)

            # We now select 'post_questions' to ensure the LLM understands the context of each answer
            query = (
                select(
                    func.date(JournalPost.created_at).label("created_at"),
                    JournalPost.post.label("journal_post"),
                    JournalPost.post_questions.label("questions")
                )
                .where(JournalPost.user_id == user_id)
                .where(JournalPost.created_at >= threshold_date)
                .order_by(desc(JournalPost.created_at))
            )

            result = await db.execute(query)
            rows = result.mappings().all()

            if not rows:
                logger.info(f"Note: No recent journals found for User: {user_id} in the last {JOURNAL_LOOKUP_DAYS} days.")
            else:
                logger.info(f"Successfully retrieved {len(rows)} journal entries for User: {user_id}.")

            logger.info(f"NODE FINISHED: get_recent_journals | User: {user_id}")
            return {"prev_journals": [dict(row) for row in rows]}

        except SQLAlchemyError as e:
            # CRITICAL: Captures DB connection or syntax issues on VPS
            logger.exception(f"Database Error: Failed to fetch recent journals for User: {user_id}")
            await db.rollback()
            return {"prev_journals": [], "errors": ["DB failure"]}

        except Exception as e:
            # CRITICAL: Captures logic or mapping failures
            logger.exception(f"Unexpected Error in get_recent_journals | User: {user_id}")
            return {"prev_journals": [], "errors": ["Unknown failure"]}


def format_journals_for_llm(state: RecommendationState) -> dict:
    """
    Refined formatter:
    - Skips mood entries ([])
    - Skips all-null entries ({"q1": null})
    - Maps valid answers to questions with "Journal Entry" fallback.
    """
    user_id = state.get('user_id')
    logger.info(f"NODE START: format_journals_for_llm | User: {user_id}")

    formatted_journals = []
    skipped_mood_entries = 0
    skipped_empty_entries = 0

    for entry in state.get("prev_journals", []):
        raw_post = entry.get("journal_post")
        raw_ques = entry.get("questions")

        try:
            # 1. Parse the strings into Python objects
            post_data = json.loads(raw_post) if raw_post else {}
            ques_data = json.loads(raw_ques) if raw_ques else {}

            # 2. Logic: If post_data is a list (like []), it's a mood entry -> SKIP
            if not isinstance(post_data, dict):
                skipped_mood_entries += 1
                continue

            # 3. Extract legit answers and pair with questions
            daily_lines = []
            for key, answer in post_data.items():
                if answer is not None and str(answer).strip().lower() != "null":
                    question = ques_data.get(key) or "Journal Entry"
                    daily_lines.append(f"- {question}: {answer}")

            # 4. If no legit answers were found, SKIP this day
            if not daily_lines:
                skipped_empty_entries += 1
                continue

            # 5. Store valid day
            formatted_journals.append({
                "created_at": str(entry["created_at"]),
                "journal_post": "\n".join(daily_lines)
            })

        except (json.JSONDecodeError, TypeError):
            logger.exception(f"Format Error: Skipping corrupted journal entry for User: {user_id}")
            continue

    # 6. Generate the Final String for the LLM
    journal_blocks = []
    current_length = 0

    for entry in formatted_journals:
        block = f"### Date: {entry['created_at']}\n{entry['journal_post']}"

        if current_length + len(block) + 10 > CHARACTER_LIMIT:
            logger.warning(f"Unusual: Journal history capped at {CHARACTER_LIMIT} chars for User: {user_id}")
            break

        journal_blocks.append(block)
        current_length += len(block)

    final_str = "\n\n---\n\n".join(
        journal_blocks) if journal_blocks else "No recent journal history found for the last 7 days."

    logger.info(
        f"Journal Formatting Summary | Valid Days: {len(journal_blocks)} | Skipped Moods: {skipped_mood_entries} | Skipped Empty: {skipped_empty_entries}")
    logger.info(f"NODE FINISHED: format_journals_for_llm | User: {user_id}")

    return {
        "prev_journals": formatted_journals,
        "formatted_journal_str": final_str
    }


# Initialize LLM with structured output + raw message access for tracing
_llm = init_chat_model(
    SMART,
    temperature=0.7,
    timeout=30,
    max_retries=3
)

# include_raw=True returns a dict: {"parsed": JournalPrompt, "raw": BaseMessage}
_structured_llm = _llm.with_structured_output(JournalPrompt, include_raw=True)


async def generate_journal_prompt(state: RecommendationState) -> dict:
    """
    Generates a single personalized journal encouragement prompt.
    Incorporates logging, LLM tracing, and character limits.
    """
    user_id = state.get("user_id")
    logger.info(f"NODE START: generate_journal_prompt | User: {user_id}")

    request_id = request_id_context.get()
    feature_name = "prompt_of_the_day"

    # 1. Prepare Messages
    user_mood = state.get("user_mood", "Okay")
    journal_str = state.get("formatted_journal_str", "No recent history.")

    user_content = USER_MESSAGE.format(
        user_mood=user_mood,
        formatted_journal_str=journal_str
    )

    messages = [
        SystemMessage(content=SYSTEM_MESSAGE),
        HumanMessage(content=user_content)
    ]

    try:
        # 2. Execute LLM Call
        logger.info(f"Invoking LLM for journal prompt generation | User: {user_id}")
        response = await _structured_llm.ainvoke(messages)
        parsed_output: JournalPrompt = response["parsed"]
        raw_message = response["raw"]

        if not parsed_output or not parsed_output.prompt:
            logger.warning(f"Unusual: LLM returned empty prompt for User: {user_id}")
            return {"journal_prompt": "How are you feeling in this moment?", "errors": ["Empty LLM output"]}

        # 3. Extract Token Usage for Tracing
        usage = getattr(raw_message, "usage_metadata", {}) or raw_message.response_metadata.get("token_usage", {})
        total_tokens = usage.get("total_tokens", 0)

        await log_llm_event({
            "request_id": request_id,
            "user_id": user_id,
            "feature": feature_name,
            "model": SMART,
            "input_tokens": usage.get("input_tokens", usage.get("prompt_tokens", 0)),
            "total_tokens": total_tokens,
            "status": "success"
        })

        logger.info(
            f"NODE FINISHED: generate_journal_prompt | Success. Tokens: {total_tokens} | Prompt: '{parsed_output.prompt[:50]}...'")

        # 4. Update State
        return {"journal_prompt": parsed_output.prompt}

    except Exception as e:
        # CRITICAL: Log failure for debugging
        logger.exception(f"Node Error: generate_journal_prompt | User: {user_id} | {str(e)}")

        await log_llm_event({
            "request_id": request_id,
            "user_id": user_id,
            "feature": feature_name,
            "model": SMART,
            "status": "failed",
            "message": str(e)
        })

        return {"journal_prompt": "Take a moment to write your inner thoughts.", "errors": [str(e)]}
