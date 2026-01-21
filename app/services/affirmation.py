from langchain.chat_models import init_chat_model
from langchain.messages import SystemMessage, HumanMessage

from app.ai.models import FAST
from app.ai.prompts.affirmation import SYSTEM_MESSAGE, USER_MESSAGE_TEMPLATE
from app.ai.structured_outputs.affirmation import Affirmations
from app.api.schemas.affirmation import (
    AffirmationRequest,
    AffirmationResponse,
)


async def generate_affirmations_service(
    payload: AffirmationRequest,
) -> AffirmationResponse:
    """
    Generate affirmations using LLM based on user input.
    """

    # Prepare user message
    formatted_user_message = USER_MESSAGE_TEMPLATE.format(
        user_goal=payload.user_goal,
        mood=payload.mood,
        emotion=payload.emotion,
        life_factor=payload.life_factor,
    )

    messages = [
        SystemMessage(SYSTEM_MESSAGE),
        HumanMessage(formatted_user_message),
    ]

    # Define the LLM model
    llm = init_chat_model(FAST, temperature=0.95)

    # Bind structured output
    structured_llm = llm.with_structured_output(Affirmations)

    # Invoke model asynchronously
    response: Affirmations = await structured_llm.ainvoke(messages)

    # Map structured output to API response
    return AffirmationResponse(
        affirmations=[affirmation.text for affirmation in response.affirmations],
    )
