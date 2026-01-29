from langchain.chat_models import init_chat_model
from langchain.messages import SystemMessage, HumanMessage

from app.ai.models import FAST
from app.ai.prompts.affirmation import SYSTEM_MESSAGE, USER_MESSAGE_TEMPLATE
from app.ai.structured_outputs.affirmation import Affirmations
from app.api.schemas.affirmation import (
    AffirmationRequest,
    AffirmationResponse,
)


# Define the LLM model
_llm = init_chat_model(
    FAST,
    temperature=0.5,
    timeout=15,
    max_retries=3
)

# Bind structured output
_structured_llm = _llm.with_structured_output(Affirmations)

async def generate_affirmations_service(
    payload: AffirmationRequest,
) -> AffirmationResponse:
    """
    Generate affirmations using LLM based on user input.
    """

    # Prepare user message
    formatted_user_message = USER_MESSAGE_TEMPLATE.format(
        user_goal=payload.user_goal
    )

    messages = [
        SystemMessage(SYSTEM_MESSAGE),
        HumanMessage(formatted_user_message),
    ]

    # Invoke model asynchronously
    response: Affirmations = await _structured_llm.ainvoke(messages)

    # Map structured output to API response
    return AffirmationResponse(
        affirmations=[affirmation.text for affirmation in response.affirmations],
    )
