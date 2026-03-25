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

            return {"prev_journals": [dict(row) for row in rows]}

        except SQLAlchemyError as e:
            # CRITICAL: Captures DB connection or syntax issues on VPS
            logger.exception(f"Database Error: Failed to fetch recent journals for User: {user_id}")
            await db.rollback()
            return {"prev_journals": [], "errors": "DB failure"}

        except Exception as e:
            # CRITICAL: Captures logic or mapping failures
            logger.exception(f"Unexpected Error in get_recent_journals | User: {user_id}")
            return {"prev_journals": [], "errors": "Unknown failure"}

def format_journals_for_llm(state: RecommendationState) -> dict:
    """
    Refined formatter:
    - Skips mood entries ([])
    - Skips all-null entries ({"q1": null})
    - Maps valid answers to questions with "Journal Entry" fallback.
    """
    formatted_journals = []
    user_id = state.get('user_id')

    for entry in state.get("prev_journals", []):
        raw_post = entry.get("journal_post")
        raw_ques = entry.get("questions")

        # We don't check 'if not raw_post' because [] is falsy but we need to parse it
        try:
            # 1. Parse the strings into Python objects
            # If columns are NULL in DB, we treat them as empty dicts
            post_data = json.loads(raw_post) if raw_post else {}
            ques_data = json.loads(raw_ques) if raw_ques else {}

            # 2. Logic: If post_data is a list (like []), it's a mood entry -> SKIP
            if not isinstance(post_data, dict):
                continue

            # 3. Extract legit answers and pair with questions
            daily_lines = []
            for key, answer in post_data.items():
                # Check if the answer actually contains text
                if answer is not None and str(answer).strip().lower() != "null":
                    # Pair with question or fallback
                    question = ques_data.get(key) or "Journal Entry"
                    daily_lines.append(f"- {question}: {answer}")

            # 4. If no legit answers were found (e.g., all were null), SKIP this day
            if not daily_lines:
                continue

            # 5. Store valid day
            formatted_journals.append({
                "created_at": str(entry["created_at"]),
                "journal_post": "\n".join(daily_lines)
            })

        except (json.JSONDecodeError, TypeError):
            # Capture corrupted JSON strings in the DB
            logger.exception(f"Format Error: Skipping corrupted journal entry for User: {user_id}")
            continue

    # 6. Generate the Final String for the LLM
    journal_blocks = []
    current_length = 0

    for entry in formatted_journals:
        block = f"### Date: {entry['created_at']}\n{entry['journal_post']}"

        # Check if adding this block exceeds the 10k limit
        # Adding +4 for the separator "\n\n---\n\n"
        if current_length + len(block) + 10 > CHARACTER_LIMIT:
            logger.warning(f"Unusual: Journal history capped at {CHARACTER_LIMIT} chars for User: {user_id}")
            break

        journal_blocks.append(block)
        current_length += len(block)

    final_str = "\n\n---\n\n".join(journal_blocks) if journal_blocks else "No recent journal history found for the last 7 days."

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
    request_id = request_id_context.get()
    feature_name = "prompt_of_the_day"

    # 1. Prepare Messages
    user_content = USER_MESSAGE.format(
        user_mood=state.get("user_mood", "Okay"),
        formatted_journal_str=state.get("formatted_journal_str", "No recent history.")
    )

    messages = [
        SystemMessage(content=SYSTEM_MESSAGE),
        HumanMessage(content=user_content)
    ]

    try:
        # 2. Execute LLM Call
        response = await _structured_llm.ainvoke(messages)
        parsed_output: JournalPrompt = response["parsed"]
        raw_message = response["raw"]

        if not parsed_output or not parsed_output.prompt:
            logger.warning(f"Unusual: LLM returned empty prompt for User: {user_id}")
            return {"journal_prompt": "How are you feeling in this moment?", "errors": "Empty LLM output"}

        # 3. Extract Token Usage for Tracing
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

        # 4. Update State
        return {"journal_prompt": parsed_output.prompt}

    except Exception as e:
        # CRITICAL: Log failure for debugging
        logger.exception(f"Node Error: generate_journal_prompt | User: {user_id}")

        await log_llm_event({
            "request_id": request_id,
            "user_id": user_id,
            "feature": feature_name,
            "model": SMART,
            "status": "failed",
            "message": str(e)
        })

        return {"journal_prompt": "Take a moment to write your inner thoughts.", "errors": str(e)}
